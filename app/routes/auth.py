from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from app.models import Usuario


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/admin"
)


def login_obrigatorio(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "usuario_id" not in session:

            return redirect(
                url_for("auth.login")
            )

        return func(*args, **kwargs)

    return wrapper


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        login = request.form["login"].strip()

        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(
            login=login,
            ativo=True
        ).first()

        if usuario and usuario.verificar_senha(senha):

            session["usuario_id"] = usuario.id

            session["usuario_nome"] = usuario.nome

            flash(
                f"Bem-vindo, {usuario.nome}.",
                "success"
            )

            return redirect(
                url_for("home.index")
            )

        flash(
            "Usuário ou senha inválidos.",
            "danger"
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route("/logout")
def logout():

    session.clear()

    flash(
        "Sessão encerrada.",
        "success"
    )

    return redirect(
        url_for("consulta.index")
    )