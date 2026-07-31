from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db
from app.models import Rua

rua_bp = Blueprint(
    "rua",
    __name__,
    url_prefix="/ruas"
)


@rua_bp.route("/")
def listar():

    ruas = Rua.query.order_by(Rua.nome).all()

    return render_template(
        "rua/listar.html",
        ruas=ruas
    )


@rua_bp.route("/novo", methods=["GET", "POST"])
def novo():

    if request.method == "POST":

        nome = request.form["nome"].strip()
        descricao = request.form["descricao"].strip()

        if not nome:

            flash("Informe o nome da rua.", "danger")
            return redirect(url_for("rua.novo"))

        existe = Rua.query.filter_by(nome=nome).first()

        if existe:

            flash("Rua já cadastrada.", "warning")
            return redirect(url_for("rua.novo"))

        rua = Rua(
            nome=nome,
            descricao=descricao
        )

        db.session.add(rua)
        db.session.commit()

        flash("Rua cadastrada com sucesso.", "success")

        return redirect(url_for("rua.listar"))

    return render_template("rua/form.html", rua=None)


@rua_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    rua = Rua.query.get_or_404(id)

    if request.method == "POST":

        nome = request.form["nome"].strip()
        descricao = request.form["descricao"].strip()

        existe = Rua.query.filter(
            Rua.nome == nome,
            Rua.id != id
        ).first()

        if existe:

            flash("Já existe uma rua com esse nome.", "warning")
            return redirect(url_for("rua.editar", id=id))

        rua.nome = nome
        rua.descricao = descricao

        db.session.commit()

        flash("Rua atualizada com sucesso.", "success")

        return redirect(url_for("rua.listar"))

    return render_template(
        "rua/form.html",
        rua=rua
    )


@rua_bp.route("/excluir/<int:id>")
def excluir(id):

    rua = Rua.query.get_or_404(id)

    db.session.delete(rua)
    db.session.commit()

    flash("Rua excluída com sucesso.", "success")

    return redirect(url_for("rua.listar"))