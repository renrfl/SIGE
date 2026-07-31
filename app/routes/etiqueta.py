from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models import Produto, ProdutoEndereco


etiqueta_bp = Blueprint(
    "etiqueta",
    __name__,
    url_prefix="/etiquetas"
)


@etiqueta_bp.route("/", methods=["GET", "POST"])
def pesquisar():

    if request.method == "POST":

        codigo = request.form["codigo"].strip()

        if not codigo:

            flash(
                "Informe o código interno do produto.",
                "danger"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        if not codigo.isdigit():

            flash(
                "O código interno deve conter somente números.",
                "danger"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        produto = Produto.query.filter_by(
            codigo=int(codigo)
        ).first()

        if not produto:

            flash(
                "Produto não encontrado.",
                "warning"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        endereco = ProdutoEndereco.query.filter_by(
            produto_id=produto.id
        ).first()

        if not endereco:

            flash(
                "Este produto ainda não possui endereço cadastrado.",
                "warning"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        return redirect(
            url_for(
                "etiqueta.imprimir",
                produto_id=produto.id
            )
        )

    return render_template(
        "etiqueta/pesquisar.html"
    )


@etiqueta_bp.route("/imprimir/<int:produto_id>")
def imprimir(produto_id):

    produto = Produto.query.get_or_404(produto_id)

    endereco = ProdutoEndereco.query.filter_by(
        produto_id=produto.id
    ).first()

    if not endereco:

        flash(
            "Este produto ainda não possui endereço cadastrado.",
            "warning"
        )

        return redirect(
            url_for("etiqueta.pesquisar")
        )

    nivel_nome = endereco.posicao.nivel.nome.strip().lower()

    if nivel_nome in ("1", "nivel 1", "nível 1", "terreo", "térreo"):

        indicador = "baixo"

    elif nivel_nome in ("2", "nivel 2", "nível 2", "superior"):

        indicador = "cima"

    else:

        indicador = "deposito"

    return render_template(
        "etiqueta/imprimir.html",
        produto=produto,
        endereco=endereco,
        indicador=indicador
    )