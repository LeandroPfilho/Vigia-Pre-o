import logging
from apscheduler.schedulers.background import BackgroundScheduler

from services.monitoramento_service import MonitoramentoService

logger = logging.getLogger(__name__)
_scheduler = None


def iniciar_agendador(app):
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    intervalo = app.config.get("INTERVALO_MONITORAMENTO_MINUTOS", 60)
    monitoramento = MonitoramentoService(app.config)

    def job():
        with app.app_context():
            logger.info("Iniciando verificação automática de preços")
            monitoramento.verificar_todos()
            logger.info("Verificação automática finalizada")

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(job, "interval", minutes=intervalo, id="monitoramento_precos", replace_existing=True)
    _scheduler.start()

    logger.info("Agendador iniciado. Intervalo: %s minutos", intervalo)
    return _scheduler
