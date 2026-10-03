import re
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import joinedload
from app import db
from app.models import Modulo, Nivel, Posicao, Predio, Produto, ProdutoEndereco, Rua
endereco_bp = Blueprint(
    "endereco",
    __name__,
    url_prefix="/enderecos"
)
def formatar_endereco_posicao(posicao):
    rua = posicao.nivel.modulo.predio.rua.nome
    predio = posicao.nivel.modulo.predio.nome
    modulo = posicao.nivel.modulo.nome
    nivel = posicao.nivel.nome
    posicao_nome = posicao.nome
    nomes_estrutura = [
        rua.strip().upper(),
        predio.strip().upper(),
        modulo.strip().upper(),
        nivel.strip().upper()
    ]
    if all(nome == "AVARIA" for nome in nomes_estrutura):
        return f"AVARIA → {posicao_nome}"
    if all(nome == "DEPOSITO" for nome in nomes_estrutura):
        return f"DEPOSITO → {posicao_nome}"
    return (
        f"{rua}"
        f" → {predio}"
        f" → {modulo}"
        f" → {nivel}"
        f" → {posicao_nome}"
    )

def formatar_endereco_operacional(posicao):
    rua = posicao.nivel.modulo.predio.rua.nome
    predio = posicao.nivel.modulo.predio.nome
    modulo = posicao.nivel.modulo.nome
    posicao_nome = posicao.nome

    if (
        rua.strip().upper() == "AVARIA"
        and predio.strip().upper() == "AVARIA"
        and modulo.strip().upper() == "AVARIA"
    ):
        return f"AVARIA → {posicao_nome}"

    if (
        rua.strip().upper() == "DEPOSITO"
        and predio.strip().upper() == "DEPOSITO"
        and modulo.strip().upper() == "DEPOSITO"
    ):
        return f"DEPOSITO → {posicao_nome}"

    return (
        f"{rua}"
        f" → {predio}"
        f" → {modulo}"
        f" → {posicao_nome}"
    )

def normalizar_texto(texto):
    texto = texto.upper()
    texto = re.sub(
        r"[^A-Z0-9]+",
        " ",
        texto
    )
    texto = re.sub(
        r"\s+",
        " ",
        texto
    )
    return texto.strip()
def normalizar_atalho(texto):
    texto = texto.upper()
    texto = re.sub(
        r"[^A-Z0-9]",
        "",
        texto
    )
    return texto
def extrair_numero_nome(nome, prefixo):
    nome_normalizado = normalizar_texto(
        nome
    )
    padrao = (
        rf"^{re.escape(prefixo)}\s+(\d+)$"
    )
    resultado = re.match(
        padrao,
        nome_normalizado
    )
    if not resultado:
        return None
    return resultado.group(1)
def gerar_atalho_posicao(posicao):
    rua = posicao.nivel.modulo.predio.rua.nome
    predio = posicao.nivel.modulo.predio.nome
    modulo = posicao.nivel.modulo.nome
    nivel = posicao.nivel.nome
    posicao_nome = posicao.nome
    numero_rua = extrair_numero_nome(
        rua,
        "RUA"
    )
    numero_deposito = extrair_numero_nome(
        rua,
        "DEPOSITO"
    )
    numero_predio = extrair_numero_nome(
        predio,
        "PREDIO"
    )
    numero_modulo = extrair_numero_nome(
        modulo,
        "MODULO"
    )
    numero_nivel = extrair_numero_nome(
        nivel,
        "NIVEL"
    )
    numero_posicao = extrair_numero_nome(
        posicao_nome,
        "POSICAO"
    )
    if numero_rua:
        inicio = f"R{numero_rua}"
    elif numero_deposito:
        inicio = f"D{numero_deposito}"
    else:
        return None
    partes = [
        inicio
    ]
    if numero_predio:
        partes.append(
            f"PR{numero_predio}"
        )
    if numero_modulo:
        partes.append(
            f"M{numero_modulo}"
        )
    if numero_nivel:
        partes.append(
            f"N{numero_nivel}"
        )
    if numero_posicao:
        partes.append(
            f"PS{numero_posicao}"
        )
    return "".join(partes)
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
            ocupacao_por_posicao[endereco.posicao_id] = endereco
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
    db.session.delete(ocupacao)
    novo_endereco = ProdutoEndereco(
        produto_id=produto_id,
        posicao_id=ocupacao.posicao_id
    )
    db.session.add(novo_endereco)
    db.session.commit()
    return produto_anterior
