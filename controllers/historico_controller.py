from flask import Blueprint, render_template
from repositories.historico_repository import HistoricoRepository
from repositories.produto_repository import ProdutoRepository

historico_bp = Blueprint("historico", __name__, url_prefix="/historico")


@historico_bp.route("/")
def listar_todos():
    historicos = HistoricoRepository.listar_todos()
    return render_template("historico.html", historicos=historicos, produto=None)


@historico_bp.route("/produto/<int:produto_id>")
def listar_por_produto(produto_id):
    produto = ProdutoRepository.buscar_por_id(produto_id)
    if not produto:
        return render_template("erro.html", mensagem="Produto não encontrado"), 404
    historicos = HistoricoRepository.listar_por_produto(produto_id)
    return render_template("historico.html", historicos=historicos, produto=produto)
