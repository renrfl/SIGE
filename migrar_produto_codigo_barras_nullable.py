import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from app import create_app, db


def obter_caminho_banco() -> Path:

    app = create_app()

    with app.app_context():

        caminho = db.engine.url.database

    if not caminho:

        raise RuntimeError(
            "Não foi possível localizar o arquivo do banco SQLite."
        )

    caminho_banco = Path(caminho)

    if not caminho_banco.is_absolute():

        caminho_banco = Path.cwd() / caminho_banco

    return caminho_banco.resolve()


def coluna_codigo_barras_aceita_nulo(
    conexao: sqlite3.Connection
) -> bool:

    colunas = conexao.execute(
        "PRAGMA table_info(produto)"
    ).fetchall()

    for coluna in colunas:

        nome = coluna[1]
        obrigatoria = coluna[3]

        if nome == "codigo_barras":

            return obrigatoria == 0

    raise RuntimeError(
        "A coluna codigo_barras não foi encontrada na tabela produto."
    )


def executar_migracao() -> None:

    caminho_banco = obter_caminho_banco()

    if not caminho_banco.exists():

        raise FileNotFoundError(
            f"Banco de dados não encontrado: {caminho_banco}"
        )

    conexao = sqlite3.connect(caminho_banco)

    try:

        if coluna_codigo_barras_aceita_nulo(conexao):

            print(
                "A coluna codigo_barras já aceita valores vazios. "
                "Nenhuma alteração foi necessária."
            )

            return

        data_hora = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        caminho_backup = caminho_banco.with_name(
            f"{caminho_banco.stem}_antes_migracao_{data_hora}"
            f"{caminho_banco.suffix}"
        )

        conexao.close()

        shutil.copy2(
            caminho_banco,
            caminho_backup
        )

        print(
            f"Backup criado em: {caminho_backup}"
        )

        conexao = sqlite3.connect(caminho_banco)

        conexao.execute(
            "PRAGMA foreign_keys = OFF"
        )

        conexao.execute(
            "BEGIN"
        )

        conexao.execute(
            """
            CREATE TABLE produto_nova (
                id INTEGER NOT NULL,
                codigo INTEGER NOT NULL,
                codigo_barras VARCHAR(30),
                descricao VARCHAR(200) NOT NULL,
                ativo BOOLEAN,
                data_cadastro DATETIME,
                PRIMARY KEY (id)
            )
            """
        )

        conexao.execute(
            """
            INSERT INTO produto_nova (
                id,
                codigo,
                codigo_barras,
                descricao,
                ativo,
                data_cadastro
            )
            SELECT
                id,
                codigo,
                NULLIF(TRIM(codigo_barras), ''),
                descricao,
                ativo,
                data_cadastro
            FROM produto
            """
        )

        conexao.execute(
            "DROP TABLE produto"
        )

        conexao.execute(
            "ALTER TABLE produto_nova RENAME TO produto"
        )

        conexao.execute(
            """
            CREATE UNIQUE INDEX uq_produto_codigo
            ON produto (codigo)
            """
        )

        conexao.execute(
            """
            CREATE UNIQUE INDEX uq_produto_codigo_barras
            ON produto (codigo_barras)
            """
        )

        conexao.commit()

        conexao.execute(
            "PRAGMA foreign_keys = ON"
        )

        resultado = conexao.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if resultado:

            raise RuntimeError(
                "Foram encontradas inconsistências de chave estrangeira "
                f"após a migração: {resultado}"
            )

        print(
            "Migração concluída com sucesso."
        )

        print(
            "A coluna codigo_barras agora aceita valores vazios."
        )

    except Exception:

        if conexao.in_transaction:

            conexao.rollback()

        raise

    finally:

        conexao.close()


if __name__ == "__main__":

    executar_migracao()