@endereco_bp.route("/buscar-produtos")
def buscar_produtos():
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
            Produto.ativo.is_(True),
            or_(
                cast(
                    Produto.codigo,
                    String
                ).ilike(padrao),
                Produto.codigo_barras.ilike(padrao),
                Produto.descricao.ilike(padrao)
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
        enderecos = []
        for vinculo in produto.enderecos:
            enderecos.append(
                formatar_endereco_posicao(
                    vinculo.posicao
                )
            )
        endereco_atual = None

        if len(produto.enderecos) == 1:
            vinculo_atual = produto.enderecos[0]
            posicao_atual = vinculo_atual.posicao

            endereco_atual = {
                "endereco_id": vinculo_atual.id,
                "posicao_id": posicao_atual.id,
                "rua_id": posicao_atual.nivel.modulo.predio.rua.id,
                "predio_id": posicao_atual.nivel.modulo.predio.id,
                "modulo_id": posicao_atual.nivel.modulo.id,
                "endereco": formatar_endereco_operacional(
                    posicao_atual
                )
            }

        resultados.append(
            {
                "id": produto.id,
                "codigo": produto.codigo,
                "codigo_barras": produto.codigo_barras,
                "descricao": produto.descricao,
                "enderecado": len(enderecos) > 0,
                "total_enderecos": len(enderecos),
                "multiplos_enderecos": len(enderecos) > 1,
                "enderecos": enderecos,
                "endereco_atual": endereco_atual
            }
        )
    return jsonify(resultados)
@endereco_bp.route("/buscar-posicoes")
def buscar_posicoes():
    termo = request.args.get(
        "q",
        ""
    ).strip()
    if len(termo) < 2:
        return jsonify([])
    termo_normalizado = normalizar_texto(
        termo
    )
    termo_atalho = normalizar_atalho(
        termo
    )
    posicoes = Posicao.query.filter_by(
        ativo=True
    ).all()
    resultados = []
    for posicao in posicoes:
        endereco_formatado = formatar_endereco_posicao(
            posicao
        )
        endereco_normalizado = normalizar_texto(
            endereco_formatado
        )
        atalho_posicao = gerar_atalho_posicao(
            posicao
        )
        corresponde_busca_normal = (
            termo_normalizado
            in endereco_normalizado
        )
        corresponde_atalho = (
            atalho_posicao is not None
            and atalho_posicao.startswith(
                termo_atalho
            )
        )
        if (
            not corresponde_busca_normal
            and not corresponde_atalho
        ):
            continue
        ocupacao = ProdutoEndereco.query.filter_by(
            posicao_id=posicao.id
        ).first()
        resultado = {
            "id": posicao.id,
            "endereco": endereco_formatado,
            "ocupada": ocupacao is not None,
            "produto": None
        }
        if ocupacao:
            resultado["produto"] = {
                "id": ocupacao.produto.id,
                "codigo": ocupacao.produto.codigo,
                "descricao": ocupacao.produto.descricao
            }
        resultados.append(resultado)
        if len(resultados) >= 20:
            break
    return jsonify(resultados)
@endereco_bp.route("/estrutura/predios")
def estrutura_predios():
    rua_id = request.args.get(
        "rua_id",
        type=int
    )

    if not rua_id:
        return jsonify([])

    predios = Predio.query.filter_by(
        rua_id=rua_id,
        ativo=True
    ).order_by(
        Predio.nome
    ).all()

    return jsonify([
        {
            "id": predio.id,
            "nome": predio.nome
        }
        for predio in predios
    ])


@endereco_bp.route("/estrutura/modulos")
def estrutura_modulos():
    predio_id = request.args.get(
        "predio_id",
        type=int
    )

    if not predio_id:
        return jsonify([])

    modulos = Modulo.query.filter_by(
        predio_id=predio_id,
        ativo=True
    ).order_by(
        Modulo.nome
    ).all()

    return jsonify([
        {
            "id": modulo.id,
            "nome": modulo.nome
        }
        for modulo in modulos
    ])


@endereco_bp.route("/estrutura/posicoes")
def estrutura_posicoes():
    modulo_id = request.args.get(
        "modulo_id",
        type=int
    )

    if not modulo_id:
        return jsonify([])

    posicoes = (
        Posicao.query
        .join(
            Nivel
        )
        .filter(
            Nivel.modulo_id == modulo_id,
            Nivel.ativo.is_(True),
            Posicao.ativo.is_(True)
        )
        .order_by(
            Posicao.nome
        )
        .all()
    )

    resultados = []

    for posicao in posicoes:
        ocupacao = ProdutoEndereco.query.filter_by(
            posicao_id=posicao.id
        ).first()

        resultado = {
            "id": posicao.id,
            "nome": posicao.nome,
            "ocupada": ocupacao is not None,
            "produto": None
        }

        if ocupacao:
            resultado["produto"] = {
                "id": ocupacao.produto.id,
                "codigo": ocupacao.produto.codigo,
                "descricao": ocupacao.produto.descricao
            }

        resultados.append(
            resultado
        )

    return jsonify(
        resultados
    )


@endereco_bp.route("/")
def listar():

    pesquisa = request.args.get("q", "").strip()
    pagina = max(1, request.args.get("page", 1, type=int))

    consulta = ProdutoEndereco.query.options(
        joinedload(ProdutoEndereco.produto),
        joinedload(ProdutoEndereco.posicao)
        .joinedload(Posicao.nivel)
        .joinedload(Nivel.modulo)
        .joinedload(Modulo.predio)
        .joinedload(Predio.rua)
    )

    if pesquisa:

        padrao = f"%{pesquisa}%"

        consulta = consulta.join(Produto).filter(
            or_(
                cast(Produto.codigo, String).ilike(padrao),
                Produto.descricao.ilike(padrao),
                Produto.codigo_barras.ilike(padrao)
            )
        )

    paginacao = consulta.order_by(
        ProdutoEndereco.data_cadastro.desc(),
        ProdutoEndereco.id.desc()
    ).paginate(
        page=pagina,
        per_page=30,
        error_out=False
    )

    if paginacao.total and pagina > paginacao.pages:
        return redirect(
            url_for(
                "endereco.listar",
                page=paginacao.pages,
                q=pesquisa
            )
        )

    return render_template(
        "endereco/listar.html",
        enderecos=paginacao.items,
        paginacao=paginacao,
        pesquisa=pesquisa
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
            produto_id=produto_id
        ).first()
        if endereco_existente:
            flash(
                "Este produto já possui um endereço cadastrado. Use Alterar endereço para mudar a posição.",
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
        db.session.add(endereco)
        db.session.commit()
        flash(
            "Produto endereçado com sucesso.",
            "success"
        )
        return redirect(
            url_for("endereco.listar")
        )
    codigo_produto = request.args.get(
        "codigo",
        type=int
    )
    produto_id_selecionado = None
    if codigo_produto:
        produto_selecionado = Produto.query.filter_by(
            codigo=codigo_produto,
            ativo=True
        ).first()
        if produto_selecionado:
            produto_id_selecionado = produto_selecionado.id
        else:
            flash(
                "O produto informado não está disponível para endereçamento.",
                "warning"
            )
    return render_template(
        "endereco/form.html",
        endereco=None,
        produtos=produtos,
        posicoes=posicoes,
        produto_id_selecionado=produto_id_selecionado,
        posicao_id_selecionada=None,
        conflito=None
    )
@endereco_bp.route("/novo-estrutura", methods=["GET", "POST"])
def novo_estrutura():
    produtos, posicoes = preparar_opcoes_formulario()

    ruas = Rua.query.filter_by(
        ativo=True
    ).order_by(
        Rua.nome
    ).all()

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
                "endereco/form_estrutura.html",
                endereco=None,
                endereco_atual=None,
                modo_alteracao=False,
                multiplos_enderecos=False,
                produtos=produtos,
                posicoes=posicoes,
                ruas=ruas,
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

        enderecos_produto = (
            ProdutoEndereco.query
            .filter_by(
                produto_id=produto_id
            )
            .order_by(
                ProdutoEndereco.id
            )
            .all()
        )

        if len(enderecos_produto) > 1:
            flash(
                (
                    "Este produto possui mais de um endereço cadastrado. "
                    "Gerencie os endereços antes de alterar."
                ),
                "warning"
            )
            return render_template(
                "endereco/form_estrutura.html",
                endereco=None,
                endereco_atual=None,
                modo_alteracao=False,
                multiplos_enderecos=True,
                produtos=produtos,
                posicoes=posicoes,
                ruas=ruas,
                produto_id_selecionado=produto_id,
                posicao_id_selecionada=None,
                conflito=None
            )

        endereco_atual = (
            enderecos_produto[0]
            if enderecos_produto
            else None
        )

        if (
            endereco_atual
            and endereco_atual.posicao_id == posicao_id
        ):
            flash(
                "O produto já está nesta posição.",
                "warning"
            )
            return render_template(
                "endereco/form_estrutura.html",
                endereco=None,
                endereco_atual=endereco_atual,
                modo_alteracao=True,
                multiplos_enderecos=False,
                produtos=produtos,
                posicoes=posicoes,
                ruas=ruas,
                produto_id_selecionado=produto_id,
                posicao_id_selecionada=posicao_id,
                conflito=None
            )

        ocupacao = buscar_ocupacao_posicao(
            posicao_id=posicao_id,
            produto_id=produto_id,
            endereco_id=(
                endereco_atual.id
                if endereco_atual
                else None
            )
        )

        if ocupacao and not confirmar_substituicao:
            return render_template(
                "endereco/form_estrutura.html",
                endereco=None,
                endereco_atual=endereco_atual,
                modo_alteracao=endereco_atual is not None,
                multiplos_enderecos=False,
                produtos=produtos,
                posicoes=posicoes,
                ruas=ruas,
                produto_id_selecionado=produto_id,
                posicao_id_selecionada=posicao_id,
                conflito={
                    "produto_novo": produto,
                    "produto_atual": ocupacao.produto,
                    "posicao": posicao
                }
            )

        if endereco_atual:
            produto_anterior = None

            if ocupacao:
                produto_anterior = ocupacao.produto
                db.session.delete(
                    ocupacao
                )

            endereco_atual.posicao_id = posicao_id
            db.session.commit()

            if produto_anterior:
                flash(
                    (
                        "Endereço atualizado com sucesso. "
                        f"O produto {produto_anterior.codigo} - "
                        f"{produto_anterior.descricao} foi removido "
                        "da posição selecionada."
                    ),
                    "success"
                )
            else:
                flash(
                    "Endereço atualizado com sucesso.",
                    "success"
                )

            return redirect(
                url_for(
                    "endereco.listar"
                )
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
                url_for(
                    "endereco.listar"
                )
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
            url_for(
                "endereco.listar"
            )
        )

    codigo_produto = request.args.get(
        "codigo",
        type=int
    )

    produto_id_selecionado = None
    posicao_id_selecionada = None
    endereco_atual = None
    multiplos_enderecos = False

    if codigo_produto:
        produto_selecionado = Produto.query.filter_by(
            codigo=codigo_produto,
            ativo=True
        ).first()

        if produto_selecionado:
            produto_id_selecionado = produto_selecionado.id

            enderecos_produto = (
                ProdutoEndereco.query
                .filter_by(
                    produto_id=produto_selecionado.id
                )
                .order_by(
                    ProdutoEndereco.id
                )
                .all()
            )

            if len(enderecos_produto) == 1:
                endereco_atual = enderecos_produto[0]
                posicao_id_selecionada = (
                    endereco_atual.posicao_id
                )

            elif len(enderecos_produto) > 1:
                multiplos_enderecos = True

        else:
            flash(
                "O produto informado não está disponível para endereçamento.",
                "warning"
            )

    return render_template(
        "endereco/form_estrutura.html",
        endereco=None,
        endereco_atual=endereco_atual,
        modo_alteracao=endereco_atual is not None,
        multiplos_enderecos=multiplos_enderecos,
        produtos=produtos,
        posicoes=posicoes,
        ruas=ruas,
        produto_id_selecionado=produto_id_selecionado,
        posicao_id_selecionada=posicao_id_selecionada,
        conflito=None
    )


@endereco_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    endereco = ProdutoEndereco.query.get_or_404(id)
    produtos, posicoes = preparar_opcoes_formulario()
    if endereco.produto and endereco.produto not in produtos:
        endereco.produto.total_enderecos = len(
            endereco.produto.enderecos
        )
        endereco.produto.enderecado = True
        produtos.append(endereco.produto)
        produtos.sort(
            key=lambda produto: produto.descricao.lower()
        )
    if endereco.posicao and endereco.posicao not in posicoes:
        endereco.posicao.ocupada = True
        endereco.posicao.produto_ocupante = endereco.produto
        posicoes.append(endereco.posicao)
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
        produto = Produto.query.get_or_404(produto_id)
        posicao = Posicao.query.get_or_404(posicao_id)
        if not produto.ativo and produto.id != endereco.produto_id:
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
        if not posicao.ativo and posicao.id != endereco.posicao_id:
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
        if produto_id != endereco.produto_id:
            endereco_existente = ProdutoEndereco.query.filter(
                ProdutoEndereco.produto_id == produto_id,
                ProdutoEndereco.id != endereco.id
            ).first()
            if endereco_existente:
                flash(
                    "Este produto já possui um endereço cadastrado. Use Alterar endereço para mudar a posição.",
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
            db.session.delete(ocupacao)
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
    endereco = ProdutoEndereco.query.get_or_404(id)
    db.session.delete(endereco)
    db.session.commit()
    flash(
        "Endereço removido com sucesso.",
        "success"
    )
    return redirect(
        url_for("endereco.listar")
    )
