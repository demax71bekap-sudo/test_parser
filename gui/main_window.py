from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QTextEdit, QProgressBar,
                             QComboBox, QLabel, QFileDialog, QMessageBox,
                             QGroupBox, QFormLayout)
from PyQt5.QtCore import QDateTime, Qt
from gui.worker_thread import ParserWorker
from utils.logger import setup_logger
import json
import os


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.logger = setup_logger("GUI")
        self._init_ui()
        self._load_sources()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("ParserApp — Сбор прайс-листов nt-rt.ru")
        self.setMinimumSize(700, 550)

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        # Группа: Источник
        source_group = QGroupBox("Источник данных")
        source_layout = QFormLayout()

        # Выбор бренда
        self.combo_source = QComboBox()
        self.combo_source.currentTextChanged.connect(self._on_source_changed)
        source_layout.addRow("Бренд:", self.combo_source)

        # URL прайса
        self.edit_price_url = QLineEdit()
        self.edit_price_url.setPlaceholderText("https://xxx.nt-rt.ru/price")
        source_layout.addRow("URL прайса:", self.edit_price_url)

        # URL производителя
        self.edit_manuf_url = QLineEdit()
        self.edit_manuf_url.setPlaceholderText("https://manufacturer.com")
        source_layout.addRow("Сайт производителя:", self.edit_manuf_url)

        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # Группа: Экспорт
        export_group = QGroupBox("Экспорт")
        export_layout = QFormLayout()

        # Путь сохранения
        h_layout = QHBoxLayout()
        self.edit_output = QLineEdit()
        self.edit_output.setText("data/output/result.xlsx")
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(40)
        btn_browse.clicked.connect(self._browse_output)
        h_layout.addWidget(self.edit_output)
        h_layout.addWidget(btn_browse)
        export_layout.addRow("Сохранить в:", h_layout)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # Кнопка запуска
        self.btn_start = QPushButton("▶ Запустить парсинг")
        self.btn_start.setFixedHeight(45)
        self.btn_start.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.btn_start.clicked.connect(self._start_parsing)
        layout.addWidget(self.btn_start)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)

        # Лог
        log_group = QGroupBox("Лог операций")
        log_layout = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        log_layout.addWidget(self.log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Статус бар
        self.statusBar().showMessage("Готов к работе")

    def _load_sources(self):
        """Загрузка списка источников из конфига"""
        try:
            with open("config/sources.json", "r", encoding="utf-8") as f:
                sources = json.load(f)

            for key, value in sources.items():
                self.combo_source.addItem(value.get("name", key), key)

            # Выбор первого по умолчанию
            if self.combo_source.count() > 0:
                self._on_source_changed(self.combo_source.currentData())

        except Exception as e:
            self._log(f"Ошибка загрузки конфига: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить config/sources.json:\n{e}")

    def _on_source_changed(self, source_key: str):
        """Обработка смены источника"""
        try:
            with open("config/sources.json", "r", encoding="utf-8") as f:
                sources = json.load(f)

            source = sources.get(source_key, {})
            self.edit_price_url.setText(source.get("price_url", ""))
            self.edit_manuf_url.setText(source.get("manufacturer_url", ""))
            self.edit_output.setText(f"data/output/{source_key}_result.xlsx")

        except Exception as e:
            self._log(f"Ошибка: {e}")

    def _browse_output(self):
        """Выбор пути сохранения"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результат", "", "Excel (*.xlsx)"
        )
        if path:
            self.edit_output.setText(path)

    def _start_parsing(self):
        """Запуск парсинга"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Предупреждение", "Парсинг уже выполняется")
            return

        # Валидация
        price_url = self.edit_price_url.text().strip()
        if not price_url:
            QMessageBox.warning(self, "Ошибка", "Укажите URL прайс-листа")
            return

        output_path = self.edit_output.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Ошибка", "Укажите путь сохранения")
            return

        # Блокировка интерфейса
        self._set_ui_enabled(False)
        self.progress.setValue(0)
        self.log.clear()

        # Запуск воркера
        self.worker = ParserWorker(
            source=self.combo_source.currentData(),
            price_url=price_url,
            manufacturer_url=self.edit_manuf_url.text().strip(),
            output_path=output_path
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.log_message.connect(self._log)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

        self.statusBar().showMessage("Парсинг запущен...")

    def _on_progress(self, percent: int, message: str):
        """Обновление прогресса"""
        self.progress.setValue(percent)
        self.statusBar().showMessage(message)

    def _log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.log.append(f"[{timestamp}] {message}")
        self.logger.info(message)

    def _on_finished(self, path: str):
        """Завершение успешно"""
        self._set_ui_enabled(True)
        QMessageBox.information(self, "Готово", f"Парсинг завершён!\nФайл сохранён:\n{path}")
        self.statusBar().showMessage("Готов к работе")

    def _on_error(self, message: str):
        """Ошибка парсинга"""
        self._set_ui_enabled(True)
        QMessageBox.critical(self, "Ошибка", f"Ошибка парсинга:\n{message}")
        self.statusBar().showMessage("Ошибка")

    def _set_ui_enabled(self, enabled: bool):
        """Включение/отключение интерфейса"""
        self.btn_start.setEnabled(enabled)
        self.combo_source.setEnabled(enabled)
        self.edit_price_url.setEnabled(enabled)
        self.edit_manuf_url.setEnabled(enabled)
        self.edit_output.setEnabled(enabled)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Выход",
                "Парсинг выполняется. Прервать и выйти?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()