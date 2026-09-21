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
    Predio,
    ProdutoEndereco,
    Rua,
    Usuario
)


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


@predio_bp.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    if session.get("usuario_perfil") != "ADMINISTRADOR":

        flash(
            "Apenas administradores podem excluir prédios.",
            "danger"
        )

        return redirect(
            url_for(
                "predio.listar"
            )
        )

    predio = Predio.query.get_or_404(
        id
    )

    modulos = list(
        predio.modulos
    )

    if not modulos:

        db.session.delete(
            predio
        )

        db.session.commit()

        flash(
            "Prédio vazio excluído com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "predio.listar"
            )
        )

    niveis = []
    posicoes = []

    for modulo in modulos:

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
                    "Não é possível excluir este prédio porque existe "
                    "pelo menos um produto endereçado em uma de suas "
                    "posições. Remova ou transfira os endereçamentos "
                    "antes de continuar."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "predio.listar"
                )
            )

    senha = request.form.get(
        "senha",
        ""
    )

    if not senha:

        flash(
            (
                "Este prédio possui uma estrutura cadastrada. "
                "Informe sua senha de administrador para confirmar "
                "a exclusão."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "predio.listar"
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
                "predio.listar"
            )
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

        for modulo in modulos:

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

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Não foi possível excluir a estrutura do prédio.",
            "danger"
        )

        return redirect(
            url_for(
                "predio.listar"
            )
        )

    flash(
        (
            "Estrutura excluída com sucesso. "
            f"Foram excluídos {quantidade_modulos} módulo(s), "
            f"{quantidade_niveis} nível(is), "
            f"{quantidade_posicoes} posição(ões) "
            "e o prédio selecionado."
        ),
        "success"
    )

    return redirect(
        url_for(
            "predio.listar"
        )
    )