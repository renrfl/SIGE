import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from app import create_app, db


PASTA_BACKUPS = "backups"


def obter_caminho_banco() -> Path:

    app = create_app()

    with app.app_context():

        caminho = db.engine.url.database

    if not caminho:

        raise RuntimeError(
            "Não foi possível localizar o banco SQLite configurado no SIGE."
        )

    caminho_banco = Path(caminho)

    if not caminho_banco.is_absolute():

        caminho_banco = (
            Path.cwd()
            / caminho_banco
        )

    return caminho_banco.resolve()


def obter_pasta_backups(
    caminho_banco: Path
) -> Path:

    raiz_projeto = Path.cwd()

    pasta = (
        raiz_projeto
        / PASTA_BACKUPS
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta.resolve()


def verificar_integridade(
    caminho_banco: Path
) -> None:

    if not caminho_banco.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho_banco}"
        )

    conexao = sqlite3.connect(
        str(caminho_banco)
    )

    try:

        resultado = conexao.execute(
            "PRAGMA integrity_check"
        ).fetchone()

    finally:

        conexao.close()

    if (
        not resultado
        or resultado[0].lower() != "ok"
    ):

        raise RuntimeError(
            (
                "O banco SQLite não passou na verificação de integridade: "
                f"{resultado}"
            )
        )


def criar_backup(
    prefixo: str = "sige"
) -> Path:

    caminho_banco = obter_caminho_banco()

    if not caminho_banco.exists():

        raise FileNotFoundError(
            f"Banco do SIGE não encontrado: {caminho_banco}"
        )

    verificar_integridade(
        caminho_banco
    )

    pasta_backups = obter_pasta_backups(
        caminho_banco
    )

    data_hora = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    caminho_backup = pasta_backups / (
        f"{prefixo}_{data_hora}.db"
    )

    origem = sqlite3.connect(
        str(caminho_banco)
    )

    destino = sqlite3.connect(
        str(caminho_backup)
    )

    try:

        origem.backup(
            destino
        )

    finally:

        destino.close()
        origem.close()

    verificar_integridade(
        caminho_backup
    )

    return caminho_backup


def listar_backups() -> list[Path]:

    caminho_banco = obter_caminho_banco()

    pasta_backups = obter_pasta_backups(
        caminho_banco
    )

    return sorted(
        pasta_backups.glob("*.db"),
        key=lambda arquivo: arquivo.stat().st_mtime,
        reverse=True
    )


def localizar_backup(
    nome_arquivo: str
) -> Path:

    caminho_banco = obter_caminho_banco()

    pasta_backups = obter_pasta_backups(
        caminho_banco
    )

    nome_seguro = Path(
        nome_arquivo
    ).name

    caminho_backup = (
        pasta_backups
        / nome_seguro
    ).resolve()

    if caminho_backup.parent != pasta_backups:

        raise ValueError(
            "Nome de backup inválido."
        )

    if not caminho_backup.exists():

        raise FileNotFoundError(
            f"Backup não encontrado: {nome_seguro}"
        )

    return caminho_backup


def restaurar_backup(
    nome_arquivo: str
) -> Path:

    caminho_backup = localizar_backup(
        nome_arquivo
    )

    verificar_integridade(
        caminho_backup
    )

    caminho_banco = obter_caminho_banco()

    if not caminho_banco.exists():

        raise FileNotFoundError(
            f"Banco atual do SIGE não encontrado: {caminho_banco}"
        )

    backup_seguranca = criar_backup(
        prefixo="antes_restauracao"
    )

    app = create_app()

    with app.app_context():

        db.session.remove()
        db.engine.dispose()

    origem = sqlite3.connect(
        str(caminho_backup)
    )

    destino = sqlite3.connect(
        str(caminho_banco)
    )

    try:

        origem.backup(
            destino
        )

    finally:

        destino.close()
        origem.close()

    verificar_integridade(
        caminho_banco
    )

    return backup_seguranca


def comando_backup() -> None:

    caminho_backup = criar_backup()

    tamanho_mb = (
        caminho_backup.stat().st_size
        / 1024
        / 1024
    )

    print(
        "Backup criado com sucesso."
    )

    print(
        f"Arquivo: {caminho_backup}"
    )

    print(
        f"Tamanho: {tamanho_mb:.2f} MB"
    )


def comando_listar() -> None:

    backups = listar_backups()

    if not backups:

        print(
            "Nenhum backup encontrado."
        )

        return

    print(
        "Backups disponíveis:"
    )

    for arquivo in backups:

        tamanho_mb = (
            arquivo.stat().st_size
            / 1024
            / 1024
        )

        data = datetime.fromtimestamp(
            arquivo.stat().st_mtime
        ).strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        print(
            f"- {arquivo.name} | {data} | {tamanho_mb:.2f} MB"
        )


def comando_verificar(
    nome_arquivo: str
) -> None:

    caminho_backup = localizar_backup(
        nome_arquivo
    )

    verificar_integridade(
        caminho_backup
    )

    print(
        "Backup íntegro."
    )

    print(
        f"Arquivo: {caminho_backup}"
    )


def comando_restaurar(
    nome_arquivo: str,
    confirmar: bool
) -> None:

    if not confirmar:

        print(
            "Restauração cancelada."
        )

        print(
            (
                "Pare o SIGE/Gunicorn e execute novamente "
                "com a opção --confirmar."
            )
        )

        sys.exit(
            1
        )

    backup_seguranca = restaurar_backup(
        nome_arquivo
    )

    print(
        "Backup restaurado com sucesso."
    )

    print(
        (
            "Uma cópia do banco anterior foi criada automaticamente em:"
        )
    )

    print(
        backup_seguranca
    )


def criar_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Backup e restauração do banco SQLite do SIGE."
        )
    )

    subcomandos = parser.add_subparsers(
        dest="comando",
        required=True
    )

    subcomandos.add_parser(
        "backup",
        help="Cria um novo backup do banco."
    )

    subcomandos.add_parser(
        "listar",
        help="Lista os backups existentes."
    )

    verificar = subcomandos.add_parser(
        "verificar",
        help="Verifica a integridade de um backup."
    )

    verificar.add_argument(
        "arquivo",
        help="Nome do arquivo existente na pasta backups."
    )

    restaurar = subcomandos.add_parser(
        "restaurar",
        help="Restaura um backup existente."
    )

    restaurar.add_argument(
        "arquivo",
        help="Nome do arquivo existente na pasta backups."
    )

    restaurar.add_argument(
        "--confirmar",
        action="store_true",
        help="Confirma explicitamente a restauração."
    )

    return parser


def main() -> None:

    parser = criar_parser()

    argumentos = parser.parse_args()

    try:

        if argumentos.comando == "backup":

            comando_backup()

        elif argumentos.comando == "listar":

            comando_listar()

        elif argumentos.comando == "verificar":

            comando_verificar(
                argumentos.arquivo
            )

        elif argumentos.comando == "restaurar":

            comando_restaurar(
                argumentos.arquivo,
                argumentos.confirmar
            )

    except Exception as erro:

        print(
            f"ERRO: {erro}",
            file=sys.stderr
        )

        sys.exit(
            1
        )


if __name__ == "__main__":

    main()