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
    ProdutoEndereco,
    Rua,
    Usuario
)


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


@rua_bp.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    if session.get("usuario_perfil") != "ADMINISTRADOR":

        flash(
            "Apenas administradores podem excluir ruas.",
            "danger"
        )

        return redirect(
            url_for(
                "rua.listar"
            )
        )

    rua = Rua.query.get_or_404(
        id
    )

    predios = list(
        rua.predios
    )

    if not predios:

        db.session.delete(
            rua
        )

        db.session.commit()

        flash(
            "Rua vazia excluída com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "rua.listar"
            )
        )

    modulos = []
    niveis = []
    posicoes = []

    for predio in predios:

        for modulo in predio.modulos:

            modulos.append(
                modulo
            )

            for nivel in modulo.niveis:

                niveis.append(
                    nivel
                )

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
                    "Não é possível excluir esta rua porque existe "
                    "pelo menos um produto endereçado em uma de suas "
                    "posições. Remova ou transfira os endereçamentos "
                    "antes de continuar."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "rua.listar"
                )
            )

    senha = request.form.get(
        "senha",
        ""
    )

    if not senha:

        flash(
            (
                "Esta rua possui uma estrutura cadastrada. "
                "Informe sua senha de administrador para confirmar "
                "a exclusão."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "rua.listar"
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
                "rua.listar"
            )
        )

    quantidade_predios = len(
        predios
    )

    quantidade_modulos = len(
        modulos
    )

    quantidade_niveis = len(
        niveis
    )

    quantidade_posicoes = len(
        posicoes
    )

    try:

        for predio in predios:

            for modulo in list(predio.modulos):

                for nivel in list(modulo.niveis):

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

            db.session.delete(
                predio
            )

        db.session.delete(
            rua
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Não foi possível excluir a estrutura da rua.",
            "danger"
        )

        return redirect(
            url_for(
                "rua.listar"
            )
        )

    flash(
        (
            "Estrutura excluída com sucesso. "
            f"Foram excluídos {quantidade_predios} prédio(s), "
            f"{quantidade_modulos} módulo(s), "
            f"{quantidade_niveis} nível(is), "
            f"{quantidade_posicoes} posição(ões) "
            "e a rua selecionada."
        ),
        "success"
    )

    return redirect(
        url_for(
            "rua.listar"
        )
    )