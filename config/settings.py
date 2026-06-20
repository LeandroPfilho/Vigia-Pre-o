import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///vigia_preco.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
    REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))
    INTERVALO_REQUISICOES_SEGUNDOS = int(os.getenv("INTERVALO_REQUISICOES_SEGUNDOS", "5"))
    INTERVALO_MONITORAMENTO_MINUTOS = int(os.getenv("INTERVALO_MONITORAMENTO_MINUTOS", "60"))

    ALERTA_QUEDA_PERCENTUAL = 8.0
