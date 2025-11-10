# intermediate_window.py — Промежуточное окно для администраторов

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ManageTableWindow import ManageTableWindow
from admin_panel import AdminPanel
from main import MainWindow


class IntermediateWindow(QWidget):
    """Промежуточное окно для администраторов"""

    def __init__(self, db, user_id):
        super().__init__()

        self.db = db
        self.user_id = user_id
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Меню администратора")
        self.setFixedSize(400, 200)
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        layout = QVBoxLayout()

        title_label = QLabel("Приветствуем администратора!\nЧто желаете сделать?")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)

        btn_manage_users = QPushButton("Управление пользователями")
        btn_manage_users.clicked.connect(self.open_admin_panel)
        layout.addWidget(btn_manage_users)

        btn_manage_tables = QPushButton("Управление таблицами")
        btn_manage_tables.clicked.connect(self.open_main_window)
        layout.addWidget(btn_manage_tables)

        btn_open_app = QPushButton("Открыть приложение")
        btn_open_app.clicked.connect(self.open_app)
        layout.addWidget(btn_open_app)

        self.setLayout(layout)

    def open_admin_panel(self):
        """Открытие панели администратора"""
        self.admin_panel = AdminPanel(self.db)
        self.admin_panel.show()
        # self.close()

    def open_main_window(self):
        self.ManageTableWindow = ManageTableWindow(self.db)
        self.ManageTableWindow.show()
        # self.close()

    def open_app(self):
        self.app = MainWindow(self.user_id)
        self.app.show()