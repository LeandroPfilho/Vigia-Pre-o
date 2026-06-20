from decimal import Decimal
from typing import Optional
from database.extensions import db
from models.produto import Produto


class ProdutoRepository:
    @staticmethod
    def listar_todos():
        return Produto.query.order_by(Produto.criado_em.desc()).all()

    @staticmethod
    def listar_ativos():
        return Produto.query.filter_by(ativo=True).order_by(Produto.nome.asc()).all()

    @staticmethod
    def buscar_por_id(produto_id: int) -> Optional[Produto]:
        return Produto.query.get(produto_id)

    @staticmethod
    def criar(dados: dict) -> Produto:
        produto = Produto(**dados)
        db.session.add(produto)
        db.session.commit()
        return produto

    @staticmethod
    def atualizar(produto: Produto, dados: dict) -> Produto:
        for campo, valor in dados.items():
            setattr(produto, campo, valor)
        db.session.commit()
        return produto

    @staticmethod
    def desativar(produto: Produto) -> Produto:
        produto.ativo = False
        produto.status = "inativo"
        db.session.commit()
        return produto

    @staticmethod
    def ativar(produto: Produto) -> Produto:
        produto.ativo = True
        produto.status = "ativo"
        db.session.commit()
        return produto

    @staticmethod
    def atualizar_preco(produto: Produto, preco_atual: Decimal, status: str) -> Produto:
        produto.preco_atual = preco_atual
        produto.menor_preco_historico = (
            preco_atual if produto.menor_preco_historico is None else min(produto.menor_preco_historico, preco_atual)
        )
        produto.status = status
        db.session.commit()
        return produto

    @staticmethod
    def finalizar_verificacao(produto: Produto, preco_atual: Decimal, status: str, data_verificacao):
        produto.ultimo_preco_registrado = preco_atual
        produto.preco_atual = preco_atual
        produto.menor_preco_historico = (
            preco_atual if produto.menor_preco_historico is None else min(produto.menor_preco_historico, preco_atual)
        )
        produto.data_ultima_verificacao = data_verificacao
        produto.status = status
        db.session.commit()
        return produto

    @staticmethod
    def atualizar_status_erro(produto: Produto, status: str, data_verificacao):
        produto.status = status
        produto.data_ultima_verificacao = data_verificacao
        db.session.commit()
        return produto

    @staticmethod
    def contar_total() -> int:
        return Produto.query.count()

    @staticmethod
    def contar_ativos() -> int:
        return Produto.query.filter_by(ativo=True).count()

    @staticmethod
    def contar_com_erro() -> int:
        return Produto.query.filter(Produto.status.like("erro_%")).count()

    @staticmethod
    def ultimos_verificados(limite: int = 5):
        return Produto.query.filter(Produto.data_ultima_verificacao.isnot(None)).order_by(
            Produto.data_ultima_verificacao.desc()
        ).limit(limite).all()
