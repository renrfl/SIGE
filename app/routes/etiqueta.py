import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models import Produto, ProdutoEndereco


etiqueta_bp = Blueprint(
    "etiqueta",
    __name__,
    url_prefix="/etiquetas"
)


def obter_indicador(endereco):

    nivel_nome = (
        endereco.posicao.nivel.nome
        .strip()
        .lower()
    )

    if nivel_nome in (
        "1",
        "nivel 1",
        "nível 1",
        "terreo",
        "térreo"
    ):

        return "baixo"

    if nivel_nome in (
        "2",
        "nivel 2",
        "nível 2",
        "superior"
    ):

        return "cima"

    return "deposito"


def montar_etiqueta(produto):

    endereco = ProdutoEndereco.query.filter_by(
        produto_id=produto.id
    ).first()

    if not endereco:

        return None

    return {
        "produto": produto,
        "endereco": endereco,
        "indicador": obter_indicador(endereco)
    }


@etiqueta_bp.route("/", methods=["GET", "POST"])
def pesquisar():

    if request.method == "POST":

        texto_codigos = (
            request.form.get("codigos")
            or request.form.get("codigo")
            or ""
        ).strip()

        if not texto_codigos:

            flash(
                "Informe pelo menos um código interno.",
                "danger"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        codigos_informados = [
            codigo
            for codigo in re.split(
                r"[\s,;]+",
                texto_codigos
            )
            if codigo
        ]

        codigos_unicos = []
        codigos_vistos = set()

        for codigo in codigos_informados:

            if not codigo.isdigit():

                flash(
                    f"O código '{codigo}' é inválido. "
                    "Informe somente códigos numéricos.",
                    "danger"
                )

                return redirect(
                    url_for("etiqueta.pesquisar")
                )

            codigo_numero = int(codigo)

            if codigo_numero not in codigos_vistos:

                codigos_vistos.add(
                    codigo_numero
                )

                codigos_unicos.append(
                    codigo_numero
                )

        produtos = Produto.query.filter(
            Produto.codigo.in_(
                codigos_unicos
            )
        ).all()

        produtos_por_codigo = {
            produto.codigo: produto
            for produto in produtos
        }

        codigos_nao_encontrados = [
            str(codigo)
            for codigo in codigos_unicos
            if codigo not in produtos_por_codigo
        ]

        if codigos_nao_encontrados:

            flash(
                "Produtos não encontrados: "
                + ", ".join(codigos_nao_encontrados),
                "warning"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        produtos_sem_endereco = []

        produtos_ordenados = []

        for codigo in codigos_unicos:

            produto = produtos_por_codigo[
                codigo
            ]

            endereco = ProdutoEndereco.query.filter_by(
                produto_id=produto.id
            ).first()

            if not endereco:

                produtos_sem_endereco.append(
                    str(produto.codigo)
                )

                continue

            produtos_ordenados.append(
                produto
            )

        if produtos_sem_endereco:

            flash(
                "Produtos sem endereço cadastrado: "
                + ", ".join(produtos_sem_endereco),
                "warning"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        if len(produtos_ordenados) == 1:

            return redirect(
                url_for(
                    "etiqueta.imprimir",
                    produto_id=produtos_ordenados[0].id
                )
            )

        ids = ",".join(
            str(produto.id)
            for produto in produtos_ordenados
        )

        return redirect(
            url_for(
                "etiqueta.imprimir_lote",
                ids=ids
            )
        )

    return render_template(
        "etiqueta/pesquisar.html"
    )


@etiqueta_bp.route("/imprimir/<int:produto_id>")
def imprimir(produto_id):

    produto = Produto.query.get_or_404(
        produto_id
    )

    etiqueta = montar_etiqueta(
        produto
    )

    if not etiqueta:

        flash(
            "Este produto ainda não possui endereço cadastrado.",
            "warning"
        )

        return redirect(
            url_for("etiqueta.pesquisar")
        )

    return render_template(
        "etiqueta/imprimir.html",
        produto=etiqueta["produto"],
        endereco=etiqueta["endereco"],
        indicador=etiqueta["indicador"]
    )


@etiqueta_bp.route("/imprimir-lote")
def imprimir_lote():

    texto_ids = request.args.get(
        "ids",
        ""
    ).strip()

    if not texto_ids:

        flash(
            "Nenhum produto foi selecionado para impressão.",
            "warning"
        )

        return redirect(
            url_for("etiqueta.pesquisar")
        )

    ids = []

    for valor in texto_ids.split(","):

        valor = valor.strip()

        if not valor.isdigit():

            flash(
                "A seleção de produtos para impressão é inválida.",
                "danger"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        produto_id = int(valor)

        if produto_id not in ids:

            ids.append(
                produto_id
            )

    produtos = Produto.query.filter(
        Produto.id.in_(ids)
    ).all()

    produtos_por_id = {
        produto.id: produto
        for produto in produtos
    }

    etiquetas = []

    for produto_id in ids:

        produto = produtos_por_id.get(
            produto_id
        )

        if not produto:

            flash(
                "Um dos produtos selecionados não foi encontrado.",
                "warning"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        etiqueta = montar_etiqueta(
            produto
        )

        if not etiqueta:

            flash(
                f"O produto {produto.codigo} não possui endereço cadastrado.",
                "warning"
            )

            return redirect(
                url_for("etiqueta.pesquisar")
            )

        etiquetas.append(
            etiqueta
        )

    return render_template(
        "etiqueta/imprimir.html",
        etiquetas=etiquetas
    )