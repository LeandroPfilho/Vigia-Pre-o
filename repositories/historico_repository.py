from database.extensions import db
from models.historico_preco import HistoricoPreco


class HistoricoRepository:
    @staticmethod
    def criar(produto_id, preco, status_verificacao, mensagem_erro=None, data_verificacao=None):
        historico = HistoricoPreco(
            produto_id=produto_id,
            preco=preco,
            status_verificacao=status_verificacao,
            mensagem_erro=mensagem_erro,
        )
        if data_verificacao is not None:
            historico.data_verificacao = data_verificacao
        db.session.add(historico)
        db.session.commit()
        return historico

    @staticmethod
    def listar_por_produto(produto_id):
        return HistoricoPreco.query.filter_by(produto_id=produto_id).order_by(
            HistoricoPreco.data_verificacao.desc()
        ).all()

    @staticmethod
    def listar_todos():
        return HistoricoPreco.query.order_by(HistoricoPreco.data_verificacao.desc()).all()
