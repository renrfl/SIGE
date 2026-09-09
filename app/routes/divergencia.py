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
    DivergenciaCodigoBarras,
    Produto,
    ProdutoEndereco
)


divergencia_bp = Blueprint(
    "divergencia",
    __name__
)


def calcular_status_produto(
    produto_id,
    divergencias_pendentes
):

    if produto_id in divergencias_pendentes:
        return "PENDENTE"

    return "CORRETO"


@divergencia_bp.route("/")
def listar():

    filtro = request.args.get(
        "status",
        ""
    ).strip().upper()

    pesquisa = request.args.get(
        "q",
        ""
    ).strip()

    produtos_enderecados_ids = {
        resultado[0]
        for resultado in (
            db.session.query(
                ProdutoEndereco.produto_id
            )
            .distinct()
            .all()
        )
    }

    produtos = (
        Produto.query
        .filter(
            Produto.id.in_(
                produtos_enderecados_ids
            )
        )
        .order_by(
            Produto.descricao
        )
        .all()
    )

    divergencias = (
        DivergenciaCodigoBarras.query
        .order_by(
            DivergenciaCodigoBarras.data_registro.desc()
        )
        .all()
    )

    divergencias_pendentes = set()

    ultima_divergencia_por_produto = {}

    produtos_com_divergencia = set()

    produtos_corrigidos = set()

    produtos_descartados = set()

    for divergencia in divergencias:

        produtos_com_divergencia.add(
            divergencia.produto_id
        )

        if (
            divergencia.produto_id
            not in ultima_divergencia_por_produto
        ):

            ultima_divergencia_por_produto[
                divergencia.produto_id
            ] = divergencia

        if divergencia.status == "PENDENTE":

            divergencias_pendentes.add(
                divergencia.produto_id
            )

        elif divergencia.status == "CORRIGIDO":

            produtos_corrigidos.add(
                divergencia.produto_id
            )

        elif divergencia.status == "DESCARTADO":

            produtos_descartados.add(
                divergencia.produto_id
            )

    itens = []

    for produto in produtos:

        status = calcular_status_produto(
            produto.id,
            divergencias_pendentes
        )

        ultima_divergencia = (
            ultima_divergencia_por_produto.get(
                produto.id
            )
        )

        if filtro == "CORRETO":

            if status != "CORRETO":
                continue

        elif filtro == "PENDENTE":

            if status != "PENDENTE":
                continue

        elif filtro == "DIVERGENCIA":

            if (
                produto.id
                not in produtos_com_divergencia
            ):
                continue

        elif filtro == "CORRIGIDO":

            if (
                produto.id
                not in produtos_corrigidos
            ):
                continue

        elif filtro == "DESCARTADO":

            if (
                produto.id
                not in produtos_descartados
            ):
                continue

        if pesquisa:

            termo = pesquisa.lower()

            valores_pesquisa = [
                str(produto.codigo),
                produto.descricao or "",
                produto.codigo_barras or ""
            ]

            if ultima_divergencia:

                valores_pesquisa.append(
                    ultima_divergencia.codigo_barras_fisico
                    or ""
                )

                valores_pesquisa.append(
                    ultima_divergencia.codigo_barras_cadastrado
                    or ""
                )

            encontrado = any(
                termo in str(valor).lower()
                for valor in valores_pesquisa
            )

            if not encontrado:
                continue

        itens.append({
            "produto": produto,
            "status": status,
            "enderecado": True,
            "ultima_divergencia": ultima_divergencia
        })

    totais = {
        "TODOS": len(produtos),
        "CORRETO": 0,
        "PENDENTE": 0,
        "DIVERGENCIA": 0,
        "CORRIGIDO": 0,
        "DESCARTADO": 0
    }

    for produto in produtos:

        status = calcular_status_produto(
            produto.id,
            divergencias_pendentes
        )

        totais[status] += 1

        if (
            produto.id
            in produtos_com_divergencia
        ):

            totais[
                "DIVERGENCIA"
            ] += 1

        if (
            produto.id
            in produtos_corrigidos
        ):

            totais[
                "CORRIGIDO"
            ] += 1

        if (
            produto.id
            in produtos_descartados
        ):

            totais[
                "DESCARTADO"
            ] += 1

    return render_template(
        "divergencia/listar.html",
        itens=itens,
        filtro=filtro,
        pesquisa=pesquisa,
        totais=totais
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