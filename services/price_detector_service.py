import json
import logging
import re
from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests import RequestException, Timeout
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException

from services.price_service import PriceService

logger = logging.getLogger(__name__)


@dataclass
class PrecoCandidato:
    preco_texto: str
    preco_decimal: str
    origem: str
    seletor_sugerido: str = "auto"
    estrategia_sugerida: str = "auto"
    confianca: str = "media"

    def to_dict(self):
        return asdict(self)


class PriceDetectorService:
    """
    Serviço para o modo simples.

    Ele tenta encontrar preços automaticamente sem exigir que o usuário saiba CSS.
    A ordem de busca privilegia fontes mais confiáveis:
    1. JSON-LD/dados estruturados;
    2. meta tags comuns de produto;
    3. seletores conhecidos de preço;
    4. padrões de texto como R$ 419,00.
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )

    REGEX_PRECO_BR = re.compile(r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?")
    REGEX_PRECO_COMUM = re.compile(r"(?<!\d)\d{1,3}(?:\.\d{3})*,\d{2}(?!\d)")

    SELETORES_PRECO = [
        '[data-andes-money-amount-fraction="true"]',
        '.andes-money-amount__fraction',
        '.andes-money-amount__cents',
        '[itemprop="price"]',
        'meta[itemprop="price"]',
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        '[data-testid*="price" i]',
        '[data-test*="price" i]',
        '[class*="price" i]',
        '[class*="preco" i]',
        '[class*="valor" i]',
    ]

    def __init__(self, timeout=10, retries=3):
        self.timeout = int(timeout)
        self.retries = int(retries)

    def detectar_precos(self, url: str, usar_selenium: bool = False, limite: int = 10) -> list[PrecoCandidato]:
        html = self._baixar_html_requests(url)
        candidatos: list[PrecoCandidato] = []

        if html:
            soup = BeautifulSoup(html, "html.parser")
            candidatos.extend(self._detectar_json_ld(soup))
            candidatos.extend(self._detectar_meta_tags(soup))
            candidatos.extend(self._detectar_por_seletores(soup))
            candidatos.extend(self._detectar_por_regex(soup.get_text(" ", strip=True)))

        # Selenium fica como reforço, não como primeira opção, porque é mais pesado.
        if usar_selenium and not candidatos:
            html_selenium = self._baixar_html_selenium(url)
            if html_selenium:
                soup = BeautifulSoup(html_selenium, "html.parser")
                candidatos.extend(self._detectar_json_ld(soup))
                candidatos.extend(self._detectar_meta_tags(soup))
                candidatos.extend(self._detectar_por_seletores(soup, estrategia="selenium"))
                candidatos.extend(self._detectar_por_regex(soup.get_text(" ", strip=True), estrategia="selenium"))

        return self._deduplicar_e_ordenar(candidatos)[:limite]

    def detectar_melhor_preco(self, url: str) -> PrecoCandidato | None:
        candidatos = self.detectar_precos(url=url, usar_selenium=True, limite=1)
        return candidatos[0] if candidatos else None

    def _baixar_html_requests(self, url: str) -> str | None:
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
        for tentativa in range(1, self.retries + 1):
            try:
                resposta = requests.get(url, headers=headers, timeout=self.timeout)
                resposta.raise_for_status()
                return resposta.text
            except Timeout:
                logger.warning("Timeout ao detectar preço em %s. Tentativa %s/%s", url, tentativa, self.retries)
            except RequestException as exc:
                logger.warning("Falha ao detectar preço em %s. Tentativa %s/%s: %s", url, tentativa, self.retries, exc)
        return None

    def _baixar_html_selenium(self, url: str) -> str | None:
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
            return driver.page_source
        except (TimeoutException, WebDriverException) as exc:
            logger.warning("Selenium não conseguiu carregar a página para detecção automática: %s", exc)
            return None
        finally:
            if driver:
                driver.quit()

    def _detectar_json_ld(self, soup: BeautifulSoup) -> list[PrecoCandidato]:
        candidatos: list[PrecoCandidato] = []
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        for script in scripts:
            conteudo = script.string or script.get_text(strip=True)
            if not conteudo:
                continue
            try:
                dados = json.loads(conteudo)
            except json.JSONDecodeError:
                continue
            for valor in self._extrair_precos_json(dados):
                candidato = self._criar_candidato(
                    valor,
                    origem="dados estruturados JSON-LD",
                    seletor="auto",
                    estrategia="auto",
                    confianca="alta",
                )
                if candidato:
                    candidatos.append(candidato)
        return candidatos

    def _extrair_precos_json(self, dados: Any) -> list[Any]:
        encontrados = []
        chaves_preco = {"price", "lowPrice", "highPrice", "salePrice", "priceAmount"}

        if isinstance(dados, dict):
            for chave, valor in dados.items():
                if chave in chaves_preco and isinstance(valor, (str, int, float)):
                    encontrados.append(valor)
                else:
                    encontrados.extend(self._extrair_precos_json(valor))
        elif isinstance(dados, list):
            for item in dados:
                encontrados.extend(self._extrair_precos_json(item))
        return encontrados

    def _detectar_meta_tags(self, soup: BeautifulSoup) -> list[PrecoCandidato]:
        candidatos: list[PrecoCandidato] = []
        seletores = [
            'meta[itemprop="price"]',
            'meta[property="product:price:amount"]',
            'meta[property="og:price:amount"]',
            'meta[name="twitter:data1"]',
        ]
        for seletor in seletores:
            for elemento in soup.select(seletor):
                valor = elemento.get("content") or elemento.get("value") or elemento.get_text(strip=True)
                candidato = self._criar_candidato(
                    valor,
                    origem=f"meta tag {seletor}",
                    seletor=seletor,
                    estrategia="beautifulsoup",
                    confianca="alta",
                )
                if candidato:
                    candidatos.append(candidato)
        return candidatos

    def _detectar_por_seletores(self, soup: BeautifulSoup, estrategia="beautifulsoup") -> list[PrecoCandidato]:
        candidatos: list[PrecoCandidato] = []
        for seletor in self.SELETORES_PRECO:
            try:
                elementos = soup.select(seletor)[:8]
            except Exception:  # noqa: BLE001
                continue

            for elemento in elementos:
                valor = elemento.get("content") or elemento.get("aria-label") or elemento.get_text(" ", strip=True)
                candidato = self._criar_candidato(
                    valor,
                    origem=f"elemento da página: {seletor}",
                    seletor=seletor,
                    estrategia=estrategia,
                    confianca="media",
                )
                if candidato:
                    candidatos.append(candidato)
        return candidatos

    def _detectar_por_regex(self, texto: str, estrategia="auto") -> list[PrecoCandidato]:
        candidatos: list[PrecoCandidato] = []
        encontrados = self.REGEX_PRECO_BR.findall(texto)
        encontrados.extend(self.REGEX_PRECO_COMUM.findall(texto))

        for valor in encontrados[:30]:
            candidato = self._criar_candidato(
                valor,
                origem="texto encontrado automaticamente",
                seletor="auto",
                estrategia=estrategia,
                confianca="baixa",
            )
            if candidato:
                candidatos.append(candidato)
        return candidatos

    def _criar_candidato(self, valor: Any, origem: str, seletor: str, estrategia: str, confianca: str) -> PrecoCandidato | None:
        if valor is None:
            return None
        texto = str(valor).replace("\xa0", " ").strip()
        if not texto:
            return None

        # Alguns elementos trazem frases grandes. Só aproveita se houver número.
        if not re.search(r"\d", texto):
            return None

        try:
            decimal = PriceService.converter_preco_brasileiro(texto)
        except ValueError:
            return None

        # Evita valores muito pequenos que costumam ser parcela/frete, mas mantém R$ 1+.
        if decimal <= Decimal("0.99"):
            return None

        return PrecoCandidato(
            preco_texto=PriceService.formatar_moeda(decimal),
            preco_decimal=str(decimal),
            origem=origem,
            seletor_sugerido=seletor,
            estrategia_sugerida=estrategia,
            confianca=confianca,
        )

    def _deduplicar_e_ordenar(self, candidatos: list[PrecoCandidato]) -> list[PrecoCandidato]:
        pesos = {"alta": 0, "media": 1, "baixa": 2}
        unicos: dict[str, PrecoCandidato] = {}

        for candidato in candidatos:
            chave = candidato.preco_decimal
            existente = unicos.get(chave)
            if not existente or pesos[candidato.confianca] < pesos[existente.confianca]:
                unicos[chave] = candidato

        return sorted(unicos.values(), key=lambda item: (pesos.get(item.confianca, 9), Decimal(item.preco_decimal)))
