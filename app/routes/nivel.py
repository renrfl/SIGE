from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from app import db
from app.models import (
    Modulo,
    Nivel,
    ProdutoEndereco,
    Usuario
)


nivel_bp = Blueprint(
    "nivel",
    __name__,
    url_prefix="/niveis"
)


def preparar_modulos():

    modulos = Modulo.query.filter_by(
        ativo=True
    ).order_by(
        Modulo.nome
    ).all()

    for modulo in modulos:

        niveis = sorted(
            modulo.niveis,
            key=lambda nivel: nivel.nome.lower()
        )

        modulo.niveis_cadastrados = ", ".join(
            nivel.nome
            for nivel in niveis
        )

    return modulos


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

    modulos = preparar_modulos()

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

    modulos = preparar_modulos()

    if (
        nivel.modulo
        and nivel.modulo not in modulos
    ):

        modulo_atual = nivel.modulo

        niveis = sorted(
            modulo_atual.niveis,
            key=lambda item: item.nome.lower()
        )

        modulo_atual.niveis_cadastrados = ", ".join(
            item.nome
            for item in niveis
        )

        modulos.append(
            modulo_atual
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


@nivel_bp.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    if session.get("usuario_perfil") != "ADMINISTRADOR":

        flash(
            "Apenas administradores podem excluir níveis.",
            "danger"
        )

        return redirect(
            url_for(
                "nivel.listar"
            )
        )

    nivel = Nivel.query.get_or_404(
        id
    )

    posicoes = list(
        nivel.posicoes
    )

    if not posicoes:

        db.session.delete(
            nivel
        )

        db.session.commit()

        flash(
            "Nível vazio excluído com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "nivel.listar"
            )
        )

    posicoes_ids = [
        posicao.id
        for posicao in posicoes
    ]

    endereco = ProdutoEndereco.query.filter(
        ProdutoEndereco.posicao_id.in_(
            posicoes_ids
        )
    ).first()

    if endereco:

        flash(
            (
                "Não é possível excluir este nível porque existe "
                "pelo menos um produto endereçado em uma de suas "
                "posições. Remova ou transfira os endereçamentos "
                "antes de continuar."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "nivel.listar"
            )
        )

    senha = request.form.get(
        "senha",
        ""
    )

    if not senha:

        flash(
            (
                "Este nível possui posições cadastradas. "
                "Informe sua senha de administrador para confirmar "
                "a exclusão da estrutura."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "nivel.listar"
            )
        )

    usuario = Usuario.query.get(
        session.get("usuario_id")
    )

    if (
        not usuario
        or not usuario.ativo
        or usuario.perfil != "ADMINISTRADOR"
        or not usuario.verificar_senha(senha)
    ):

        flash(
            "Senha de administrador incorreta.",
            "danger"
        )

        return redirect(
            url_for(
                "nivel.listar"
            )
        )

    quantidade_posicoes = len(
        posicoes
    )

    try:

        for posicao in posicoes:

            db.session.delete(
                posicao
            )

        db.session.delete(
            nivel
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Não foi possível excluir a estrutura do nível.",
            "danger"
        )

        return redirect(
            url_for(
                "nivel.listar"
            )
        )

    flash(
        (
            "Estrutura excluída com sucesso. "
            f"Foram excluídas {quantidade_posicoes} posição(ões) "
            "e o nível selecionado."
        ),
        "success"
    )

    return redirect(
        url_for(
            "nivel.listar"
        )
    )