from datetime import datetime
from database.extensions import db


class Produto(db.Model):
    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    url = db.Column(db.Text, nullable=False)
    seletor_css = db.Column(db.String(255), nullable=False)
    estrategia_coleta = db.Column(db.String(30), nullable=False, default="beautifulsoup")

    preco_atual = db.Column(db.Numeric(10, 2), nullable=True)
    ultimo_preco_registrado = db.Column(db.Numeric(10, 2), nullable=True)
    menor_preco_historico = db.Column(db.Numeric(10, 2), nullable=True)
    data_ultima_verificacao = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(50), nullable=False, default="ativo")
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    ultimo_alerta_enviado = db.Column(db.DateTime, nullable=True)

    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    historicos = db.relationship("HistoricoPreco", back_populates="produto", cascade="all, delete-orphan")
    alertas = db.relationship("Alerta", back_populates="produto", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Produto {self.id} - {self.nome}>"
