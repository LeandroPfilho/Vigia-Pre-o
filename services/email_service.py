import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, user, password, destino, smtp_server, smtp_port):
        self.user = user
        self.password = password
        self.destino = destino
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def configurado(self) -> bool:
        return all([self.user, self.password, self.destino, self.smtp_server, self.smtp_port])

    def enviar_alerta_queda(self, produto, preco_anterior, preco_atual, percentual_queda) -> bool:
        if not self.configurado():
            logger.warning("E-mail não configurado. Alerta não enviado para o produto %s", produto.nome)
            return False

        assunto = f"Alerta de queda de preço: {produto.nome}"
        corpo = f"""Alerta de queda de preço!

Produto: {produto.nome}
Preço anterior: R$ {preco_anterior}
Preço atual: R$ {preco_atual}
Queda: {percentual_queda}%

Link: {produto.url}
"""

        mensagem = MIMEMultipart()
        mensagem["From"] = self.user
        mensagem["To"] = self.destino
        mensagem["Subject"] = assunto
        mensagem.attach(MIMEText(corpo, "plain", "utf-8"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as servidor:
                servidor.starttls()
                servidor.login(self.user, self.password)
                servidor.send_message(mensagem)
            logger.info("Alerta enviado para %s sobre %s", self.destino, produto.nome)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Erro ao enviar e-mail: %s", exc)
            return False
