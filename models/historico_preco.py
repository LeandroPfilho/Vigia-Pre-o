from datetime import datetime
from database.extensions import db


class HistoricoPreco(db.Model):
    __tablename__ = "historico_precos"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=True)
    data_verificacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status_verificacao = db.Column(db.String(50), nullable=False)
    mensagem_erro = db.Column(db.Text, nullable=True)

    produto = db.relationship("Produto", back_populates="historicos")

    def __repr__(self):
        return f"<HistoricoPreco produto={self.produto_id} preco={self.preco}>"
