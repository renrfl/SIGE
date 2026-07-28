from datetime import datetime

from app import db


class Rua(db.Model):

    __tablename__ = "rua"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(50), nullable=False)

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresa.id"),
        nullable=False
    )

    ativo = db.Column(db.Boolean, default=True)

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )