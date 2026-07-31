from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Modulo, Predio


modulo_bp = Blueprint(
    "modulo",
    __name__,
    url_prefix="/modulos"
)


@modulo_bp.route("/")
def listar():

    modulos = Modulo.query.order_by(Modulo.nome).all()

    return render_template(
        "modulo/listar.html",
        modulos=modulos
    )


@modulo_bp.route("/novo", methods=["GET", "POST"])
def novo():

    predios = Predio.query.order_by(Predio.nome).all()

    if request.method == "POST":

        nome = request.form["nome"].strip()
        predio_id = request.form["predio_id"]

        if not nome:

            flash("Informe o nome do módulo.", "danger")

            return redirect(
                url_for("modulo.novo")
            )

        modulo_existente = Modulo.query.filter_by(
            nome=nome,
            predio_id=predio_id
        ).first()

        if modulo_existente:

            flash(
                "Já existe um módulo com esse nome neste prédio.",
                "warning"
            )

            return redirect(
                url_for("modulo.novo")
            )

        modulo = Modulo(
            nome=nome,
            predio_id=predio_id
        )

        db.session.add(modulo)
        db.session.commit()

        flash(
            "Módulo cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("modulo.listar")
        )

    return render_template(
        "modulo/form.html",
        modulo=None,
        predios=predios
    )


@modulo_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    modulo = Modulo.query.get_or_404(id)

    predios = Predio.query.order_by(Predio.nome).all()

    if request.method == "POST":

        nome = request.form["nome"].strip()
        predio_id = request.form["predio_id"]

        if not nome:

            flash(
                "Informe o nome do módulo.",
                "danger"
            )

            return redirect(
                url_for(
                    "modulo.editar",
                    id=modulo.id
                )
            )

        modulo_existente = Modulo.query.filter(
            Modulo.nome == nome,
            Modulo.predio_id == predio_id,
            Modulo.id != modulo.id
        ).first()

        if modulo_existente:

            flash(
                "Já existe um módulo com esse nome neste prédio.",
                "warning"
            )

            return redirect(
                url_for(
                    "modulo.editar",
                    id=modulo.id
                )
            )

        modulo.nome = nome
        modulo.predio_id = predio_id

        db.session.commit()

        flash(
            "Módulo atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("modulo.listar")
        )

    return render_template(
        "modulo/form.html",
        modulo=modulo,
        predios=predios
    )


@modulo_bp.route("/excluir/<int:id>")
def excluir(id):

    modulo = Modulo.query.get_or_404(id)

    db.session.delete(modulo)
    db.session.commit()

    flash(
        "Módulo removido com sucesso.",
        "success"
    )

    return redirect(
        url_for("modulo.listar")
    )