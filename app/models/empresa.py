from datetime import datetime

from app import db


class Empresa(db.Model):

    __tablename__ = "empresa"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(120), nullable=False)

    ativo = db.Column(db.Boolean, default=True)

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
