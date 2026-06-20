from datetime import datetime
from database.extensions import db


class Alerta(db.Model):
    __tablename__ = "alertas"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    preco_anterior = db.Column(db.Numeric(10, 2), nullable=False)
    preco_atual = db.Column(db.Numeric(10, 2), nullable=False)
    percentual_queda = db.Column(db.Numeric(6, 2), nullable=False)
    enviado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tipo_alerta = db.Column(db.String(50), nullable=False, default="queda_preco")

    produto = db.relationship("Produto", back_populates="alertas")

    def __repr__(self):
        return f"<Alerta produto={self.produto_id} queda={self.percentual_queda}%>"
