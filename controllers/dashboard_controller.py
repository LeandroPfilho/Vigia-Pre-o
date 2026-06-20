from flask import Blueprint, render_template
from repositories.produto_repository import ProdutoRepository
from repositories.alerta_repository import AlertaRepository

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    dados = {
        "total_produtos": ProdutoRepository.contar_total(),
        "total_ativos": ProdutoRepository.contar_ativos(),
        "total_alertas": AlertaRepository.contar_total(),
        "produtos_com_erro": ProdutoRepository.contar_com_erro(),
        "ultimos_produtos": ProdutoRepository.ultimos_verificados(5),
        "ultimos_alertas": AlertaRepository.listar_ultimos(5),
    }
    return render_template("index.html", dados=dados)
