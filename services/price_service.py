import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class PriceService:
    @staticmethod
    def converter_preco_brasileiro(valor) -> Decimal:
        """Converte strings como 'R$ 1.299,90' para Decimal('1299.90')."""
        if valor is None:
            raise ValueError("Preço vazio")

        if isinstance(valor, (int, float, Decimal)):
            return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        texto = str(valor).strip()
        texto = texto.replace("\xa0", " ")
        texto = re.sub(r"[^0-9,.-]", "", texto)

        if not texto:
            raise ValueError("Preço não possui números")

        # Caso brasileiro: 1.299,90
        if "," in texto and "." in texto:
            texto = texto.replace(".", "").replace(",", ".")
        # Caso brasileiro simples: 299,90
        elif "," in texto:
            texto = texto.replace(",", ".")

        try:
            return Decimal(texto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError(f"Preço inválido: {valor}") from exc

    @staticmethod
    def calcular_queda_percentual(preco_anterior: Decimal, preco_atual: Decimal) -> Decimal:
        if preco_anterior is None or preco_atual is None:
            return Decimal("0.00")
        preco_anterior = Decimal(preco_anterior)
        preco_atual = Decimal(preco_atual)
        if preco_anterior <= 0 or preco_atual >= preco_anterior:
            return Decimal("0.00")
        queda = ((preco_anterior - preco_atual) / preco_anterior) * Decimal("100")
        return queda.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def formatar_moeda(valor) -> str:
        if valor is None:
            return "-"
        valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        texto = f"R$ {valor:,.2f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")
