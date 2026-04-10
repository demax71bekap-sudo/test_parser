import logging
import os
from datetime import datetime


def setup_logger(name: str, log_file: str = "parser.log", level: str = "INFO") -> logging.Logger:
    """Настройка логгера"""

    # Создание директории для логов
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Очистка существующих обработчиков
    logger.handlers.clear()

    # Формат сообщений
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Файловый обработчик
    file_handler = logging.FileHandler(os.path.join("logs", log_file), encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Глобальный логгер
_main_logger = None


def get_logger(name: str) -> logging.Logger:
    """Получение логгера"""
    global _main_logger
    if _main_logger is None:
        _main_logger = setup_logger("ParserApp")
    return _main_logger