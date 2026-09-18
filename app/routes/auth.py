from datetime import datetime, timezone
from functools import wraps

from flask import (
    Blueprint,
    current_app,
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

        agora = datetime.now(
            timezone.utc
        )

        ultima_atividade = session.get(
            "ultima_atividade"
        )

        if ultima_atividade:

            try:

                ultima_atividade = datetime.fromisoformat(
                    ultima_atividade
                )

                tempo_inativo = (
                    agora - ultima_atividade
                )

                if tempo_inativo > current_app.config[
                    "PERMANENT_SESSION_LIFETIME"
                ]:

                    session.clear()

                    flash(
                        "Sua sessão expirou por inatividade. "
                        "Faça login novamente.",
                        "warning"
                    )

                    return redirect(
                        url_for("auth.login")
                    )

            except (ValueError, TypeError):

                session.clear()

                return redirect(
                    url_for("auth.login")
                )

        session["ultima_atividade"] = (
            agora.isoformat()
        )

        session.modified = True

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

            session.clear()

            session.permanent = True

            session["usuario_id"] = usuario.id

            session["usuario_nome"] = usuario.nome

            session["ultima_atividade"] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            flash(
                f"Bem-vindo, {usuario.nome}.",
                "success"
            )

            return redirect(
                url_for("home.dashboard")
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