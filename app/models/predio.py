from datetime import datetime

from app import db


class Predio(db.Model):

    __tablename__ = "predio"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(50),
        nullable=False
    )

    rua_id = db.Column(
        db.Integer,
        db.ForeignKey("rua.id"),
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

    modulos = db.relationship(
        "Modulo",
        backref="predio",
        lazy=True,
        cascade="all, delete-orphan"
    )