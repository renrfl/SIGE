from datetime import datetime

from app import db


class ProdutoEndereco(db.Model):

    __tablename__ = "produto_endereco"

    id = db.Column(db.Integer, primary_key=True)

    produto_id = db.Column(
        db.Integer,
        db.ForeignKey("produto.id"),
        nullable=False
    )

    posicao_id = db.Column(
        db.Integer,
        db.ForeignKey("posicao.id"),
        nullable=False
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    posicao = db.relationship(
        "Posicao",
        backref="enderecos",
        lazy=True
    )