#!/usr/bin/env python3
"""
ParserApp — Универсальный парсер прайс-листов nt-rt.ru
Версия: 1.0
"""

import sys
import os


def is_pyinstaller():
    """Проверка запуска из EXE"""
    return getattr(sys, "frozen", False)


def get_app_path():
    """Получение пути к ресурсам"""
    if is_pyinstaller():
        return sys._MEIPASS
    return os.path.abspath(".")


def main():
    """Точка входа"""
    # Настройка пути к ресурсам
    app_path = get_app_path()
    os.chdir(app_path)

    # Создание необходимых директорий
    os.makedirs("config", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Запуск GUI
    from PyQt5.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("ParserApp")
    app.setOrganizationName("ParserApp")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()