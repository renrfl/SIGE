from getpass import getpass

from app import create_app, db
from app.models import Usuario


app = create_app()


with app.app_context():

    nome = input("Nome do administrador: ").strip()
    login = input("Login: ").strip()
    senha = getpass("Senha: ").strip()
    confirmar_senha = getpass("Confirme a senha: ").strip()

    if not nome:
        print("O nome é obrigatório.")
        raise SystemExit(1)

    if not login:
        print("O login é obrigatório.")
        raise SystemExit(1)

    if not senha:
        print("A senha é obrigatória.")
        raise SystemExit(1)

    if senha != confirmar_senha:
        print("As senhas não conferem.")
        raise SystemExit(1)

    usuario_existente = Usuario.query.filter_by(
        login=login
    ).first()

    if usuario_existente:
        print("Já existe um usuário com esse login.")
        raise SystemExit(1)

    usuario = Usuario(
        nome=nome,
        login=login
    )

    usuario.definir_senha(senha)

    db.session.add(usuario)
    db.session.commit()

    print("Administrador criado com sucesso.")