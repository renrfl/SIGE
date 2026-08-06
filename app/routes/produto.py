import csv
import io

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Produto, ProdutoEndereco


produto_bp = Blueprint(
    "produto",
    __name__,
    url_prefix="/produtos"
)


def converter_status(valor):

    if valor is None or not valor.strip():
        return True

    valor = valor.strip().lower()

    valores_ativos = (
        "1",
        "sim",
        "s",
        "true",
        "ativo",
        "a"
    )

    valores_inativos = (
        "0",
        "nao",
        "não",
        "n",
        "false",
        "inativo",
        "i"
    )

    if valor in valores_ativos:
        return True

    if valor in valores_inativos:
        return False

    raise ValueError("Status inválido")


def ler_arquivo_csv(arquivo):

    conteudo = arquivo.read()

    if not conteudo:
        raise ValueError("O arquivo CSV está vazio.")

    try:
        texto = conteudo.decode("utf-8-sig")

    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")

    amostra = texto[:4096]

    try:
        delimitador = csv.Sniffer().sniff(
            amostra,
            delimiters=",;"
        ).delimiter

    except csv.Error:
        delimitador = ";"

    leitor = csv.DictReader(
        io.StringIO(texto),
        delimiter=delimitador
    )

    if not leitor.fieldnames:
        raise ValueError("O arquivo CSV não possui cabeçalho.")

    leitor.fieldnames = [
        campo.strip().lower()
        for campo in leitor.fieldnames
    ]

    campos_obrigatorios = {
        "codigo",
        "codigo_barras",
        "descricao"
    }

    campos_ausentes = campos_obrigatorios.difference(
        leitor.fieldnames
    )

    if campos_ausentes:

        nomes = ", ".join(
            sorted(campos_ausentes)
        )

        raise ValueError(
            f"Colunas obrigatórias ausentes: {nomes}."
        )

    return list(leitor)


@produto_bp.route("/")
def listar():

    resultados = (
        db.session.query(
            Produto,
            func.count(
                ProdutoEndereco.id
            ).label("total_enderecos")
        )
        .outerjoin(
            ProdutoEndereco,
            ProdutoEndereco.produto_id == Produto.id
        )
        .group_by(Produto.id)
        .order_by(Produto.descricao)
        .all()
    )

    produtos = []

    for produto, total_enderecos in resultados:

        produto.enderecado = total_enderecos > 0
        produto.total_enderecos = total_enderecos

        produtos.append(produto)

    return render_template(
        "produto/listar.html",
        produtos=produtos
    )


