from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Nivel, Posicao, ProdutoEndereco


posicao_bp = Blueprint(
    "posicao",
    __name__,
    url_prefix="/posicoes"
)


def obter_destino_retorno():

    origem = request.args.get(
        "origem",
        ""
    ).strip().lower()

    if origem == "enderecos":

        return url_for(
            "endereco.listar"
        )

    return url_for(
        "posicao.listar"
    )


@posicao_bp.route("/")
def listar():

    posicoes = Posicao.query.order_by(
        Posicao.nome
    ).all()

    posicoes_ocupadas = {
        resultado[0]
        for resultado in (
            db.session.query(
                ProdutoEndereco.posicao_id
            )
            .distinct()
            .all()
        )
    }

    for posicao in posicoes:

        posicao.ocupada = (
            posicao.id
            in posicoes_ocupadas
        )

    return render_template(
        "posicao/listar.html",
        posicoes=posicoes
    )


@posicao_bp.route("/novo", methods=["GET", "POST"])
def novo():

    niveis = Nivel.query.filter_by(
        ativo=True
    ).order_by(
        Nivel.nome
    ).all()

    if request.method == "POST":

        nome = request.form[
            "nome"
        ].strip()

        nivel_id = request.form.get(
            "nivel_id",
            type=int
        )

        if not nome:

            flash(
                "Informe o nome da posição.",
                "danger"
            )

            return redirect(
                url_for(
                    "posicao.novo"
                )
            )

        if not nivel_id:

            flash(
                "Selecione o nível da posição.",
                "danger"
            )

            return redirect(
                url_for(
                    "posicao.novo"
                )
            )

        nivel = Nivel.query.filter_by(
            id=nivel_id,
            ativo=True
        ).first()

        if not nivel:

            flash(
                "O nível selecionado não está disponível.",
                "danger"
            )

            return redirect(
                url_for(
                    "posicao.novo"
                )
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
                url_for(
                    "posicao.novo"
                )
            )

        posicao = Posicao(
            nome=nome,
            nivel_id=nivel_id,
            ativo=True
        )

        db.session.add(
            posicao
        )

        db.session.commit()

        flash(
            "Posição cadastrada com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "posicao.listar"
            )
        )

    return render_template(
        "posicao/form.html",
        posicao=None,
        niveis=niveis
    )


@posicao_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar(id):

    posicao = Posicao.query.get_or_404(
        id
    )

    niveis = Nivel.query.filter_by(
        ativo=True
    ).order_by(
        Nivel.nome
    ).all()

    if (
        posicao.nivel
        and posicao.nivel not in niveis
    ):

        niveis.append(
            posicao.nivel
        )

        niveis.sort(
            key=lambda nivel: nivel.nome.lower()
        )

    if request.method == "POST":

        nome = request.form[
            "nome"
        ].strip()

        nivel_id = request.form.get(
            "nivel_id",
            type=int
        )

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

        if not nivel_id:

            flash(
                "Selecione o nível da posição.",
                "danger"
            )

            return redirect(
                url_for(
                    "posicao.editar",
                    id=posicao.id
                )
            )

        nivel = Nivel.query.get(
            nivel_id
        )

        if not nivel:

            flash(
                "O nível selecionado não foi encontrado.",
                "danger"
            )

            return redirect(
                url_for(
                    "posicao.editar",
                    id=posicao.id
                )
            )

        if (
            not nivel.ativo
            and nivel.id != posicao.nivel_id
        ):

            flash(
                "Não é permitido mover a posição para um nível inativo.",
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
            url_for(
                "posicao.listar"
            )
        )

    return render_template(
        "posicao/form.html",
        posicao=posicao,
        niveis=niveis
    )


@posicao_bp.route(
    "/alternar-status/<int:id>",
    methods=["POST"]
)
def alternar_status(id):

    posicao = Posicao.query.get_or_404(
        id
    )

    posicao.ativo = not posicao.ativo

    db.session.commit()

    if posicao.ativo:

        flash(
            "Posição ativada com sucesso.",
            "success"
        )

    else:

        flash(
            (
                "Posição inativada com sucesso. "
                "Ela não aparecerá em novos endereçamentos."
            ),
            "success"
        )

    return redirect(
        obter_destino_retorno()
    )


@posicao_bp.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    posicao = Posicao.query.get_or_404(
        id
    )

    endereco = ProdutoEndereco.query.filter_by(
        posicao_id=posicao.id
    ).first()

    if endereco:

        flash(
            (
                "Não é possível excluir esta posição porque existe "
                "um produto endereçado nela. Transfira ou remova o "
                "endereçamento antes de continuar."
            ),
            "danger"
        )

        return redirect(
            obter_destino_retorno()
        )

    db.session.delete(
        posicao
    )

    db.session.commit()

    flash(
        "Posição vazia excluída com sucesso.",
        "success"
    )

    return redirect(
        obter_destino_retorno()
    )