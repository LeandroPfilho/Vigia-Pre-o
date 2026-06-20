from database.extensions import db


def init_db():
    # Importa os models para que o SQLAlchemy conheça as tabelas antes do create_all.
    from models.produto import Produto  # noqa: F401
    from models.historico_preco import HistoricoPreco  # noqa: F401
    from models.alerta import Alerta  # noqa: F401

    db.create_all()
