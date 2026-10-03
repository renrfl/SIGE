from datetime import datetime, timezone

from flask import Flask, flash, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app():

    app = Flask(__name__)

    app.config.from_object("config.Config")

    db.init_app(app)

    from app.models import (
        Rua,
        Predio,
        Modulo,
        Nivel,
        Posicao,
        Produto,
        ProdutoEndereco,
        Usuario,
        DivergenciaCodigoBarras
    )

    from app.routes.home import home_bp
    from app.routes.rua import rua_bp
    from app.routes.predio import predio_bp
    from app.routes.modulo import modulo_bp
    from app.routes.nivel import nivel_bp
    from app.routes.posicao import posicao_bp
    from app.routes.produto import produto_bp
    from app.routes.endereco import endereco_bp
    from app.routes.consulta import consulta_bp
    from app.routes.etiqueta import etiqueta_bp
    from app.routes.auth import auth_bp
    from app.routes.usuario import usuario_bp
    from app.routes.divergencia import divergencia_bp

    @app.before_request
    def proteger_area_administrativa():

        if request.endpoint in (
            None,
            "static",
            "auth.login",
            "auth.logout"
        ):
            return None

        acesso_restrito = (
            request.path == "/admin"
            or request.path.startswith("/admin/")
            or request.endpoint in (
                "consulta.gerenciar_enderecos",
                "consulta.remover_endereco"
            )
        )

        usuario_id = session.get("usuario_id")

        if usuario_id is None:

            if acesso_restrito:
                return redirect(url_for("auth.login"))

            return None

        agora = datetime.now(timezone.utc)
        mensagem = None

        try:

            ultima_atividade = datetime.fromisoformat(
                session.get("ultima_atividade", "")
            )

            if ultima_atividade.tzinfo is None:
                ultima_atividade = ultima_atividade.replace(
                    tzinfo=timezone.utc
                )

            tempo_inativo = agora - ultima_atividade

            if (
                tempo_inativo.total_seconds() < 0
                or tempo_inativo >= app.permanent_session_lifetime
            ):
                mensagem = (
                    "Sua sessão expirou por inatividade. "
                    "Faça login novamente."
                )

        except (ValueError, TypeError, OverflowError):

            mensagem = (
                "Sua sessão não é mais válida. "
                "Faça login novamente."
            )

        if mensagem is None:

            usuario = None

            if type(usuario_id) is int and usuario_id > 0:
                usuario = db.session.get(Usuario, usuario_id)

            if not usuario or not usuario.ativo:
                mensagem = (
                    "Seu acesso foi encerrado. "
                    "Faça login com um usuário ativo."
                )

        if mensagem:

            session.clear()
            flash(mensagem, "warning")

            if acesso_restrito:
                return redirect(url_for("auth.login"))

            return None

        session.permanent = True
        session["usuario_nome"] = usuario.nome
        session["usuario_perfil"] = usuario.perfil
        session["ultima_atividade"] = agora.isoformat()

        return None

    app.register_blueprint(home_bp)
    app.register_blueprint(consulta_bp)
    app.register_blueprint(auth_bp)

    app.register_blueprint(
        rua_bp,
        url_prefix="/admin/ruas"
    )

    app.register_blueprint(
        predio_bp,
        url_prefix="/admin/predios"
    )

    app.register_blueprint(
        modulo_bp,
        url_prefix="/admin/modulos"
    )

    app.register_blueprint(
        nivel_bp,
        url_prefix="/admin/niveis"
    )

    app.register_blueprint(
        posicao_bp,
        url_prefix="/admin/posicoes"
    )

    app.register_blueprint(
        produto_bp,
        url_prefix="/admin/produtos"
    )

    app.register_blueprint(
        endereco_bp,
        url_prefix="/admin/enderecos"
    )

    app.register_blueprint(
        etiqueta_bp,
        url_prefix="/admin/etiquetas"
    )

    app.register_blueprint(
        usuario_bp,
        url_prefix="/admin/usuarios"
    )

    app.register_blueprint(
        divergencia_bp,
        url_prefix="/admin/divergencias"
    )

    with app.app_context():

        db.create_all()

    return app