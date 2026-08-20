from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

from main import MainWindow
from intermediate_window import IntermediateWindow
from db import Database


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.db = Database()

        self.setWindowTitle("Вход в систему MODTFIL")
        self.setFixedSize(400, 300)
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        self.lbl_title = QLabel("Система учёта договоров")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Логин")

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Пароль")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.check_show_passwd = QCheckBox("Показать пароль")
        self.check_show_passwd.stateChanged.connect(self.toggle_password_visibility)

        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.login_user)

        vbox = QVBoxLayout()
        vbox.addWidget(self.lbl_title)
        vbox.addStretch()
        vbox.addWidget(self.input_login)
        vbox.addWidget(self.input_password)
        vbox.addWidget(self.check_show_passwd)
        vbox.addWidget(self.btn_login)
        vbox.addStretch()
        self.setLayout(vbox)

    def toggle_password_visibility(self, state):
        if state == Qt.CheckState.Checked.value:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

    def login_user(self):
        login = self.input_login.text().strip()
        password = self.input_password.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return

        user = self.db.get_user_by_credentials(login, password)
        if user:
            QMessageBox.information(self, "Успех", f"Добро пожаловать, {user['name_user']}!")

            if user["role"] == "Администратор":
                self.intermediate_window = IntermediateWindow(db=self.db, user_id=user["id_user"])
                self.intermediate_window.show()
            else:
                self.main_window = MainWindow(user)
                self.main_window.show()

            self.close()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")