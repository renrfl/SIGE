from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Posicao, Produto, ProdutoEndereco


endereco_bp = Blueprint(
    "endereco",
    __name__,
    url_prefix="/enderecos"
)


def preparar_opcoes_formulario():

    produtos = Produto.query.filter_by(
        ativo=True
    ).order_by(
        Produto.descricao
    ).all()

    posicoes = Posicao.query.filter_by(
        ativo=True
    ).order_by(
        Posicao.nome
    ).all()

    enderecos = ProdutoEndereco.query.all()

    quantidade_enderecos_por_produto = {}

    ocupacao_por_posicao = {}

    for endereco in enderecos:

        quantidade_enderecos_por_produto[
            endereco.produto_id
        ] = (
            quantidade_enderecos_por_produto.get(
                endereco.produto_id,
                0
            )
            + 1
        )

        if endereco.posicao_id not in ocupacao_por_posicao:

            ocupacao_por_posicao[
                endereco.posicao_id
            ] = endereco

    for produto in produtos:

        produto.total_enderecos = (
            quantidade_enderecos_por_produto.get(
                produto.id,
                0
            )
        )

        produto.enderecado = (
            produto.total_enderecos > 0
        )

    for posicao in posicoes:

        ocupacao = ocupacao_por_posicao.get(
            posicao.id
        )

        posicao.ocupada = (
            ocupacao is not None
        )

        posicao.produto_ocupante = (
            ocupacao.produto
            if ocupacao
            else None
        )

    return produtos, posicoes


def buscar_ocupacao_posicao(
    posicao_id,
    produto_id,
    endereco_id=None
):

    consulta = ProdutoEndereco.query.filter(
        ProdutoEndereco.posicao_id == posicao_id,
        ProdutoEndereco.produto_id != produto_id
    )

    if endereco_id is not None:

        consulta = consulta.filter(
            ProdutoEndereco.id != endereco_id
        )

    return consulta.first()


def substituir_ocupacao_posicao(
    ocupacao,
    produto_id
):

    produto_anterior = ocupacao.produto

    db.session.delete(
        ocupacao
    )

    novo_endereco = ProdutoEndereco(
        produto_id=produto_id,
        posicao_id=ocupacao.posicao_id
    )

    db.session.add(
        novo_endereco
    )

    db.session.commit()

    return produto_anterior


@endereco_bp.route("/")
def listar():

    enderecos = ProdutoEndereco.query.order_by(
        ProdutoEndereco.data_cadastro.desc()
    ).all()

    return render_template(
        "endereco/listar.html",
        enderecos=enderecos
    )


@endereco_bp.route("/novo", methods=["GET", "POST"])
def novo():

    produtos, posicoes = preparar_opcoes_formulario()

    if request.method == "POST":

        produto_id = request.form.get(
            "produto_id",
            type=int
        )

        posicao_id = request.form.get(
            "posicao_id",
            type=int
        )

        confirmar_substituicao = (
            request.form.get(
                "confirmar_substituicao"
            )
            == "sim"
        )

        if not produto_id or not posicao_id:

            flash(
                "Selecione o produto e a posição.",
                "danger"
            )

            return render_template(
                "endereco/form.html",
                endereco=None,
                produtos=produtos,
                posicoes=posicoes,
                produto_id_selecionado=produto_id,
                posicao_id_selecionada=posicao_id,
                conflito=None
            )

        produto = Produto.query.filter_by(
            id=produto_id,
            ativo=True
        ).first_or_404()

        posicao = Posicao.query.filter_by(
            id=posicao_id,
            ativo=True
        ).first_or_404()

        endereco_existente = ProdutoEndereco.query.filter_by(
            produto_id=produto_id,
            posicao_id=posicao_id
        ).first()

        if endereco_existente:

            flash(
                "Este produto já está vinculado a essa posição.",
                "warning"
            )

            return redirect(
                url_for("endereco.novo")
            )

        ocupacao = buscar_ocupacao_posicao(
            posicao_id=posicao_id,
            produto_id=produto_id
        )

        if ocupacao and not confirmar_substituicao:

            return render_template(
                "endereco/form.html",
                endereco=None,
                produtos=produtos,
                posicoes=posicoes,
                produto_id_selecionado=produto_id,
                posicao_id_selecionada=posicao_id,
                conflito={
                    "produto_novo": produto,
                    "produto_atual": ocupacao.produto,
                    "posicao": posicao
                }
            )

        if ocupacao and confirmar_substituicao:

            produto_anterior = substituir_ocupacao_posicao(
                ocupacao=ocupacao,
                produto_id=produto_id
            )

            flash(
                (
                    "Posição atualizada com sucesso. "
                    f"O produto {produto_anterior.codigo} - "
                    f"{produto_anterior.descricao} foi removido da posição "
                    f"e substituído por {produto.codigo} - "
                    f"{produto.descricao}."
                ),
                "success"
            )

            return redirect(
                url_for("endereco.listar")
            )

        endereco = ProdutoEndereco(
            produto_id=produto_id,
            posicao_id=posicao_id
        )

        db.session.add(
            endereco
        )

        db.session.commit()

        flash(
            "Produto endereçado com sucesso.",
            "success"
        )

        return redirect(
            url_for("endereco.listar")
        )

    return render_template(
        "endereco/form.html",
        endereco=None,
        produtos=produtos,
        posicoes=posicoes,
        produto_id_selecionado=None,
        posicao_id_selecionada=None,
        conflito=None
    )


