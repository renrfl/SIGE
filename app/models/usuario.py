from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class Usuario(db.Model):

    __tablename__ = "usuario"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    login = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    senha_hash = db.Column(
        db.String(255),
        nullable=False
    )

    ativo = db.Column(
        db.Boolean,
        default=True
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def definir_senha(self, senha):

        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):

        return check_password_hash(
            self.senha_hash,
            senha
        )

    def __repr__(self):

        return f"<Usuario {self.login}>"