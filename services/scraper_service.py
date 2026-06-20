import logging
import time
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests import RequestException, Timeout
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from services.price_detector_service import PriceDetectorService

logger = logging.getLogger(__name__)


@dataclass
class ScraperResult:
    sucesso: bool
    preco_texto: str | None = None
    status: str = "verificado_com_sucesso"
    mensagem_erro: str | None = None


class ScraperService:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )

    def __init__(self, timeout=10, retries=3):
        self.timeout = timeout
        self.retries = retries

    def buscar_preco(self, url: str, seletor_css: str, estrategia: str) -> ScraperResult:
        estrategia = (estrategia or "auto").lower().strip()
        seletor_css = (seletor_css or "auto").strip()

        if estrategia == "auto":
            return self.buscar_automaticamente(url, seletor_preferido=seletor_css)
        if seletor_css == "auto":
            return self.buscar_automaticamente(url)
        if estrategia == "beautifulsoup":
            return self.buscar_com_beautifulsoup(url, seletor_css)
        if estrategia == "selenium":
            return self.buscar_com_selenium(url, seletor_css)
        if estrategia == "api":
            return self.buscar_com_api(url, seletor_css)
        return ScraperResult(False, status="erro_preco_nao_encontrado", mensagem_erro="Estratégia de coleta inválida")

    def buscar_automaticamente(self, url: str, seletor_preferido: str | None = None) -> ScraperResult:
        # Se o usuário escolheu um preço na tela simples, tentamos reaproveitar o seletor salvo.
        # Se falhar, caímos na detecção automática completa.
        if seletor_preferido and seletor_preferido != "auto":
            resultado_preferido = self.buscar_com_beautifulsoup(url, seletor_preferido)
            if resultado_preferido.sucesso:
                return resultado_preferido

        detector = PriceDetectorService(timeout=self.timeout, retries=self.retries)
        candidato = detector.detectar_melhor_preco(url)
        if not candidato:
            return ScraperResult(
                False,
                status="erro_preco_nao_encontrado",
                mensagem_erro="Não foi possível detectar preço automaticamente. Tente o modo avançado com seletor CSS.",
            )
        return ScraperResult(True, preco_texto=candidato.preco_texto)

    def buscar_com_beautifulsoup(self, url: str, seletor_css: str) -> ScraperResult:
        headers = {"User-Agent": self.USER_AGENT}

        for tentativa in range(1, self.retries + 1):
            try:
                resposta = requests.get(url, headers=headers, timeout=self.timeout)
                resposta.raise_for_status()

                soup = BeautifulSoup(resposta.text, "html.parser")
                elemento = soup.select_one(seletor_css)

                if not elemento:
                    return ScraperResult(
                        False,
                        status="erro_preco_nao_encontrado",
                        mensagem_erro=f"Seletor CSS não encontrado: {seletor_css}",
                    )

                preco_texto = elemento.get_text(strip=True)
                return ScraperResult(True, preco_texto=preco_texto)

            except Timeout:
                logger.warning("Timeout ao acessar %s. Tentativa %s/%s", url, tentativa, self.retries)
                if tentativa == self.retries:
                    return ScraperResult(False, status="erro_timeout", mensagem_erro="Timeout na requisição")
            except RequestException as exc:
                logger.warning("Erro de requisição em %s. Tentativa %s/%s: %s", url, tentativa, self.retries, exc)
                if tentativa == self.retries:
                    return ScraperResult(False, status="erro_site_indisponivel", mensagem_erro=str(exc))
            time.sleep(1)

        return ScraperResult(False, status="erro_site_indisponivel", mensagem_erro="Falha desconhecida na coleta")

    def buscar_com_selenium(self, url: str, seletor_css: str) -> ScraperResult:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-background-networking")
        options.add_argument("--log-level=3")
        options.add_argument(f"user-agent={self.USER_AGENT}")

        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout)
            driver.get(url)

            wait = WebDriverWait(driver, self.timeout)
            elemento = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor_css)))
            preco_texto = (elemento.text or elemento.get_attribute("content") or elemento.get_attribute("aria-label") or "").strip()

            if not preco_texto:
                raise NoSuchElementException("Elemento encontrado, mas sem texto de preço")

            return ScraperResult(True, preco_texto=preco_texto)

        except TimeoutException as exc:
            return ScraperResult(False, status="erro_timeout", mensagem_erro=f"Timeout no Selenium: {exc}")
        except (WebDriverException, NoSuchElementException) as exc:
            return ScraperResult(False, status="erro_preco_nao_encontrado", mensagem_erro=str(exc))
        finally:
            if driver:
                driver.quit()

    def buscar_com_api(self, url: str, caminho_json: str) -> ScraperResult:
        headers = {"User-Agent": self.USER_AGENT, "Accept": "application/json"}

        for tentativa in range(1, self.retries + 1):
            try:
                resposta = requests.get(url, headers=headers, timeout=self.timeout)
                resposta.raise_for_status()
                dados = resposta.json()

                valor = self._buscar_valor_json(dados, caminho_json)
                if valor is None:
                    return ScraperResult(
                        False,
                        status="erro_preco_nao_encontrado",
                        mensagem_erro=f"Caminho JSON não encontrado: {caminho_json}",
                    )
                return ScraperResult(True, preco_texto=str(valor))
            except Timeout:
                if tentativa == self.retries:
                    return ScraperResult(False, status="erro_timeout", mensagem_erro="Timeout na API")
            except (RequestException, ValueError) as exc:
                if tentativa == self.retries:
                    return ScraperResult(False, status="erro_site_indisponivel", mensagem_erro=str(exc))
            time.sleep(1)

        return ScraperResult(False, status="erro_site_indisponivel", mensagem_erro="Falha desconhecida na API")

    def _buscar_valor_json(self, dados: Any, caminho: str):
        atual = dados
        for parte in caminho.split("."):
            if isinstance(atual, dict):
                atual = atual.get(parte)
            elif isinstance(atual, list) and parte.isdigit():
                indice = int(parte)
                atual = atual[indice] if indice < len(atual) else None
            else:
                return None
        return atual
