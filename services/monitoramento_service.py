import logging
import time
from datetime import datetime
from decimal import Decimal

from repositories.produto_repository import ProdutoRepository
from repositories.historico_repository import HistoricoRepository
from repositories.alerta_repository import AlertaRepository
from services.price_service import PriceService
from services.scraper_service import ScraperService
from services.email_service import EmailService

logger = logging.getLogger(__name__)


class MonitoramentoService:
    def __init__(self, config):
        self.config = config
        self.scraper = ScraperService(
            timeout=self._get_config("REQUEST_TIMEOUT", 10),
            retries=self._get_config("REQUEST_RETRIES", 3),
        )
        self.email_service = EmailService(
            user=self._get_config("EMAIL_USER", ""),
            password=self._get_config("EMAIL_PASSWORD", ""),
            destino=self._get_config("EMAIL_DESTINO", ""),
            smtp_server=self._get_config("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=self._get_config("SMTP_PORT", 587),
        )

    def _get_config(self, chave, padrao=None):
        if isinstance(self.config, dict):
            return self.config.get(chave, padrao)
        return getattr(self.config, chave, padrao)

    def verificar_todos(self):
        produtos = ProdutoRepository.listar_ativos()
        resultados = []

        for indice, produto in enumerate(produtos):
            resultados.append(self.verificar_produto(produto.id))
            if indice < len(produtos) - 1:
                time.sleep(self._get_config("INTERVALO_REQUISICOES_SEGUNDOS", 5))

        return resultados

    def verificar_produto(self, produto_id):
        produto = ProdutoRepository.buscar_por_id(produto_id)
        if not produto:
            return {"sucesso": False, "mensagem": "Produto não encontrado"}

        if not produto.ativo:
            return {"sucesso": False, "mensagem": "Produto inativo"}

        data_verificacao = datetime.utcnow()
        preco_anterior = produto.ultimo_preco_registrado

        try:
            resultado = self.scraper.buscar_preco(
                url=produto.url,
                seletor_css=produto.seletor_css,
                estrategia=produto.estrategia_coleta,
            )

            if not resultado.sucesso:
                ProdutoRepository.atualizar_status_erro(produto, resultado.status, data_verificacao)
                HistoricoRepository.criar(
                    produto_id=produto.id,
                    preco=None,
                    status_verificacao=resultado.status,
                    mensagem_erro=resultado.mensagem_erro,
                    data_verificacao=data_verificacao,
                )
                return {"sucesso": False, "produto": produto.nome, "mensagem": resultado.mensagem_erro}

            preco_atual = PriceService.converter_preco_brasileiro(resultado.preco_texto)

            HistoricoRepository.criar(
                produto_id=produto.id,
                preco=preco_atual,
                status_verificacao="verificado_com_sucesso",
                data_verificacao=data_verificacao,
            )

            # Calcula alerta antes de atualizar o último preço registrado.
            alerta_enviado = False
            percentual_queda = Decimal("0.00")
            if preco_anterior is not None:
                percentual_queda = PriceService.calcular_queda_percentual(preco_anterior, preco_atual)
                if percentual_queda >= Decimal(str(self._get_config("ALERTA_QUEDA_PERCENTUAL", 8.0))):
                    alerta_enviado = self._processar_alerta(produto, preco_anterior, preco_atual, percentual_queda)

            ProdutoRepository.finalizar_verificacao(
                produto=produto,
                preco_atual=preco_atual,
                status="verificado_com_sucesso",
                data_verificacao=data_verificacao,
            )

            return {
                "sucesso": True,
                "produto": produto.nome,
                "preco_atual": preco_atual,
                "percentual_queda": percentual_queda,
                "alerta_enviado": alerta_enviado,
            }

        except Exception as exc:  # noqa: BLE001
            logger.exception("Erro ao verificar produto %s: %s", produto.nome, exc)
            ProdutoRepository.atualizar_status_erro(produto, "erro_banco", data_verificacao)
            HistoricoRepository.criar(
                produto_id=produto.id,
                preco=None,
                status_verificacao="erro_banco",
                mensagem_erro=str(exc),
                data_verificacao=data_verificacao,
            )
            return {"sucesso": False, "produto": produto.nome, "mensagem": str(exc)}

    def _processar_alerta(self, produto, preco_anterior, preco_atual, percentual_queda):
        existe = AlertaRepository.existe_alerta_similar(
            produto_id=produto.id,
            preco_anterior=preco_anterior,
            preco_atual=preco_atual,
            tipo_alerta="queda_preco",
        )

        if existe:
            logger.info("Alerta repetido evitado para produto %s", produto.nome)
            return False

        email_enviado = self.email_service.enviar_alerta_queda(
            produto=produto,
            preco_anterior=preco_anterior,
            preco_atual=preco_atual,
            percentual_queda=percentual_queda,
        )

        # Mesmo quando o e-mail não está configurado, registra o alerta para evitar repetição.
        AlertaRepository.criar(
            produto=produto,
            preco_anterior=preco_anterior,
            preco_atual=preco_atual,
            percentual_queda=percentual_queda,
            tipo_alerta="queda_preco",
        )
        return email_enviado
