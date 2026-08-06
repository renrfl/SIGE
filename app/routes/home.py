from flask import Blueprint, redirect, render_template, url_for
from sqlalchemy import distinct, func

from app import db
from app.models import Posicao, Produto, ProdutoEndereco


home_bp = Blueprint(
    "home",
    __name__
)


@home_bp.route("/")
def index():

    return redirect(
        url_for("consulta.index")
    )


@home_bp.route("/admin")
@home_bp.route("/admin/")
def dashboard():

    total_produtos = Produto.query.count()

    produtos_enderecados = (
        db.session.query(
            func.count(
                distinct(
                    ProdutoEndereco.produto_id
                )
            )
        )
        .scalar()
        or 0
    )

    produtos_pendentes = (
        total_produtos
        - produtos_enderecados
    )

    total_posicoes = Posicao.query.count()

    if total_produtos > 0:

        percentual_enderecado = round(
            (
                produtos_enderecados
                / total_produtos
            )
            * 100,
            1
        )

    else:

        percentual_enderecado = 0

    return render_template(
        "index.html",
        total_produtos=total_produtos,
        produtos_enderecados=produtos_enderecados,
        produtos_pendentes=produtos_pendentes,
        total_posicoes=total_posicoes,
        percentual_enderecado=percentual_enderecado
    )