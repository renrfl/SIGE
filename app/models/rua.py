from datetime import datetime

from app import db


class Rua(db.Model):

    __tablename__ = "rua"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    descricao = db.Column(
        db.String(200)
    )

    ativo = db.Column(
        db.Boolean,
        default=True
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    predios = db.relationship(
        "Predio",
        backref="rua",
        lazy=True,
        cascade="all, delete-orphan"
    )