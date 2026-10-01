from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from app import db
from app.models import Produto, ProdutoEndereco


consulta_bp = Blueprint(
    "consulta",
    __name__,
    url_prefix="/consulta"
)


@consulta_bp.route("/", methods=["GET", "POST"])
def index():

    produto = None
    endereco = None
    enderecos = []
    total_enderecos = 0

    if request.method == "POST":

        pesquisa = request.form["pesquisa"].strip()

        produto = Produto.query.filter(
            (Produto.codigo == pesquisa) |
            (Produto.codigo_barras == pesquisa)
        ).first()

        if produto:

            enderecos = ProdutoEndereco.query.filter_by(
                produto_id=produto.id
            ).all()

            total_enderecos = len(enderecos)

            if enderecos:
                endereco = enderecos[0]

    return render_template(
        "consulta/index.html",
        produto=produto,
        endereco=endereco,
        enderecos=enderecos,
        total_enderecos=total_enderecos
    )


@consulta_bp.route(
    "/produto/<int:codigo>/enderecos",
    methods=["GET"]
)
def gerenciar_enderecos(codigo):

    if not session.get("usuario_id"):

        flash(
            "Faça login para acessar esta função.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    produto = Produto.query.filter_by(
        codigo=codigo
    ).first_or_404()

    enderecos = ProdutoEndereco.query.filter_by(
        produto_id=produto.id
    ).all()

    return render_template(
        "consulta/gerenciar_enderecos.html",
        produto=produto,
        enderecos=enderecos,
        total_enderecos=len(enderecos)
    )


@consulta_bp.route(
    "/endereco/<int:id>/remover",
    methods=["POST"]
)
def remover_endereco(id):

    if not session.get("usuario_id"):

        flash(
            "Faça login para acessar esta função.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    endereco = ProdutoEndereco.query.get_or_404(id)

    codigo_produto = endereco.produto.codigo

    db.session.delete(endereco)
    db.session.commit()

    flash(
        "Endereço removido com sucesso.",
        "success"
    )

    enderecos_restantes = ProdutoEndereco.query.filter_by(
        produto_id=endereco.produto_id
    ).count()

    if enderecos_restantes > 0:

        return redirect(
            url_for(
                "consulta.gerenciar_enderecos",
                codigo=codigo_produto
            )
        )

    return redirect(
        url_for("consulta.index")
    )