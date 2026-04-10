from bs4 import BeautifulSoup
from typing import List, Optional
import re
from core.product_model import Product
from core.http_client import HTTPClient
from utils.logger import get_logger

logger = get_logger(__name__)


class NtRtPriceParser:
    """Парсер прайс-листов *.nt-rt.ru/price"""

    def __init__(self, http_client: HTTPClient, base_url: str, selectors: dict):
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")
        self.selectors = selectors

    def fetch_and_parse(self) -> List[Product]:
        """Загрузка и парсинг страницы прайса"""
        html = self.http_client.get(self.base_url)
        if not html:
            logger.error("Не удалось загрузить страницу прайса")
            return []
        return self.parse_html(html)

    def parse_html(self, html: str) -> List[Product]:
        """Парсинг HTML-страницы прайса"""
        soup = BeautifulSoup(html, "lxml")
        products = []
        current_category = ""

        container = soup.select_one(self.selectors.get("container", "div.price__body"))
        if not container:
            logger.error("Контейнер прайса не найден")
            return products

        table = container.select_one(self.selectors.get("table", "table"))
        if not table:
            logger.error("Таблица прайса не найдена")
            return products

        for row in table.select("tbody tr"):
            # Проверка на строку категории
            if row.has_attr("class") and "highlight" in row.get("class", []):
                category_link = row.select_one("a")
                if category_link:
                    current_category = category_link.get_text(strip=True)
                    logger.debug(f"Категория: {current_category}")
                continue

            # Парсинг строки товара
            product = self._parse_product_row(row, current_category)
            if product:
                products.append(product)

        logger.info(f"Найдено товаров: {len(products)}")
        return products

    def _parse_product_row(self, row, category: str) -> Optional[Product]:
        """Парсинг одной строки товара"""
        try:
            # Артикул
            article_el = row.select_one(self.selectors.get("article", "td:nth-child(1)"))
            article = article_el.get_text(strip=True) if article_el else ""
            if not article:
                return None

            # Название и ссылка
            name_link = row.select_one(self.selectors.get("name_link", "td:nth-child(2) a"))
            if not name_link:
                return None

            name = name_link.get_text(separator=" ", strip=True)
            detail_url = name_link.get("href", "")

            # Полная ссылка
            if detail_url and not detail_url.startswith("http"):
                detail_url = self.base_url + detail_url

            # Цена
            price_el = row.select_one(self.selectors.get("price", "td:nth-child(4)"))
            price_text = price_el.get_text(strip=True) if price_el else "0"
            price = self._parse_price(price_text)

            return Product(
                article=article,
                name=name,
                price=price,
                detail_url=detail_url,
                source=self.base_url,
                category=category
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга строки: {e}")
            return None

    def _parse_price(self, text: str) -> float:
        """Преобразование текста цены в float"""
        # "208 999,42 ₽" → 208999.42
        text = re.sub(r"[^\d,]", "", text).replace(",", ".")
        try:
            return float(text) if text else 0.0
        except ValueError:
            logger.warning(f"Не удалось распарсить цену: {text}")
            return 0.0