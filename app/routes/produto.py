from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Produto


produto_bp = Blueprint(
    "produto",
    __name__,
    url_prefix="/produtos"
)


@produto_bp.route("/")
def listar():

    produtos = Produto.query.order_by(
        Produto.descricao
    ).all()

    return render_template(
        "produto/listar.html",
        produtos=produtos
    )


@produto_bp.route("/novo", methods=["GET", "POST"])
def novo():

    if request.method == "POST":

        codigo = request.form["codigo"].strip()
        codigo_barras = request.form["codigo_barras"].strip()
        descricao = request.form["descricao"].strip()

        if not codigo:

            flash(
                "Informe o código do produto.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        if not codigo.isdigit():

            flash(
                "O código do produto deve conter somente números.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        if not codigo_barras:

            flash(
                "Informe o código de barras do produto.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        if not descricao:

            flash(
                "Informe a descrição do produto.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        produto_existente = Produto.query.filter(
            db.or_(
                Produto.codigo == int(codigo),
                Produto.codigo_barras == codigo_barras
            )
        ).first()

        if produto_existente:

            flash(
                "Já existe um produto com esse código ou código de barras.",
                "warning"
            )

            return redirect(
                url_for("produto.novo")
            )

        produto = Produto(
            codigo=int(codigo),
            codigo_barras=codigo_barras,
            descricao=descricao
        )

        try:

            db.session.add(produto)
            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "Não foi possível cadastrar o produto. Verifique os dados informados.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        flash(
            "Produto cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("produto.listar")
        )

    return render_template(
        "produto/form.html",
        produto=None
    )


@produto_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    produto = Produto.query.get_or_404(id)

    if request.method == "POST":

        codigo = request.form["codigo"].strip()
        codigo_barras = request.form["codigo_barras"].strip()
        descricao = request.form["descricao"].strip()

        if not codigo:

            flash(
                "Informe o código do produto.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        if not codigo.isdigit():

            flash(
                "O código do produto deve conter somente números.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        if not codigo_barras:

            flash(
                "Informe o código de barras do produto.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        if not descricao:

            flash(
                "Informe a descrição do produto.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        produto_existente = Produto.query.filter(
            db.or_(
                Produto.codigo == int(codigo),
                Produto.codigo_barras == codigo_barras
            ),
            Produto.id != produto.id
        ).first()

        if produto_existente:

            flash(
                "Já existe outro produto com esse código ou código de barras.",
                "warning"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        produto.codigo = int(codigo)
        produto.codigo_barras = codigo_barras
        produto.descricao = descricao

        try:

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "Não foi possível atualizar o produto. Verifique os dados informados.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        flash(
            "Produto atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("produto.listar")
        )

    return render_template(
        "produto/form.html",
        produto=produto
    )


@produto_bp.route("/excluir/<int:id>")
def excluir(id):

    produto = Produto.query.get_or_404(id)

    try:

        db.session.delete(produto)
        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        flash(
            "Não foi possível remover o produto.",
            "danger"
        )

        return redirect(
            url_for("produto.listar")
        )

    flash(
        "Produto removido com sucesso.",
        "success"
    )

    return redirect(
        url_for("produto.listar")
    )