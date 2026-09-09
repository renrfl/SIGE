from datetime import datetime

from app import db


class DivergenciaCodigoBarras(db.Model):

    __tablename__ = "divergencia_codigo_barras"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    produto_id = db.Column(
        db.Integer,
        db.ForeignKey("produto.id"),
        nullable=False
    )

    codigo_barras_cadastrado = db.Column(
        db.String(30),
        nullable=True
    )

    codigo_barras_fisico = db.Column(
        db.String(30),
        nullable=False
    )

    observacao = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDENTE"
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id"),
        nullable=True
    )

    data_registro = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    data_atualizacao = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    produto = db.relationship(
        "Produto",
        backref="divergencias_codigo_barras"
    )

    usuario = db.relationship(
        "Usuario",
        backref="divergencias_codigo_barras"
    )

    def __repr__(self):

        return (
            f"<DivergenciaCodigoBarras "
            f"produto={self.produto_id} "
            f"status={self.status}>"
        )