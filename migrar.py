import os
import sqlite3


BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "sige.db"
)


def coluna_existe(cursor, tabela, coluna):

    cursor.execute(
        f"PRAGMA table_info({tabela})"
    )

    colunas = cursor.fetchall()

    return any(
        item[1] == coluna
        for item in colunas
    )


def migrar():

    if not os.path.exists(DATABASE_PATH):

        print(
            "ERRO: banco de dados não encontrado:"
        )
        print(DATABASE_PATH)
        return

    conexao = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conexao.cursor()

    try:

        if coluna_existe(
            cursor,
            "usuario",
            "perfil"
        ):

            print(
                "A coluna 'perfil' já existe."
            )

            cursor.execute(
                """
                SELECT
                    id,
                    nome,
                    login,
                    perfil
                FROM usuario
                ORDER BY id
                """
            )

            usuarios = cursor.fetchall()

            print()

            for usuario in usuarios:

                print(
                    f"ID: {usuario[0]} | "
                    f"Nome: {usuario[1]} | "
                    f"Login: {usuario[2]} | "
                    f"Perfil: {usuario[3]}"
                )

            return

        print(
            "Adicionando coluna 'perfil'..."
        )

        cursor.execute(
            """
            ALTER TABLE usuario
            ADD COLUMN perfil VARCHAR(20)
            NOT NULL
            DEFAULT 'ADMINISTRADOR'
            """
        )

        cursor.execute(
            """
            UPDATE usuario
            SET perfil = 'ADMINISTRADOR'
            """
        )

        conexao.commit()

        print(
            "Migração concluída com sucesso."
        )

        print()
        print(
            "Usuários existentes:"
        )

        cursor.execute(
            """
            SELECT
                id,
                nome,
                login,
                perfil
            FROM usuario
            ORDER BY id
            """
        )

        usuarios = cursor.fetchall()

        for usuario in usuarios:

            print(
                f"ID: {usuario[0]} | "
                f"Nome: {usuario[1]} | "
                f"Login: {usuario[2]} | "
                f"Perfil: {usuario[3]}"
            )

    except Exception as erro:

        conexao.rollback()

        print(
            "ERRO durante a migração:"
        )

        print(erro)

    finally:

        conexao.close()


if __name__ == "__main__":

    migrar()