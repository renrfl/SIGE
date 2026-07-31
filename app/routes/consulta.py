from flask import Blueprint, render_template, request

from app.models import Produto, ProdutoEndereco


consulta_bp = Blueprint(
    "consulta",
    __name__,
    url_prefix="/consulta"
)


@consulta_bp.route("/", methods=["GET", "POST"])
def index():

    endereco = None

    if request.method == "POST":

        pesquisa = request.form["pesquisa"].strip()

        produto = Produto.query.filter(
            (Produto.codigo == pesquisa) |
            (Produto.codigo_barras == pesquisa)
        ).first()

        if produto:

            endereco = ProdutoEndereco.query.filter_by(
                produto_id=produto.id
            ).first()

    return render_template(
        "consulta/index.html",
        endereco=endereco
    )