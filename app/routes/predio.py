from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Predio, Rua


predio_bp = Blueprint(
    "predio",
    __name__,
    url_prefix="/predios"
)


@predio_bp.route("/")
def listar():

    predios = Predio.query.order_by(
        Predio.nome
    ).all()

    return render_template(
        "predio/listar.html",
        predios=predios
    )


@predio_bp.route("/novo", methods=["GET", "POST"])
def novo():

    ruas = Rua.query.filter_by(
        ativo=True
    ).order_by(
        Rua.nome
    ).all()

    if request.method == "POST":

        nome = request.form[
            "nome"
        ].strip()

        rua_id = request.form.get(
            "rua_id",
            type=int
        )

        if not nome:

            flash(
                "Informe o nome do prédio.",
                "danger"
            )

            return redirect(
                url_for(
                    "predio.novo"
                )
            )

        if not rua_id:

            flash(
                "Selecione a rua do prédio.",
                "danger"
            )

            return redirect(
                url_for(
                    "predio.novo"
                )
            )

        rua = Rua.query.filter_by(
            id=rua_id,
            ativo=True
        ).first()

        if not rua:

            flash(
                "A rua selecionada não está disponível.",
                "danger"
            )

            return redirect(
                url_for(
                    "predio.novo"
                )
            )

        predio_existente = Predio.query.filter_by(
            nome=nome,
            rua_id=rua_id
        ).first()

        if predio_existente:

            flash(
                "Já existe um prédio com esse nome nesta rua.",
                "warning"
            )

            return redirect(
                url_for(
                    "predio.novo"
                )
            )

        predio = Predio(
            nome=nome,
            rua_id=rua_id,
            ativo=True
        )

        db.session.add(
            predio
        )

        db.session.commit()

        flash(
            "Prédio cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "predio.listar"
            )
        )

    return render_template(
        "predio/form.html",
        predio=None,
        ruas=ruas
    )


@predio_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar(id):

    predio = Predio.query.get_or_404(
        id
    )

    ruas = Rua.query.filter_by(
        ativo=True
    ).order_by(
        Rua.nome
    ).all()

    if (
        predio.rua
        and predio.rua not in ruas
    ):

        ruas.append(
            predio.rua
        )

        ruas.sort(
            key=lambda rua: rua.nome.lower()
        )

    if request.method == "POST":

        nome = request.form[
            "nome"
        ].strip()

        rua_id = request.form.get(
            "rua_id",
            type=int
        )

        if not nome:

            flash(
                "Informe o nome do prédio.",
                "danger"
            )

            return redirect(
                url_for(
                    "predio.editar",
                    id=predio.id
                )
            )

        if not rua_id:

            flash(
                "Selecione a rua do prédio.",
                "danger"
            )

            return redirect(
                url_for(
                    "predio.editar",
                    id=predio.id
                )
            )

        rua = Rua.query.get(
            rua_id
        )

        if not rua:

            flash(
                "A rua selecionada não foi encontrada.",
                "danger"
            )

            return redirect(
                url_for(
                    "predio.editar",
                    id=predio.id
                )
            )

        if (
            not rua.ativo
            and rua.id != predio.rua_id
        ):

            flash(
                "Não é permitido mover o prédio para uma rua inativa.",
                "danger"
            )

            return redirect(
                url_for(
                    "predio.editar",
                    id=predio.id
                )
            )

        predio_existente = Predio.query.filter(
            Predio.nome == nome,
            Predio.rua_id == rua_id,
            Predio.id != predio.id
        ).first()

        if predio_existente:

            flash(
                "Já existe um prédio com esse nome nesta rua.",
                "warning"
            )

            return redirect(
                url_for(
                    "predio.editar",
                    id=predio.id
                )
            )

        predio.nome = nome
        predio.rua_id = rua_id

        db.session.commit()

        flash(
            "Prédio atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "predio.listar"
            )
        )

    return render_template(
        "predio/form.html",
        predio=predio,
        ruas=ruas
    )


@predio_bp.route(
    "/alternar-status/<int:id>",
    methods=["POST"]
)
def alternar_status(id):

    predio = Predio.query.get_or_404(
        id
    )

    novo_status = not predio.ativo

    predio.ativo = novo_status

    quantidade_modulos = 0
    quantidade_niveis = 0
    quantidade_posicoes = 0

    for modulo in predio.modulos:

        modulo.ativo = novo_status
        quantidade_modulos += 1

        for nivel in modulo.niveis:

            nivel.ativo = novo_status
            quantidade_niveis += 1

            for posicao in nivel.posicoes:

                posicao.ativo = novo_status
                quantidade_posicoes += 1

    db.session.commit()

    if novo_status:

        flash(
            (
                "Prédio ativado com sucesso. "
                f"Também foram ativados {quantidade_modulos} módulo(s), "
                f"{quantidade_niveis} nível(is) e "
                f"{quantidade_posicoes} posição(ões)."
            ),
            "success"
        )

    else:

        flash(
            (
                "Prédio inativado com sucesso. "
                f"Também foram inativados {quantidade_modulos} módulo(s), "
                f"{quantidade_niveis} nível(is) e "
                f"{quantidade_posicoes} posição(ões). "
                "Os endereçamentos existentes foram preservados."
            ),
            "success"
        )

    return redirect(
        url_for(
            "predio.listar"
        )
    )