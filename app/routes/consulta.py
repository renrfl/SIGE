from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from sqlalchemy import String, cast, or_

from app import db
from app.models import Produto, ProdutoEndereco


consulta_bp = Blueprint(
    "consulta",
    __name__,
    url_prefix="/consulta"
)


def carregar_enderecos_produto(produto):

    enderecos = ProdutoEndereco.query.filter_by(
        produto_id=produto.id
    ).all()

    endereco = (
        enderecos[0]
        if enderecos
        else None
    )

    return (
        endereco,
        enderecos,
        len(enderecos)
    )


@consulta_bp.route("/", methods=["GET", "POST"])
def index():

    produto = None
    endereco = None
    enderecos = []
    total_enderecos = 0
    resultados_pesquisa = []
    pesquisa = ""

    if request.method == "POST":

        pesquisa = request.form[
            "pesquisa"
        ].strip()

        if pesquisa:

            filtros_exatos = [
                Produto.codigo_barras == pesquisa
            ]

            if pesquisa.isdigit():

                filtros_exatos.append(
                    Produto.codigo == int(
                        pesquisa
                    )
                )

            produto = Produto.query.filter(
                or_(
                    *filtros_exatos
                )
            ).first()

            if (
                not produto
                and session.get(
                    "usuario_id"
                )
            ):

                resultados_pesquisa = (
                    Produto.query
                    .filter(
                        Produto.descricao.ilike(
                            f"%{pesquisa}%"
                        )
                    )
                    .order_by(
                        Produto.descricao
                    )
                    .limit(20)
                    .all()
                )

                if (
                    len(
                        resultados_pesquisa
                    )
                    == 1
                ):

                    produto = (
                        resultados_pesquisa[
                            0
                        ]
                    )

                    resultados_pesquisa = []

            if produto:

                (
                    endereco,
                    enderecos,
                    total_enderecos
                ) = carregar_enderecos_produto(
                    produto
                )

    return render_template(
        "consulta/index.html",
        produto=produto,
        endereco=endereco,
        enderecos=enderecos,
        total_enderecos=total_enderecos,
        resultados_pesquisa=resultados_pesquisa,
        pesquisa=pesquisa
    )


@consulta_bp.route(
    "/buscar-produtos",
    methods=["GET"]
)
def buscar_produtos():

    if not session.get(
        "usuario_id"
    ):

        return jsonify([])

    termo = request.args.get(
        "q",
        ""
    ).strip()

    if len(termo) < 2:

        return jsonify([])

    padrao = f"%{termo}%"

    produtos = (
        Produto.query
        .filter(
            or_(
                cast(
                    Produto.codigo,
                    String
                ).ilike(
                    padrao
                ),
                Produto.codigo_barras.ilike(
                    padrao
                ),
                Produto.descricao.ilike(
                    padrao
                )
            )
        )
        .order_by(
            Produto.descricao
        )
        .limit(20)
        .all()
    )

    resultados = []

    for produto in produtos:

        resultados.append(
            {
                "codigo": produto.codigo,
                "codigo_barras": (
                    produto.codigo_barras
                    or ""
                ),
                "descricao": produto.descricao
            }
        )

    return jsonify(
        resultados
    )


@consulta_bp.route(
    "/produto/<int:codigo>",
    methods=["GET"]
)
def consultar_produto(codigo):

    produto = Produto.query.filter_by(
        codigo=codigo
    ).first_or_404()

    (
        endereco,
        enderecos,
        total_enderecos
    ) = carregar_enderecos_produto(
        produto
    )

    return render_template(
        "consulta/index.html",
        produto=produto,
        endereco=endereco,
        enderecos=enderecos,
        total_enderecos=total_enderecos,
        resultados_pesquisa=[],
        pesquisa=str(
            produto.codigo
        )
    )


@consulta_bp.route(
    "/produto/<int:codigo>/enderecos",
    methods=["GET"]
)
def gerenciar_enderecos(codigo):

    if not session.get("usuario_id"):

        flash(
            "Faça login para acessar esta função.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    produto = Produto.query.filter_by(
        codigo=codigo
    ).first_or_404()

    enderecos = ProdutoEndereco.query.filter_by(
        produto_id=produto.id
    ).all()

    return render_template(
        "consulta/gerenciar_enderecos.html",
        produto=produto,
        enderecos=enderecos,
        total_enderecos=len(enderecos)
    )


@consulta_bp.route(
    "/endereco/<int:id>/remover",
    methods=["POST"]
)
def remover_endereco(id):

    if not session.get("usuario_id"):

        flash(
            "Faça login para acessar esta função.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    endereco = ProdutoEndereco.query.get_or_404(id)

    codigo_produto = endereco.produto.codigo
    produto_id = endereco.produto_id

    db.session.delete(endereco)
    db.session.commit()

    flash(
        "Endereço removido com sucesso.",
        "success"
    )

    enderecos_restantes = ProdutoEndereco.query.filter_by(
        produto_id=produto_id
    ).count()

    if enderecos_restantes > 0:

        return redirect(
            url_for(
                "consulta.gerenciar_enderecos",
                codigo=codigo_produto
            )
        )

    return redirect(
        url_for("consulta.index")
    )
