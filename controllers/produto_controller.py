from flask import Blueprint, render_template, request, redirect, url_for, flash
from repositories.produto_repository import ProdutoRepository

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
        flash("Produto cadastrado com sucesso!", "success")
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


def _dados_formulario():
    ativo = request.form.get("ativo") == "on"
    return {
        "nome": request.form.get("nome", "").strip(),
        "url": request.form.get("url", "").strip(),
        "seletor_css": request.form.get("seletor_css", "").strip(),
        "estrategia_coleta": request.form.get("estrategia_coleta", "beautifulsoup"),
        "ativo": ativo,
        "status": "ativo" if ativo else "inativo",
    }