@endereco_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    endereco = ProdutoEndereco.query.get_or_404(
        id
    )

    produtos, posicoes = preparar_opcoes_formulario()

    if (
        endereco.produto
        and endereco.produto not in produtos
    ):

        endereco.produto.total_enderecos = len(
            endereco.produto.enderecos
        )

        endereco.produto.enderecado = True

        produtos.append(
            endereco.produto
        )

        produtos.sort(
            key=lambda produto: produto.descricao.lower()
        )

    if (
        endereco.posicao
        and endereco.posicao not in posicoes
    ):

        endereco.posicao.ocupada = True
        endereco.posicao.produto_ocupante = endereco.produto

        posicoes.append(
            endereco.posicao
        )

        posicoes.sort(
            key=lambda posicao: posicao.nome.lower()
        )

    if request.method == "POST":

        produto_id = request.form.get(
            "produto_id",
            type=int
        )

        posicao_id = request.form.get(
            "posicao_id",
            type=int
        )

        confirmar_substituicao = (
            request.form.get(
                "confirmar_substituicao"
            )
            == "sim"
        )

        if not produto_id or not posicao_id:

            flash(
                "Selecione o produto e a posição.",
                "danger"
            )

            return render_template(
                "endereco/form.html",
                endereco=endereco,
                produtos=produtos,
                posicoes=posicoes,
                produto_id_selecionado=produto_id,
                posicao_id_selecionada=posicao_id,
                conflito=None
            )

        produto = Produto.query.get_or_404(
            produto_id
        )

        posicao = Posicao.query.get_or_404(
            posicao_id
        )

        if (
            not produto.ativo
            and produto.id != endereco.produto_id
        ):

            flash(
                "Não é permitido selecionar um produto inativo.",
                "danger"
            )

            return redirect(
                url_for(
                    "endereco.editar",
                    id=endereco.id
                )
            )

        if (
            not posicao.ativo
            and posicao.id != endereco.posicao_id
        ):

            flash(
                "Não é permitido selecionar uma posição inativa.",
                "danger"
            )

            return redirect(
                url_for(
                    "endereco.editar",
                    id=endereco.id
                )
            )

        endereco_existente = ProdutoEndereco.query.filter(
            ProdutoEndereco.produto_id == produto_id,
            ProdutoEndereco.posicao_id == posicao_id,
            ProdutoEndereco.id != endereco.id
        ).first()

        if endereco_existente:

            flash(
                "Este produto já está vinculado a essa posição.",
                "warning"
            )

            return redirect(
                url_for(
                    "endereco.editar",
                    id=endereco.id
                )
            )

        ocupacao = buscar_ocupacao_posicao(
            posicao_id=posicao_id,
            produto_id=produto_id,
            endereco_id=endereco.id
        )

        if ocupacao and not confirmar_substituicao:

            return render_template(
                "endereco/form.html",
                endereco=endereco,
                produtos=produtos,
                posicoes=posicoes,
                produto_id_selecionado=produto_id,
                posicao_id_selecionada=posicao_id,
                conflito={
                    "produto_novo": produto,
                    "produto_atual": ocupacao.produto,
                    "posicao": posicao
                }
            )

        if ocupacao and confirmar_substituicao:

            produto_anterior = ocupacao.produto

            db.session.delete(
                ocupacao
            )

            endereco.produto_id = produto_id
            endereco.posicao_id = posicao_id

            db.session.commit()

            flash(
                (
                    "Endereço atualizado com sucesso. "
                    f"O produto {produto_anterior.codigo} - "
                    f"{produto_anterior.descricao} foi removido da posição."
                ),
                "success"
            )

            return redirect(
                url_for("endereco.listar")
            )

        endereco.produto_id = produto_id
        endereco.posicao_id = posicao_id

        db.session.commit()

        flash(
            "Endereço atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("endereco.listar")
        )

    return render_template(
        "endereco/form.html",
        endereco=endereco,
        produtos=produtos,
        posicoes=posicoes,
        produto_id_selecionado=endereco.produto_id,
        posicao_id_selecionada=endereco.posicao_id,
        conflito=None
    )


@endereco_bp.route("/excluir/<int:id>")
def excluir(id):

    endereco = ProdutoEndereco.query.get_or_404(
        id
    )

    db.session.delete(
        endereco
    )

    db.session.commit()

    flash(
        "Endereço removido com sucesso.",
        "success"
    )

    return redirect(
        url_for("endereco.listar")
    )