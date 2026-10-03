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
from sqlalchemy.orm import joinedload

from app import db
from app.models import (
    DivergenciaCodigoBarras,
    Produto,
    ProdutoEndereco
)


divergencia_bp = Blueprint(
    "divergencia",
    __name__
)


@divergencia_bp.route("/")
def listar():

    filtro = request.args.get(
        "status",
        "PENDENTE"
    ).strip().upper()

    if filtro == "DIVERGENCIA":
        filtro = "HISTORICO"

    if filtro not in (
        "PENDENTE",
        "HISTORICO",
        "CORRIGIDO",
        "DESCARTADO"
    ):
        filtro = "PENDENTE"

    pesquisa = request.args.get(
        "q",
        ""
    ).strip()

    divergencias = (
        DivergenciaCodigoBarras.query
        .join(Produto)
        .options(
            joinedload(DivergenciaCodigoBarras.produto)
        )
        .order_by(
            DivergenciaCodigoBarras.data_registro.desc(),
            DivergenciaCodigoBarras.id.desc()
        )
        .all()
    )

    totais = {
        "PENDENTE": 0,
        "CORRIGIDO": 0,
        "DESCARTADO": 0,
        "HISTORICO": 0,
        "TODOS": 0,
        "DIVERGENCIA": 0,
        "CORRETO": 0
    }

    itens = []
    termo = pesquisa.casefold()

    for divergencia in divergencias:

        if divergencia.status not in (
            "PENDENTE",
            "CORRIGIDO",
            "DESCARTADO"
        ):
            continue

        totais[divergencia.status] += 1
        totais["TODOS"] += 1
        totais["DIVERGENCIA"] += 1

        if divergencia.status in ("CORRIGIDO", "DESCARTADO"):
            totais["HISTORICO"] += 1

        if filtro == "HISTORICO":

            if divergencia.status not in ("CORRIGIDO", "DESCARTADO"):
                continue

        elif divergencia.status != filtro:
            continue

        produto = divergencia.produto

        if termo:

            valores_pesquisa = (
                str(produto.codigo),
                produto.descricao or "",
                produto.codigo_barras or "",
                divergencia.codigo_barras_cadastrado or "",
                divergencia.codigo_barras_fisico or ""
            )

            if not any(
                termo in valor.casefold()
                for valor in valores_pesquisa
            ):
                continue

        itens.append({
            "produto": produto,
            "status": divergencia.status,
            "divergencia": divergencia,
            "ultima_divergencia": divergencia
        })

    return render_template(
        "divergencia/listar.html",
        itens=itens,
        filtro=filtro,
        pesquisa=pesquisa,
        totais=totais,
        historico=filtro in (
            "HISTORICO",
            "CORRIGIDO",
            "DESCARTADO"
        )
    )


@divergencia_bp.route("/buscar-produtos")
def buscar_produtos():

    termo = request.args.get("q", "").strip()

    if len(termo) < 2:
        return jsonify([])

    padrao = f"%{termo}%"

    produtos = (
        Produto.query
        .filter(
            Produto.enderecos.any(),
            or_(
                cast(Produto.codigo, String).ilike(padrao),
                Produto.descricao.ilike(padrao),
                Produto.codigo_barras.ilike(padrao)
            )
        )
        .order_by(Produto.descricao, Produto.codigo)
        .limit(20)
        .all()
    )

    produtos_ids = [produto.id for produto in produtos]

    pendentes = (
        DivergenciaCodigoBarras.query
        .filter(
            DivergenciaCodigoBarras.produto_id.in_(produtos_ids),
            DivergenciaCodigoBarras.status == "PENDENTE"
        )
        .order_by(
            DivergenciaCodigoBarras.data_registro.desc(),
            DivergenciaCodigoBarras.id.desc()
        )
        .all()
    )

    pendente_por_produto = {}

    for divergencia in pendentes:
        pendente_por_produto.setdefault(
            divergencia.produto_id,
            divergencia.id
        )

    return jsonify([
        {
            "id": produto.id,
            "codigo": produto.codigo,
            "descricao": produto.descricao,
            "codigo_barras": produto.codigo_barras or "",
            "divergencia_pendente_id": pendente_por_produto.get(produto.id)
        }
        for produto in produtos
    ])


@divergencia_bp.route(
    "/<int:id>"
)
def detalhes(id):

    divergencia = (
        DivergenciaCodigoBarras.query
        .get_or_404(id)
    )

    endereco = (
        ProdutoEndereco.query
        .filter_by(
            produto_id=divergencia.produto_id
        )
        .order_by(
            ProdutoEndereco.id.desc()
        )
        .first()
    )

    return render_template(
        "divergencia/detalhes.html",
        divergencia=divergencia,
        endereco=endereco
    )


