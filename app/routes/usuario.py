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
from app.models import Usuario
from app.routes.auth import login_obrigatorio


usuario_bp = Blueprint(
    "usuario",
    __name__
)


@usuario_bp.route("/")
@login_obrigatorio
def listar():

    usuarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    return render_template(
        "usuario/listar.html",
        usuarios=usuarios
    )


@usuario_bp.route("/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        login = request.form.get(
            "login",
            ""
        ).strip()

        senha = request.form.get(
            "senha",
            ""
        )

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
        )

        if not nome or not login or not senha:

            flash(
                "Preencha todos os campos obrigatórios.",
                "danger"
            )

            return render_template(
                "usuario/form.html",
                usuario=None
            )

        if senha != confirmar_senha:

            flash(
                "A confirmação da senha não confere.",
                "danger"
            )

            return render_template(
                "usuario/form.html",
                usuario=None
            )

        usuario_existente = Usuario.query.filter_by(
            login=login
        ).first()

        if usuario_existente:

            flash(
                "Já existe um usuário com esse login.",
                "danger"
            )

            return render_template(
                "usuario/form.html",
                usuario=None
            )

        usuario = Usuario(
            nome=nome,
            login=login,
            ativo=True
        )

        usuario.definir_senha(senha)

        db.session.add(usuario)
        db.session.commit()

        flash(
            "Usuário cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("usuario.listar")
        )

    return render_template(
        "usuario/form.html",
        usuario=None
    )


@usuario_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(usuario_id):

    usuario = Usuario.query.get_or_404(
        usuario_id
    )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        login = request.form.get(
            "login",
            ""
        ).strip()

        if not nome or not login:

            flash(
                "Preencha todos os campos obrigatórios.",
                "danger"
            )

            return render_template(
                "usuario/form.html",
                usuario=usuario
            )

        usuario_existente = Usuario.query.filter(
            Usuario.login == login,
            Usuario.id != usuario.id
        ).first()

        if usuario_existente:

            flash(
                "Já existe outro usuário com esse login.",
                "danger"
            )

            return render_template(
                "usuario/form.html",
                usuario=usuario
            )

        usuario.nome = nome
        usuario.login = login

        db.session.commit()

        if session.get("usuario_id") == usuario.id:
            session["usuario_nome"] = usuario.nome

        flash(
            "Usuário atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("usuario.listar")
        )

    return render_template(
        "usuario/form.html",
        usuario=usuario
    )


@usuario_bp.route("/<int:usuario_id>/senha", methods=["GET", "POST"])
@login_obrigatorio
def alterar_senha(usuario_id):

    usuario = Usuario.query.get_or_404(
        usuario_id
    )

    if request.method == "POST":

        senha = request.form.get(
            "senha",
            ""
        )

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
        )

        if not senha:

            flash(
                "Informe a nova senha.",
                "danger"
            )

            return render_template(
                "usuario/senha.html",
                usuario=usuario
            )

        if senha != confirmar_senha:

            flash(
                "A confirmação da senha não confere.",
                "danger"
            )

            return render_template(
                "usuario/senha.html",
                usuario=usuario
            )

        usuario.definir_senha(senha)

        db.session.commit()

        flash(
            "Senha alterada com sucesso.",
            "success"
        )

        return redirect(
            url_for("usuario.listar")
        )

    return render_template(
        "usuario/senha.html",
        usuario=usuario
    )


@usuario_bp.route("/<int:usuario_id>/status", methods=["POST"])
@login_obrigatorio
def alterar_status(usuario_id):

    usuario = Usuario.query.get_or_404(
        usuario_id
    )

    if session.get("usuario_id") == usuario.id:

        flash(
            "Você não pode inativar o próprio usuário.",
            "danger"
        )

        return redirect(
            url_for("usuario.listar")
        )

    usuario.ativo = not usuario.ativo

    db.session.commit()

    if usuario.ativo:
        mensagem = "Usuário ativado com sucesso."
    else:
        mensagem = "Usuário inativado com sucesso."

    flash(
        mensagem,
        "success"
    )

    return redirect(
        url_for("usuario.listar")
    )