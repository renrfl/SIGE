from datetime import datetime

from app import db


class Nivel(db.Model):

    __tablename__ = "nivel"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(50), nullable=False)

    modulo_id = db.Column(
        db.Integer,
        db.ForeignKey("modulo.id"),
        nullable=False
    )

    ativo = db.Column(db.Boolean, default=True)

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )