from flask import Blueprint, current_app, flash, redirect, url_for
from services.monitoramento_service import MonitoramentoService

monitoramento_bp = Blueprint("monitoramento", __name__, url_prefix="/monitoramento")


@monitoramento_bp.route("/verificar-todos", methods=["POST"])
def verificar_todos():
    service = MonitoramentoService(current_app.config)
    resultados = service.verificar_todos()
    sucessos = sum(1 for r in resultados if r.get("sucesso"))
    falhas = len(resultados) - sucessos
    flash(f"Verificação concluída. Sucessos: {sucessos}. Falhas: {falhas}.", "info")
    return redirect(url_for("dashboard.index"))


@monitoramento_bp.route("/verificar/<int:produto_id>", methods=["POST"])
def verificar_produto(produto_id):
    service = MonitoramentoService(current_app.config)
    resultado = service.verificar_produto(produto_id)

    if resultado.get("sucesso"):
        flash("Produto verificado com sucesso!", "success")
    else:
        flash(f"Erro na verificação: {resultado.get('mensagem')}", "danger")

    return redirect(url_for("produto.listar"))