@produto_bp.route("/novo", methods=["GET", "POST"])
def novo():

    if request.method == "POST":

        codigo = request.form["codigo"].strip()
        codigo_barras = request.form["codigo_barras"].strip()
        descricao = request.form["descricao"].strip()

        if not codigo:

            flash(
                "Informe o código do produto.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        if not codigo.isdigit():

            flash(
                "O código do produto deve conter somente números.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        if not codigo_barras:

            flash(
                "Informe o código de barras do produto.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        if not descricao:

            flash(
                "Informe a descrição do produto.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        produto_existente = Produto.query.filter(
            db.or_(
                Produto.codigo == int(codigo),
                Produto.codigo_barras == codigo_barras
            )
        ).first()

        if produto_existente:

            flash(
                "Já existe um produto com esse código ou código de barras.",
                "warning"
            )

            return redirect(
                url_for("produto.novo")
            )

        produto = Produto(
            codigo=int(codigo),
            codigo_barras=codigo_barras,
            descricao=descricao
        )

        try:

            db.session.add(produto)
            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "Não foi possível cadastrar o produto. Verifique os dados informados.",
                "danger"
            )

            return redirect(
                url_for("produto.novo")
            )

        flash(
            "Produto cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("produto.listar")
        )

    return render_template(
        "produto/form.html",
        produto=None
    )


@produto_bp.route("/importar", methods=["GET", "POST"])
def importar():

    if request.method == "POST":

        arquivo = request.files.get("arquivo")

        if not arquivo or not arquivo.filename:

            flash(
                "Selecione um arquivo CSV.",
                "danger"
            )

            return redirect(
                url_for("produto.importar")
            )

        if not arquivo.filename.lower().endswith(".csv"):

            flash(
                "O arquivo selecionado deve possuir a extensão .csv.",
                "danger"
            )

            return redirect(
                url_for("produto.importar")
            )

        try:
            linhas = ler_arquivo_csv(arquivo)

        except ValueError as erro:

            flash(
                str(erro),
                "danger"
            )

            return redirect(
                url_for("produto.importar")
            )

        produtos_existentes = Produto.query.all()

        produtos_por_codigo = {
            produto.codigo: produto
            for produto in produtos_existentes
        }

        produtos_por_codigo_barras = {
            produto.codigo_barras: produto
            for produto in produtos_existentes
            if produto.codigo_barras
        }

        codigos_csv = set()
        codigos_barras_csv = set()

        novos = 0
        atualizados = 0
        ignorados = 0
        erros = []

        for numero_linha, linha in enumerate(
            linhas,
            start=2
        ):

            codigo = (linha.get("codigo") or "").strip()
            codigo_barras = (
                linha.get("codigo_barras") or ""
            ).strip()
            descricao = (
                linha.get("descricao") or ""
            ).strip()
            status = linha.get("ativo")

            if not codigo or not codigo.isdigit():

                erros.append(
                    f"Linha {numero_linha}: código inválido."
                )

                continue

            if not descricao:

                erros.append(
                    f"Linha {numero_linha}: descrição não informada."
                )

                continue

            codigo = int(codigo)

            try:
                ativo = converter_status(status)

            except ValueError:

                erros.append(
                    f"Linha {numero_linha}: status ativo inválido."
                )

                continue

            if codigo in codigos_csv:

                erros.append(
                    f"Linha {numero_linha}: código {codigo} repetido no CSV."
                )

                continue

            if (
                codigo_barras
                and codigo_barras in codigos_barras_csv
            ):

                erros.append(
                    f"Linha {numero_linha}: código de barras {codigo_barras} repetido no CSV."
                )

                continue

            codigos_csv.add(codigo)

            if codigo_barras:
                codigos_barras_csv.add(codigo_barras)

            produto = produtos_por_codigo.get(codigo)

            produto_do_codigo_barras = None

            if codigo_barras:

                produto_do_codigo_barras = (
                    produtos_por_codigo_barras.get(
                        codigo_barras
                    )
                )

            if (
                produto_do_codigo_barras
                and produto_do_codigo_barras is not produto
            ):

                erros.append(
                    f"Linha {numero_linha}: o código de barras {codigo_barras} pertence a outro produto."
                )

                continue

            if produto:

                houve_alteracao = False

                novo_codigo_barras = (
                    codigo_barras
                    if codigo_barras
                    else None
                )

                if produto.codigo_barras != novo_codigo_barras:

                    if produto.codigo_barras:

                        produtos_por_codigo_barras.pop(
                            produto.codigo_barras,
                            None
                        )

                    produto.codigo_barras = novo_codigo_barras

                    if novo_codigo_barras:

                        produtos_por_codigo_barras[
                            novo_codigo_barras
                        ] = produto

                    houve_alteracao = True

                if produto.descricao != descricao:
                    produto.descricao = descricao
                    houve_alteracao = True

                if produto.ativo != ativo:
                    produto.ativo = ativo
                    houve_alteracao = True

                if houve_alteracao:
                    atualizados += 1

                else:
                    ignorados += 1

                continue

            produto = Produto(
                codigo=codigo,
                codigo_barras=(
                    codigo_barras
                    if codigo_barras
                    else None
                ),
                descricao=descricao,
                ativo=ativo
            )

            db.session.add(produto)

            produtos_por_codigo[codigo] = produto
            if codigo_barras:

                produtos_por_codigo_barras[
                    codigo_barras
                ] = produto

            novos += 1

        if erros:

            db.session.rollback()

            mensagem = " ".join(erros[:5])

            if len(erros) > 5:
                mensagem += (
                    f" Existem mais {len(erros) - 5} erro(s)."
                )

            flash(
                "Importação cancelada. " + mensagem,
                "danger"
            )

            return redirect(
                url_for("produto.importar")
            )

        try:
            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "A importação não foi concluída devido a um conflito entre códigos ou códigos de barras.",
                "danger"
            )

            return redirect(
                url_for("produto.importar")
            )

        flash(
            (
                "Importação concluída: "
                f"{novos} novo(s), "
                f"{atualizados} atualizado(s) e "
                f"{ignorados} sem alteração."
            ),
            "success"
        )

        return redirect(
            url_for("produto.listar")
        )

    return render_template(
        "produto/importar.html"
    )


@produto_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    produto = Produto.query.get_or_404(id)

    if request.method == "POST":

        codigo = request.form["codigo"].strip()
        codigo_barras = request.form["codigo_barras"].strip()
        descricao = request.form["descricao"].strip()

        if not codigo:

            flash(
                "Informe o código do produto.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        if not codigo.isdigit():

            flash(
                "O código do produto deve conter somente números.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        if not codigo_barras:

            flash(
                "Informe o código de barras do produto.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        if not descricao:

            flash(
                "Informe a descrição do produto.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        produto_existente = Produto.query.filter(
            db.or_(
                Produto.codigo == int(codigo),
                Produto.codigo_barras == codigo_barras
            ),
            Produto.id != produto.id
        ).first()

        if produto_existente:

            flash(
                "Já existe outro produto com esse código ou código de barras.",
                "warning"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        produto.codigo = int(codigo)
        produto.codigo_barras = codigo_barras
        produto.descricao = descricao

        try:

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "Não foi possível atualizar o produto. Verifique os dados informados.",
                "danger"
            )

            return redirect(
                url_for(
                    "produto.editar",
                    id=produto.id
                )
            )

        flash(
            "Produto atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("produto.listar")
        )

    return render_template(
        "produto/form.html",
        produto=produto
    )


@produto_bp.route("/excluir/<int:id>")
def excluir(id):

    produto = Produto.query.get_or_404(id)

    try:

        db.session.delete(produto)
        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        flash(
            "Não foi possível remover o produto.",
            "danger"
        )

        return redirect(
            url_for("produto.listar")
        )

    flash(
        "Produto removido com sucesso.",
        "success"
    )

    return redirect(
        url_for("produto.listar")
    )