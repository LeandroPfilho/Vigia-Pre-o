from datetime import datetime
from decimal import Decimal
from database.extensions import db
from models.alerta import Alerta


class AlertaRepository:
    @staticmethod
    def criar(produto, preco_anterior, preco_atual, percentual_queda, tipo_alerta="queda_preco"):
        alerta = Alerta(
            produto_id=produto.id,
            preco_anterior=preco_anterior,
            preco_atual=preco_atual,
            percentual_queda=percentual_queda,
            tipo_alerta=tipo_alerta,
        )
        produto.ultimo_alerta_enviado = datetime.utcnow()
        db.session.add(alerta)
        db.session.commit()
        return alerta

    @staticmethod
    def listar_todos():
        return Alerta.query.order_by(Alerta.enviado_em.desc()).all()

    @staticmethod
    def listar_ultimos(limite=5):
        return Alerta.query.order_by(Alerta.enviado_em.desc()).limit(limite).all()

    @staticmethod
    def contar_total():
        return Alerta.query.count()

    @staticmethod
    def existe_alerta_similar(produto_id, preco_anterior, preco_atual, tipo_alerta="queda_preco") -> bool:
        alerta = Alerta.query.filter_by(
            produto_id=produto_id,
            preco_anterior=Decimal(preco_anterior),
            preco_atual=Decimal(preco_atual),
            tipo_alerta=tipo_alerta,
        ).first()
        return alerta is not None
