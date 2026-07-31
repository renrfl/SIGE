from datetime import datetime

from app import db


class Produto(db.Model):

    __tablename__ = "produto"

    id = db.Column(db.Integer, primary_key=True)

    codigo = db.Column(
        db.Integer,
        nullable=False,
        unique=True
    )

    codigo_barras = db.Column(
        db.String(30),
        nullable=False,
        unique=True
    )

    descricao = db.Column(
        db.String(200),
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

    enderecos = db.relationship(
        "ProdutoEndereco",
        backref="produto",
        lazy=True,
        cascade="all, delete-orphan"
    )