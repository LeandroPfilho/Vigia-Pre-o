from flask import Blueprint, render_template
from repositories.alerta_repository import AlertaRepository

alerta_bp = Blueprint("alerta", __name__, url_prefix="/alertas")


@alerta_bp.route("/")
def listar():
    alertas = AlertaRepository.listar_todos()
    return render_template("alertas.html", alertas=alertas)
