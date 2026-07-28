from datetime import datetime

from app import db


class Posicao(db.Model):

    __tablename__ = "posicao"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(50), nullable=False)

    nivel_id = db.Column(
        db.Integer,
        db.ForeignKey("nivel.id"),
        nullable=False
    )

    ativo = db.Column(db.Boolean, default=True)

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )