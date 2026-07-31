from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Posicao, Produto, ProdutoEndereco


endereco_bp = Blueprint(
    "endereco",
    __name__,
    url_prefix="/enderecos"
)


@endereco_bp.route("/")
def listar():

    enderecos = ProdutoEndereco.query.order_by(
        ProdutoEndereco.data_cadastro.desc()
    ).all()

    return render_template(
        "endereco/listar.html",
        enderecos=enderecos
    )


@endereco_bp.route("/novo", methods=["GET", "POST"])
def novo():

    produtos = Produto.query.order_by(
        Produto.descricao
    ).all()

    posicoes = Posicao.query.order_by(
        Posicao.nome
    ).all()

    if request.method == "POST":

        produto_id = request.form["produto_id"]
        posicao_id = request.form["posicao_id"]

        endereco_existente = ProdutoEndereco.query.filter_by(
            produto_id=produto_id,
            posicao_id=posicao_id
        ).first()

        if endereco_existente:

            flash(
                "Este produto já está vinculado a essa posição.",
                "warning"
            )

            return redirect(
                url_for("endereco.novo")
            )

        endereco = ProdutoEndereco(
            produto_id=produto_id,
            posicao_id=posicao_id
        )

        db.session.add(endereco)
        db.session.commit()

        flash(
            "Produto endereçado com sucesso.",
            "success"
        )

        return redirect(
            url_for("endereco.listar")
        )

    return render_template(
        "endereco/form.html",
        endereco=None,
        produtos=produtos,
        posicoes=posicoes
    )


@endereco_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    endereco = ProdutoEndereco.query.get_or_404(id)

    produtos = Produto.query.order_by(
        Produto.descricao
    ).all()

    posicoes = Posicao.query.order_by(
        Posicao.nome
    ).all()

    if request.method == "POST":

        produto_id = request.form["produto_id"]
        posicao_id = request.form["posicao_id"]

        endereco_existente = ProdutoEndereco.query.filter(
            ProdutoEndereco.produto_id == produto_id,
            ProdutoEndereco.posicao_id == posicao_id,
            ProdutoEndereco.id != endereco.id
        ).first()

        if endereco_existente:

            flash(
                "Este produto já está vinculado a essa posição.",
                "warning"
            )

            return redirect(
                url_for(
                    "endereco.editar",
                    id=endereco.id
                )
            )

        endereco.produto_id = produto_id
        endereco.posicao_id = posicao_id

        db.session.commit()

        flash(
            "Endereço atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("endereco.listar")
        )

    return render_template(
        "endereco/form.html",
        endereco=endereco,
        produtos=produtos,
        posicoes=posicoes
    )


@endereco_bp.route("/excluir/<int:id>")
def excluir(id):

    endereco = ProdutoEndereco.query.get_or_404(id)

    db.session.delete(endereco)
    db.session.commit()

    flash(
        "Endereço removido com sucesso.",
        "success"
    )

    return redirect(
        url_for("endereco.listar")
    )