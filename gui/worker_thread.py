from PyQt5.QtCore import QThread, pyqtSignal
from typing import Optional
import json
import os
from core.http_client import HTTPClient
from core.nt_rt_parser import NtRtPriceParser
from core.excel_exporter import export_to_excel
from utils.logger import setup_logger


class ParserWorker(QThread):
    """Фоновый поток для парсинга"""

    # Сигналы
    progress = pyqtSignal(int, str)  # процент, сообщение
    log_message = pyqtSignal(str)    # сообщение в лог
    finished = pyqtSignal(str)       # путь к файлу
    error = pyqtSignal(str)          # ошибка

    def __init__(self, source: str, price_url: str, manufacturer_url: str, output_path: str):
        super().__init__()
        self.source = source
        self.price_url = price_url
        self.manufacturer_url = manufacturer_url
        self.output_path = output_path
        self.logger = setup_logger("Worker")
        self._stop_flag = False

    def run(self):
        """Основной метод выполнения"""
        try:
            self.progress.emit(5, "Инициализация...")
            self.log_message.emit(f"Источник: {self.source}")
            self.log_message.emit(f"URL прайса: {self.price_url}")

            # Загрузка конфигурации
            with open("config/settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)

            with open("config/selectors.json", "r", encoding="utf-8") as f:
                selectors = json.load(f)

            http_config = settings.get("http", {})
            profile = selectors.get("nt_rt_default", {}).get("price_page", {})

            # 1. Парсинг прайс-листа
            self.progress.emit(10, "Загрузка прайс-листа...")
            self.log_message.emit("Загрузка страницы прайса...")

            http_client = HTTPClient(http_config)
            parser = NtRtPriceParser(http_client, self.price_url, profile)

            products = parser.fetch_and_parse()

            if not products:
                self.log_message.emit("❌ Товары не найдены")
                self.error.emit("Товары не найдены")
                return

            self.log_message.emit(f"✅ Найдено товаров: {len(products)}")

            # Сохранение очереди
            os.makedirs("data", exist_ok=True)
            with open("data/queue.json", "w", encoding="utf-8") as f:
                json.dump({
                    "source": self.source,
                    "count": len(products),
                    "products": [p.to_dict() for p in products]
                }, f, ensure_ascii=False, indent=2)

            self.progress.emit(50, f"Найдено {len(products)} товаров")
            self.log_message.emit(f"Очередь сохранена: data/queue.json")

            # 2. Детальный парсинг (упрощённая версия для этапа 1)
            self.progress.emit(60, "Сбор деталей...")
            self.log_message.emit("Парсинг деталей товаров (этап 2)...")

            # 3. Экспорт в Excel
            self.progress.emit(80, "Экспорт в Excel...")
            self.log_message.emit("Сохранение результата...")

            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            success = export_to_excel(products, self.output_path)

            if success:
                self.progress.emit(100, "Готово!")
                self.log_message.emit(f"✅ Файл сохранён: {self.output_path}")
                self.finished.emit(self.output_path)
            else:
                self.log_message.emit("❌ Ошибка экспорта")
                self.error.emit("Ошибка экспорта")

        except Exception as e:
            self.logger.error(str(e))
            self.log_message.emit(f"❌ Ошибка: {str(e)}")
            self.error.emit(str(e))

    def stop(self):
        """Остановка парсинга"""
        self._stop_flag = True