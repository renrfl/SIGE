from flask import Flask
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
        Usuario
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

    app.register_blueprint(home_bp)
    app.register_blueprint(rua_bp)
    app.register_blueprint(predio_bp)
    app.register_blueprint(modulo_bp)
    app.register_blueprint(nivel_bp)
    app.register_blueprint(posicao_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(endereco_bp)
    app.register_blueprint(consulta_bp)
    app.register_blueprint(etiqueta_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():

        db.create_all()

    return app