@divergencia_bp.route(
    "/registrar/<int:produto_id>",
    methods=["GET", "POST"]
)
def registrar(produto_id):

    produto = Produto.query.get_or_404(
        produto_id
    )

    produto_enderecado = (
        ProdutoEndereco.query
        .filter_by(
            produto_id=produto.id
        )
        .first()
    )

    if not produto_enderecado:

        flash(
            (
                "Este produto ainda não está endereçado "
                "e não pode ter o código de barras "
                "validado por esta rotina."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "divergencia.listar"
            )
        )

    divergencia_pendente = (
        DivergenciaCodigoBarras.query
        .filter_by(
            produto_id=produto.id,
            status="PENDENTE"
        )
        .order_by(
            DivergenciaCodigoBarras.data_registro.desc()
        )
        .first()
    )

    if request.method == "POST":

        codigo_barras_fisico = (
            request.form.get(
                "codigo_barras_fisico",
                ""
            )
            .strip()
        )

        observacao = (
            request.form.get(
                "observacao",
                ""
            )
            .strip()
        )

        if not codigo_barras_fisico:

            flash(
                (
                    "Informe o código de barras "
                    "encontrado no produto físico."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "divergencia.registrar",
                    produto_id=produto.id
                )
            )

        if (
            produto.codigo_barras
            and codigo_barras_fisico
            == produto.codigo_barras
        ):

            flash(
                (
                    "O código informado é igual ao "
                    "código cadastrado atualmente "
                    "no SIGE."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "divergencia.registrar",
                    produto_id=produto.id
                )
            )

        if divergencia_pendente:

            flash(
                (
                    "Este produto já possui uma "
                    "divergência de código de barras "
                    "pendente."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "divergencia.listar",
                    status="PENDENTE"
                )
            )

        divergencia = DivergenciaCodigoBarras(
            produto_id=produto.id,
            codigo_barras_cadastrado=produto.codigo_barras,
            codigo_barras_fisico=codigo_barras_fisico,
            observacao=observacao or None,
            status="PENDENTE",
            usuario_id=session.get(
                "usuario_id"
            )
        )

        db.session.add(
            divergencia
        )

        db.session.commit()

        flash(
            (
                "Divergência de código de barras registrada. "
                "Ela permanecerá pendente até que o novo código "
                "seja recebido novamente através da importação "
                "do WinThor."
            ),
            "success"
        )

        return redirect(
            url_for(
                "divergencia.listar",
                status="PENDENTE"
            )
        )

    return render_template(
        "divergencia/form.html",
        produto=produto,
        divergencia_pendente=divergencia_pendente
    )


@divergencia_bp.route(
    "/<int:id>/descartar",
    methods=["POST"]
)
def descartar(id):

    divergencia = (
        DivergenciaCodigoBarras.query
        .get_or_404(id)
    )

    if divergencia.status != "PENDENTE":

        flash(
            (
                "Somente divergências pendentes "
                "podem ser descartadas."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "divergencia.listar"
            )
        )

    divergencia.status = "DESCARTADO"

    db.session.commit()

    flash(
        "Divergência descartada.",
        "warning"
    )

    return redirect(
        url_for(
            "divergencia.listar",
            status="DESCARTADO"
        )
    )


@divergencia_bp.route(
    "/<int:id>/reabrir",
    methods=["POST"]
)
def reabrir(id):

    divergencia = (
        DivergenciaCodigoBarras.query
        .get_or_404(id)
    )

    if divergencia.status != "DESCARTADO":

        flash(
            (
                "Somente divergências descartadas "
                "podem ser reabertas."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "divergencia.listar"
            )
        )

    outra_pendente = (
        DivergenciaCodigoBarras.query
        .filter(
            DivergenciaCodigoBarras.produto_id
            == divergencia.produto_id,
            DivergenciaCodigoBarras.status
            == "PENDENTE",
            DivergenciaCodigoBarras.id
            != divergencia.id
        )
        .first()
    )

    if outra_pendente:

        flash(
            (
                "Este produto já possui outra "
                "divergência pendente."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "divergencia.listar"
            )
        )

    divergencia.status = "PENDENTE"

    db.session.commit()

    flash(
        "Divergência reaberta.",
        "success"
    )

    return redirect(
        url_for(
            "divergencia.listar",
            status="PENDENTE"
        )
    )
