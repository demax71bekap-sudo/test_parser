from bs4 import BeautifulSoup
import re
import html


def clean_html(html_text: str) -> str:
    """
    Очистка HTML до чистого текста
    - Удаляет все теги
    - Нормализует пробелы
    - Декодирует HTML-сущности
    """
    if not html_text:
        return ""

    # Парсинг HTML
    soup = BeautifulSoup(html_text, "lxml")

    # Удаление скриптов и стилей
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Получение текста
    text = soup.get_text(separator=" ", strip=True)

    # Декодирование HTML-сущностей
    text = html.unescape(text)

    # Нормализация пробелов
    text = re.sub(r"\s+", " ", text)

    # Удаление невидимых символов
    text = re.sub(r"[\u200b-\u200d\ufeff]", "", text)

    return text.strip()


def normalize_whitespace(text: str) -> str:
    """Нормализация пробелов в тексте"""
    return re.sub(r"\s+", " ", text).strip()