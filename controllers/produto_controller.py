from flask import Blueprint, current_app, jsonify, render_template, request, redirect, url_for, flash

from repositories.produto_repository import ProdutoRepository
from services.price_detector_service import PriceDetectorService

produto_bp = Blueprint("produto", __name__, url_prefix="/produtos")


@produto_bp.route("/")
def listar():
    produtos = ProdutoRepository.listar_todos()
    return render_template("produtos.html", produtos=produtos)


@produto_bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        dados = _dados_formulario()
        ProdutoRepository.criar(dados)
        if dados["estrategia_coleta"] == "auto":
            flash("Produto cadastrado no modo simples. O preço será detectado automaticamente nas verificações.", "success")
        else:
            flash("Produto cadastrado no modo avançado com sucesso!", "success")
        return redirect(url_for("produto.listar"))

    return render_template("produto_form.html", produto=None, titulo="Novo Produto")


@produto_bp.route("/<int:produto_id>/editar", methods=["GET", "POST"])
def editar(produto_id):
    produto = ProdutoRepository.buscar_por_id(produto_id)
    if not produto:
        return render_template("erro.html", mensagem="Produto não encontrado"), 404

    if request.method == "POST":
        dados = _dados_formulario()
        ProdutoRepository.atualizar(produto, dados)
        flash("Produto atualizado com sucesso!", "success")
        return redirect(url_for("produto.listar"))

    return render_template("produto_form.html", produto=produto, titulo="Editar Produto")


@produto_bp.route("/<int:produto_id>/desativar", methods=["POST"])
def desativar(produto_id):
    produto = ProdutoRepository.buscar_por_id(produto_id)
    if not produto:
        return render_template("erro.html", mensagem="Produto não encontrado"), 404
    ProdutoRepository.desativar(produto)
    flash("Produto desativado com sucesso!", "warning")
    return redirect(url_for("produto.listar"))


@produto_bp.route("/<int:produto_id>/ativar", methods=["POST"])
def ativar(produto_id):
    produto = ProdutoRepository.buscar_por_id(produto_id)
    if not produto:
        return render_template("erro.html", mensagem="Produto não encontrado"), 404
    ProdutoRepository.ativar(produto)
    flash("Produto ativado com sucesso!", "success")
    return redirect(url_for("produto.listar"))


@produto_bp.route("/detectar-precos", methods=["POST"])
def detectar_precos():
    """Endpoint usado pelo botão 'Detectar preço' no modo simples."""
    url = (request.form.get("url") or "").strip()
    usar_selenium = request.form.get("usar_selenium") == "true"

    if not url:
        return jsonify({"sucesso": False, "mensagem": "Informe a URL do produto."}), 400

    detector = PriceDetectorService(
        timeout=current_app.config.get("REQUEST_TIMEOUT", 10),
        retries=current_app.config.get("REQUEST_RETRIES", 3),
    )
    candidatos = detector.detectar_precos(url=url, usar_selenium=usar_selenium, limite=8)

    if not candidatos:
        return jsonify(
            {
                "sucesso": False,
                "mensagem": "Nenhum preço foi encontrado automaticamente. Tente marcar 'usar Selenium' ou use o modo avançado.",
            }
        )

    return jsonify({"sucesso": True, "candidatos": [c.to_dict() for c in candidatos]})


def _dados_formulario():
    ativo = request.form.get("ativo") == "on"
    modo_cadastro = request.form.get("modo_cadastro", "simples")

    if modo_cadastro == "simples":
        # No modo simples mantemos a estratégia como auto.
        # Se o usuário escolher um candidato, salvamos o seletor apenas como dica interna.
        estrategia = "auto"
        seletor = request.form.get("seletor_detectado", "auto") or "auto"
    else:
        estrategia = request.form.get("estrategia_coleta", "beautifulsoup")
        seletor = request.form.get("seletor_css", "").strip()

    # Garante que o banco não receba seletor vazio.
    if not seletor:
        seletor = "auto"

    return {
        "nome": request.form.get("nome", "").strip(),
        "url": request.form.get("url", "").strip(),
        "seletor_css": seletor,
        "estrategia_coleta": estrategia,
        "ativo": ativo,
        "status": "ativo" if ativo else "inativo",
    }
