from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Rua


rua_bp = Blueprint(
    "rua",
    __name__,
    url_prefix="/ruas"
)


@rua_bp.route("/")
def listar():

    ruas = Rua.query.order_by(
        Rua.nome
    ).all()

    return render_template(
        "rua/listar.html",
        ruas=ruas
    )


@rua_bp.route("/novo", methods=["GET", "POST"])
def novo():

    if request.method == "POST":

        nome = request.form[
            "nome"
        ].strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        if not nome:

            flash(
                "Informe o nome da rua.",
                "danger"
            )

            return redirect(
                url_for(
                    "rua.novo"
                )
            )

        rua_existente = Rua.query.filter_by(
            nome=nome
        ).first()

        if rua_existente:

            flash(
                "Já existe uma rua com esse nome.",
                "warning"
            )

            return redirect(
                url_for(
                    "rua.novo"
                )
            )

        rua = Rua(
            nome=nome,
            descricao=descricao,
            ativo=True
        )

        db.session.add(
            rua
        )

        db.session.commit()

        flash(
            "Rua cadastrada com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "rua.listar"
            )
        )

    return render_template(
        "rua/form.html",
        rua=None
    )


@rua_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar(id):

    rua = Rua.query.get_or_404(
        id
    )

    if request.method == "POST":

        nome = request.form[
            "nome"
        ].strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        if not nome:

            flash(
                "Informe o nome da rua.",
                "danger"
            )

            return redirect(
                url_for(
                    "rua.editar",
                    id=rua.id
                )
            )

        rua_existente = Rua.query.filter(
            Rua.nome == nome,
            Rua.id != rua.id
        ).first()

        if rua_existente:

            flash(
                "Já existe uma rua com esse nome.",
                "warning"
            )

            return redirect(
                url_for(
                    "rua.editar",
                    id=rua.id
                )
            )

        rua.nome = nome
        rua.descricao = descricao

        db.session.commit()

        flash(
            "Rua atualizada com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "rua.listar"
            )
        )

    return render_template(
        "rua/form.html",
        rua=rua
    )


@rua_bp.route(
    "/alternar-status/<int:id>",
    methods=["POST"]
)
def alternar_status(id):

    rua = Rua.query.get_or_404(
        id
    )

    novo_status = not rua.ativo

    rua.ativo = novo_status

    quantidade_predios = 0
    quantidade_modulos = 0
    quantidade_niveis = 0
    quantidade_posicoes = 0

    for predio in rua.predios:

        predio.ativo = novo_status
        quantidade_predios += 1

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
                "Rua ativada com sucesso. "
                f"Também foram ativados {quantidade_predios} prédio(s), "
                f"{quantidade_modulos} módulo(s), "
                f"{quantidade_niveis} nível(is) e "
                f"{quantidade_posicoes} posição(ões)."
            ),
            "success"
        )

    else:

        flash(
            (
                "Rua inativada com sucesso. "
                f"Também foram inativados {quantidade_predios} prédio(s), "
                f"{quantidade_modulos} módulo(s), "
                f"{quantidade_niveis} nível(is) e "
                f"{quantidade_posicoes} posição(ões). "
                "Os endereçamentos existentes foram preservados."
            ),
            "success"
        )

    return redirect(
        url_for(
            "rua.listar"
        )
    )