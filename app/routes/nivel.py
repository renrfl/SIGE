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

    niveis = Nivel.query.order_by(
        Nivel.nome
    ).all()

    return render_template(
        "nivel/listar.html",
        niveis=niveis
    )


@nivel_bp.route("/novo", methods=["GET", "POST"])
def novo():

    modulos = Modulo.query.filter_by(
        ativo=True
    ).order_by(
        Modulo.nome
    ).all()

    if request.method == "POST":

        nome = request.form[
            "nome"
        ].strip()

        modulo_id = request.form.get(
            "modulo_id",
            type=int
        )

        if not nome:

            flash(
                "Informe o nome do nível.",
                "danger"
            )

            return redirect(
                url_for(
                    "nivel.novo"
                )
            )

        if not modulo_id:

            flash(
                "Selecione o módulo do nível.",
                "danger"
            )

            return redirect(
                url_for(
                    "nivel.novo"
                )
            )

        modulo = Modulo.query.filter_by(
            id=modulo_id,
            ativo=True
        ).first()

        if not modulo:

            flash(
                "O módulo selecionado não está disponível.",
                "danger"
            )

            return redirect(
                url_for(
                    "nivel.novo"
                )
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
                url_for(
                    "nivel.novo"
                )
            )

        nivel = Nivel(
            nome=nome,
            modulo_id=modulo_id,
            ativo=True
        )

        db.session.add(
            nivel
        )

        db.session.commit()

        flash(
            "Nível cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "nivel.listar"
            )
        )

    return render_template(
        "nivel/form.html",
        nivel=None,
        modulos=modulos
    )


@nivel_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar(id):

    nivel = Nivel.query.get_or_404(
        id
    )

    modulos = Modulo.query.filter_by(
        ativo=True
    ).order_by(
        Modulo.nome
    ).all()

    if (
        nivel.modulo
        and nivel.modulo not in modulos
    ):

        modulos.append(
            nivel.modulo
        )

        modulos.sort(
            key=lambda modulo: modulo.nome.lower()
        )

    if request.method == "POST":

        nome = request.form[
            "nome"
        ].strip()

        modulo_id = request.form.get(
            "modulo_id",
            type=int
        )

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

        if not modulo_id:

            flash(
                "Selecione o módulo do nível.",
                "danger"
            )

            return redirect(
                url_for(
                    "nivel.editar",
                    id=nivel.id
                )
            )

        modulo = Modulo.query.get(
            modulo_id
        )

        if not modulo:

            flash(
                "O módulo selecionado não foi encontrado.",
                "danger"
            )

            return redirect(
                url_for(
                    "nivel.editar",
                    id=nivel.id
                )
            )

        if (
            not modulo.ativo
            and modulo.id != nivel.modulo_id
        ):

            flash(
                "Não é permitido mover o nível para um módulo inativo.",
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
            url_for(
                "nivel.listar"
            )
        )

    return render_template(
        "nivel/form.html",
        nivel=nivel,
        modulos=modulos
    )


@nivel_bp.route(
    "/alternar-status/<int:id>",
    methods=["POST"]
)
def alternar_status(id):

    nivel = Nivel.query.get_or_404(
        id
    )

    novo_status = not nivel.ativo

    nivel.ativo = novo_status

    for posicao in nivel.posicoes:

        posicao.ativo = novo_status

    db.session.commit()

    if novo_status:

        flash(
            (
                "Nível ativado com sucesso. "
                "As posições vinculadas também foram ativadas."
            ),
            "success"
        )

    else:

        flash(
            (
                "Nível inativado com sucesso. "
                "As posições vinculadas não aparecerão em novos "
                "endereçamentos."
            ),
            "success"
        )

    return redirect(
        url_for(
            "nivel.listar"
        )
    )