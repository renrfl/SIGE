from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Nivel, Posicao


posicao_bp = Blueprint(
    "posicao",
    __name__,
    url_prefix="/posicoes"
)


@posicao_bp.route("/")
def listar():

    posicoes = Posicao.query.order_by(Posicao.nome).all()

    return render_template(
        "posicao/listar.html",
        posicoes=posicoes
    )


@posicao_bp.route("/novo", methods=["GET", "POST"])
def novo():

    niveis = Nivel.query.order_by(Nivel.nome).all()

    if request.method == "POST":

        nome = request.form["nome"].strip()
        nivel_id = request.form["nivel_id"]

        if not nome:

            flash(
                "Informe o nome da posição.",
                "danger"
            )

            return redirect(
                url_for("posicao.novo")
            )

        posicao_existente = Posicao.query.filter_by(
            nome=nome,
            nivel_id=nivel_id
        ).first()

        if posicao_existente:

            flash(
                "Já existe uma posição com esse nome neste nível.",
                "warning"
            )

            return redirect(
                url_for("posicao.novo")
            )

        posicao = Posicao(
            nome=nome,
            nivel_id=nivel_id
        )

        db.session.add(posicao)
        db.session.commit()

        flash(
            "Posição cadastrada com sucesso.",
            "success"
        )

        return redirect(
            url_for("posicao.listar")
        )

    return render_template(
        "posicao/form.html",
        posicao=None,
        niveis=niveis
    )


@posicao_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    posicao = Posicao.query.get_or_404(id)

    niveis = Nivel.query.order_by(Nivel.nome).all()

    if request.method == "POST":

        nome = request.form["nome"].strip()
        nivel_id = request.form["nivel_id"]

        if not nome:

            flash(
                "Informe o nome da posição.",
                "danger"
            )

            return redirect(
                url_for(
                    "posicao.editar",
                    id=posicao.id
                )
            )

        posicao_existente = Posicao.query.filter(
            Posicao.nome == nome,
            Posicao.nivel_id == nivel_id,
            Posicao.id != posicao.id
        ).first()

        if posicao_existente:

            flash(
                "Já existe uma posição com esse nome neste nível.",
                "warning"
            )

            return redirect(
                url_for(
                    "posicao.editar",
                    id=posicao.id
                )
            )

        posicao.nome = nome
        posicao.nivel_id = nivel_id

        db.session.commit()

        flash(
            "Posição atualizada com sucesso.",
            "success"
        )

        return redirect(
            url_for("posicao.listar")
        )

    return render_template(
        "posicao/form.html",
        posicao=posicao,
        niveis=niveis
    )


@posicao_bp.route("/excluir/<int:id>")
def excluir(id):

    posicao = Posicao.query.get_or_404(id)

    db.session.delete(posicao)
    db.session.commit()

    flash(
        "Posição removida com sucesso.",
        "success"
    )

    return redirect(
        url_for("posicao.listar")
    )