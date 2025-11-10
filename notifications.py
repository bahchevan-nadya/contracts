# -*- coding: utf-8 -*-
# notifications.py — окно уведомлений о сроках договоров, гарантий и удержаний

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialog
from PyQt6.QtCore import Qt
from datetime import date
from datetime import timedelta

class NotificationsWindow(QDialog):
    """Окно отображает уведомления о сроках действия договоров и гарантий"""

    def __init__(self, db):
        super().__init__()
        self.db = db

        self.setWindowTitle("🔔 Уведомления")
        self.resize(1100, 700)

        # Подключаем стили
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Заголовок
        title = QLabel("Уведомления о сроках действия")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Таблица уведомлений
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Тип", "Номер / Название", "Дата окончания", "Комментарий"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Загрузка данных
        self.load_notifications()

    # ----------------------------------------------------------------------

    def load_notifications(self):
        """Загружает уведомления о сроках"""
        self.table.setRowCount(0)

        today = date.today()
        soon = today + timedelta(days=30)

        items = self.db.get_expiring_items(today, soon)
        if not items:
            print("⚠️ Нет уведомлений на ближайшие 30 дней")
            return

        for row_idx, row in enumerate(items):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row.get("category", ""))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row.get("name", ""))))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row.get("end_date", ""))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(row.get("note", ""))))