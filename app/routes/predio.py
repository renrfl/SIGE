from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db
from app.models import Predio, Rua

predio_bp = Blueprint(
    "predio",
    __name__,
    url_prefix="/predios"
)


@predio_bp.route("/")
def listar():

    predios = Predio.query.order_by(Predio.nome).all()

    return render_template(
        "predio/listar.html",
        predios=predios
    )


@predio_bp.route("/novo", methods=["GET", "POST"])
def novo():

    ruas = Rua.query.order_by(Rua.nome).all()

    if request.method == "POST":

        nome = request.form["nome"].strip()
        rua_id = request.form["rua_id"]

        if not nome:

            flash("Informe o nome do prédio.", "danger")
            return redirect(url_for("predio.novo"))

        existe = Predio.query.filter_by(
            nome=nome,
            rua_id=rua_id
        ).first()

        if existe:

            flash("Prédio já cadastrado nesta rua.", "warning")
            return redirect(url_for("predio.novo"))

        predio = Predio(
            nome=nome,
            rua_id=rua_id
        )

        db.session.add(predio)
        db.session.commit()

        flash("Prédio cadastrado com sucesso.", "success")

        return redirect(url_for("predio.listar"))

    return render_template(
        "predio/form.html",
        predio=None,
        ruas=ruas
    )


@predio_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    predio = Predio.query.get_or_404(id)
    ruas = Rua.query.order_by(Rua.nome).all()

    if request.method == "POST":

        predio.nome = request.form["nome"].strip()
        predio.rua_id = request.form["rua_id"]

        db.session.commit()

        flash("Prédio atualizado com sucesso.", "success")

        return redirect(url_for("predio.listar"))

    return render_template(
        "predio/form.html",
        predio=predio,
        ruas=ruas
    )


@predio_bp.route("/excluir/<int:id>")
def excluir(id):

    predio = Predio.query.get_or_404(id)

    db.session.delete(predio)
    db.session.commit()

    flash("Prédio removido com sucesso.", "success")

    return redirect(url_for("predio.listar"))