from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Modulo, Predio


modulo_bp = Blueprint(
    "modulo",
    __name__,
    url_prefix="/modulos"
)


def preparar_predios():

    predios = Predio.query.filter_by(
        ativo=True
    ).order_by(
        Predio.nome
    ).all()

    for predio in predios:

        predio.modulos_cadastrados = len(
            predio.modulos
        )

    return predios


@modulo_bp.route("/")
def listar():

    modulos = Modulo.query.order_by(
        Modulo.nome
    ).all()

    return render_template(
        "modulo/listar.html",
        modulos=modulos
    )


@modulo_bp.route("/novo", methods=["GET", "POST"])
def novo():

    predios = preparar_predios()

    if request.method == "POST":

        nome = request.form["nome"].strip()

        predio_id = request.form.get(
            "predio_id",
            type=int
        )

        if not nome:

            flash(
                "Informe o nome do módulo.",
                "danger"
            )

            return redirect(
                url_for("modulo.novo")
            )

        if not predio_id:

            flash(
                "Selecione o prédio do módulo.",
                "danger"
            )

            return redirect(
                url_for("modulo.novo")
            )

        predio = Predio.query.filter_by(
            id=predio_id,
            ativo=True
        ).first()

        if not predio:

            flash(
                "O prédio selecionado não está disponível.",
                "danger"
            )

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
            predio_id=predio_id,
            ativo=True
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


@modulo_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar(id):

    modulo = Modulo.query.get_or_404(id)

    predios = preparar_predios()

    if (
        modulo.predio
        and modulo.predio not in predios
    ):

        predio_atual = modulo.predio

        predio_atual.modulos_cadastrados = len(
            predio_atual.modulos
        )

        predios.append(
            predio_atual
        )

        predios.sort(
            key=lambda predio: predio.nome.lower()
        )

    if request.method == "POST":

        nome = request.form["nome"].strip()

        predio_id = request.form.get(
            "predio_id",
            type=int
        )

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

        if not predio_id:

            flash(
                "Selecione o prédio do módulo.",
                "danger"
            )

            return redirect(
                url_for(
                    "modulo.editar",
                    id=modulo.id
                )
            )

        predio = Predio.query.get(
            predio_id
        )

        if not predio:

            flash(
                "O prédio selecionado não foi encontrado.",
                "danger"
            )

            return redirect(
                url_for(
                    "modulo.editar",
                    id=modulo.id
                )
            )

        if (
            not predio.ativo
            and predio.id != modulo.predio_id
        ):

            flash(
                "Não é permitido mover o módulo para um prédio inativo.",
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


@modulo_bp.route(
    "/alternar-status/<int:id>",
    methods=["POST"]
)
def alternar_status(id):

    modulo = Modulo.query.get_or_404(id)

    novo_status = not modulo.ativo

    modulo.ativo = novo_status

    quantidade_niveis = 0
    quantidade_posicoes = 0

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
                "Módulo ativado com sucesso. "
                f"Também foram ativados {quantidade_niveis} nível(is) "
                f"e {quantidade_posicoes} posição(ões)."
            ),
            "success"
        )

    else:

        flash(
            (
                "Módulo inativado com sucesso. "
                f"Também foram inativados {quantidade_niveis} nível(is) "
                f"e {quantidade_posicoes} posição(ões). "
                "Os endereçamentos existentes foram preservados."
            ),
            "success"
        )

    return redirect(
        url_for("modulo.listar")
    )