from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Modulo, Nivel


nivel_bp = Blueprint(
    "nivel",
    __name__,
    url_prefix="/niveis"
)


@nivel_bp.route("/")
def listar():

    niveis = Nivel.query.order_by(Nivel.nome).all()

    return render_template(
        "nivel/listar.html",
        niveis=niveis
    )


@nivel_bp.route("/novo", methods=["GET", "POST"])
def novo():

    modulos = Modulo.query.order_by(Modulo.nome).all()

    if request.method == "POST":

        nome = request.form["nome"].strip()
        modulo_id = request.form["modulo_id"]

        if not nome:

            flash(
                "Informe o nome do nível.",
                "danger"
            )

            return redirect(
                url_for("nivel.novo")
            )

        nivel_existente = Nivel.query.filter_by(
            nome=nome,
            modulo_id=modulo_id
        ).first()

        if nivel_existente:

            flash(
                "Já existe um nível com esse nome neste módulo.",
                "warning"
            )

            return redirect(
                url_for("nivel.novo")
            )

        nivel = Nivel(
            nome=nome,
            modulo_id=modulo_id
        )

        db.session.add(nivel)
        db.session.commit()

        flash(
            "Nível cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("nivel.listar")
        )

    return render_template(
        "nivel/form.html",
        nivel=None,
        modulos=modulos
    )


@nivel_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    nivel = Nivel.query.get_or_404(id)

    modulos = Modulo.query.order_by(Modulo.nome).all()

    if request.method == "POST":

        nome = request.form["nome"].strip()
        modulo_id = request.form["modulo_id"]

        if not nome:

            flash(
                "Informe o nome do nível.",
                "danger"
            )

            return redirect(
                url_for(
                    "nivel.editar",
                    id=nivel.id
                )
            )

        nivel_existente = Nivel.query.filter(
            Nivel.nome == nome,
            Nivel.modulo_id == modulo_id,
            Nivel.id != nivel.id
        ).first()

        if nivel_existente:

            flash(
                "Já existe um nível com esse nome neste módulo.",
                "warning"
            )

            return redirect(
                url_for(
                    "nivel.editar",
                    id=nivel.id
                )
            )

        nivel.nome = nome
        nivel.modulo_id = modulo_id

        db.session.commit()

        flash(
            "Nível atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("nivel.listar")
        )

    return render_template(
        "nivel/form.html",
        nivel=nivel,
        modulos=modulos
    )


@nivel_bp.route("/excluir/<int:id>")
def excluir(id):

    nivel = Nivel.query.get_or_404(id)

    db.session.delete(nivel)
    db.session.commit()

    flash(
        "Nível removido com sucesso.",
        "success"
    )

    return redirect(
        url_for("nivel.listar")
    )