from flask import Blueprint, render_template

estrutura_bp = Blueprint("estrutura", __name__)


@estrutura_bp.route("/estrutura")
def estrutura():

    return render_template("estrutura.html")