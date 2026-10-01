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


def calcular_indicadores_produtos(filtro_ativo=None):

    produtos_query = db.session.query(
        Produto.id
    )

    if filtro_ativo is not None:

        produtos_query = produtos_query.filter(
            Produto.ativo == filtro_ativo
        )

    total_produtos = (
        produtos_query.count()
    )

    produtos_enderecados_query = (
        db.session.query(
            func.count(
                distinct(
                    ProdutoEndereco.produto_id
                )
            )
        )
        .join(
            Produto,
            Produto.id == ProdutoEndereco.produto_id
        )
    )

    if filtro_ativo is not None:

        produtos_enderecados_query = (
            produtos_enderecados_query.filter(
                Produto.ativo == filtro_ativo
            )
        )

    produtos_enderecados = (
        produtos_enderecados_query.scalar()
        or 0
    )

    produtos_pendentes = (
        total_produtos
        - produtos_enderecados
    )

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

    return {
        "total_produtos": total_produtos,
        "produtos_enderecados": produtos_enderecados,
        "produtos_pendentes": produtos_pendentes,
        "percentual_enderecado": percentual_enderecado
    }


@home_bp.route("/admin")
@home_bp.route("/admin/")
def dashboard():

    indicadores_ativos = calcular_indicadores_produtos(
        True
    )

    indicadores_todos = calcular_indicadores_produtos()

    indicadores_inativos = calcular_indicadores_produtos(
        False
    )

    total_posicoes = Posicao.query.count()

    return render_template(
        "index.html",

        total_produtos=(
            indicadores_ativos[
                "total_produtos"
            ]
        ),

        produtos_enderecados=(
            indicadores_ativos[
                "produtos_enderecados"
            ]
        ),

        produtos_pendentes=(
            indicadores_ativos[
                "produtos_pendentes"
            ]
        ),

        percentual_enderecado=(
            indicadores_ativos[
                "percentual_enderecado"
            ]
        ),

        total_posicoes=total_posicoes,

        indicadores_ativos=indicadores_ativos,
        indicadores_todos=indicadores_todos,
        indicadores_inativos=indicadores_inativos
    )