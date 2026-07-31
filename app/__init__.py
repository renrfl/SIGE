from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():

    app = Flask(__name__)

    app.config.from_object("config.Config")

    db.init_app(app)

    from app import models

    with app.app_context():
        db.create_all()

    from app.routes.home import home_bp
    from app.routes.estrutura import estrutura_bp
    from app.routes.rua import rua_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(estrutura_bp)
    app.register_blueprint(rua_bp)

    return app
