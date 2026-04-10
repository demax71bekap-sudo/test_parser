import requests
import random
import time
from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """HTTP-клиент с ротацией User-Agent и обработкой ошибок"""

    def __init__(self, config: dict):
        self.config = config
        self.session = requests.Session()
        self.user_agents = config.get("user_agents", [])
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.delay_min = config.get("delay_min", 2)
        self.delay_max = config.get("delay_max", 5)

        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })

    def _get_random_user_agent(self) -> str:
        return random.choice(self.user_agents) if self.user_agents else ""

    def _delay(self):
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
        logger.debug(f"Задержка {delay:.2f} сек")

    def get(self, url: str, headers: Optional[Dict] = None) -> Optional[str]:
        """GET-запрос с обработкой ошибок и повторными попытками"""
        self._delay()

        if headers is None:
            headers = {}

        headers["User-Agent"] = self._get_random_user_agent()

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Запрос [{attempt + 1}/{self.max_retries}]: {url}")
                response = self.session.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"
                logger.info(f"Успешный запрос: {url} (статус {response.status_code})")
                return response.text
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ошибка запроса {url}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"Повторная попытка через {wait_time} сек...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Все попытки исчерпаны для {url}")
                    return None

        return None

    def download_file(self, url: str, save_path: str) -> bool:
        """Скачивание файла (изображения)"""
        self._delay()

        try:
            headers = {"User-Agent": self._get_random_user_agent()}
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Файл сохранён: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка скачивания {url}: {e}")
            return False