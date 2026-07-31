from datetime import datetime

from app import db


class Modulo(db.Model):

    __tablename__ = "modulo"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(50),
        nullable=False
    )

    predio_id = db.Column(
        db.Integer,
        db.ForeignKey("predio.id"),
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

    niveis = db.relationship(
        "Nivel",
        backref="modulo",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Modulo {self.nome}>"