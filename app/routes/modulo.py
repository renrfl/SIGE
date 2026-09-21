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
    Predio,
    ProdutoEndereco,
    Rua,
    Usuario
)


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

    rua_id = request.args.get(
        "rua_id",
        type=int
    )

    predio_id = request.args.get(
        "predio_id",
        type=int
    )

    ruas = Rua.query.filter_by(
        ativo=True
    ).order_by(
        Rua.nome
    ).all()

    predios_query = Predio.query.filter_by(
        ativo=True
    )

    if rua_id:

        predios_query = predios_query.filter_by(
            rua_id=rua_id
        )

    predios = predios_query.order_by(
        Predio.nome
    ).all()

    modulos_query = Modulo.query.join(
        Predio
    )

    if rua_id:

        modulos_query = modulos_query.filter(
            Predio.rua_id == rua_id
        )

    if predio_id:

        modulos_query = modulos_query.filter(
            Modulo.predio_id == predio_id
        )

    modulos = modulos_query.order_by(
        Predio.nome,
        Modulo.nome
    ).all()

    return render_template(
        "modulo/listar.html",
        modulos=modulos,
        ruas=ruas,
        predios=predios,
        rua_id=rua_id,
        predio_id=predio_id
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


@modulo_bp.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    if session.get("usuario_perfil") != "ADMINISTRADOR":

        flash(
            "Apenas administradores podem excluir módulos.",
            "danger"
        )

        return redirect(
            url_for("modulo.listar")
        )

    modulo = Modulo.query.get_or_404(
        id
    )

    niveis = list(
        modulo.niveis
    )

    if not niveis:

        db.session.delete(
            modulo
        )

        db.session.commit()

        flash(
            "Módulo vazio excluído com sucesso.",
            "success"
        )

        return redirect(
            url_for("modulo.listar")
        )

    posicoes = []

    for nivel in niveis:

        posicoes.extend(
            list(nivel.posicoes)
        )

    if posicoes:

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
                    "Não é possível excluir este módulo porque existe "
                    "pelo menos um produto endereçado em uma de suas "
                    "posições. Remova ou transfira os endereçamentos "
                    "antes de continuar."
                ),
                "danger"
            )

            return redirect(
                url_for("modulo.listar")
            )

    senha = request.form.get(
        "senha",
        ""
    )

    if not senha:

        flash(
            (
                "Este módulo possui uma estrutura cadastrada. "
                "Informe sua senha de administrador para confirmar "
                "a exclusão."
            ),
            "warning"
        )

        return redirect(
            url_for("modulo.listar")
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
            url_for("modulo.listar")
        )

    quantidade_niveis = len(
        niveis
    )

    quantidade_posicoes = len(
        posicoes
    )

    try:

        for nivel in niveis:

            for posicao in list(nivel.posicoes):

                db.session.delete(
                    posicao
                )

            db.session.delete(
                nivel
            )

        db.session.delete(
            modulo
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Não foi possível excluir a estrutura do módulo.",
            "danger"
        )

        return redirect(
            url_for("modulo.listar")
        )

    flash(
        (
            "Estrutura excluída com sucesso. "
            f"Foram excluídos {quantidade_niveis} nível(is), "
            f"{quantidade_posicoes} posição(ões) "
            "e o módulo selecionado."
        ),
        "success"
    )

    return redirect(
        url_for("modulo.listar")
    )