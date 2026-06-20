from flask import Flask

from config.settings import Config
from database.extensions import db
from database.db import init_db
from utils.logger import setup_logger
from repositories.produto_repository import ProdutoRepository
from services.price_service import PriceService
from services.scheduler_service import iniciar_agendador

from controllers.dashboard_controller import dashboard_bp
from controllers.produto_controller import produto_bp
from controllers.monitoramento_controller import monitoramento_bp
from controllers.historico_controller import historico_bp
from controllers.alerta_controller import alerta_bp


def create_app():
    setup_logger()

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(monitoramento_bp)
    app.register_blueprint(historico_bp)
    app.register_blueprint(alerta_bp)

    app.jinja_env.filters["moeda"] = PriceService.formatar_moeda

    with app.app_context():
        init_db()
        cadastrar_produtos_teste()
        iniciar_agendador(app)

    return app


def cadastrar_produtos_teste():
    if ProdutoRepository.contar_total() > 0:
        return

    produtos = [
        {
            "nome": "Produto Teste Automático",
            "url": "https://example.com/produto-teste",
            "seletor_css": "auto",
            "estrategia_coleta": "auto",
            "status": "ativo",
            "ativo": True,
        },
        {
            "nome": "Produto Teste API",
            "url": "https://api.exemplo.com/produto/1",
            "seletor_css": "produto.preco",
            "estrategia_coleta": "api",
            "status": "ativo",
            "ativo": True,
        },
    ]

    for dados in produtos:
        ProdutoRepository.criar(dados)


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, use_reloader=False)
