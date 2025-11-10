# -*- coding: utf-8 -*-
# Окно авторизации пользователей (вход в систему)

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

from main import MainWindow  # импортируем главное окно
from intermediate_window import IntermediateWindow
from db import Database  # импортируем класс работы с БД


class LoginWindow(QWidget):
    """Окно входа в приложение"""
    login_success = pyqtSignal(dict) # сигнал с данными пользователя

    def __init__(self):
        super().__init__()  # инициализация базового класса QWidget
        self.db = Database()  # создаем экземпляр подключения к БД

        self.setWindowTitle("Вход в систему MODTFIL")  # заголовок окна
        self.setFixedSize(400, 300)  # фиксированный размер окна
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())  # подключаем стили

        # создаем метку-заголовок
        self.lbl_title = QLabel("Система учёта договоров")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        # поле ввода логина
        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Логин")

        # поле ввода пароля
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Пароль")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)  # скрывает символы

        # чекбокс "Показать пароль"
        self.check_show_passwd = QCheckBox("Показать пароль")
        self.check_show_passwd.stateChanged.connect(self.toggle_password_visibility)

        # кнопка входа
        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.login_user)  # обработчик нажатия

        # собираем элементы в вертикальный макет
        vbox = QVBoxLayout()
        vbox.addWidget(self.lbl_title)
        vbox.addStretch()
        vbox.addWidget(self.input_login)
        vbox.addWidget(self.input_password)
        vbox.addWidget(self.check_show_passwd)  # размещаем чекбокс ниже строки пароля
        vbox.addWidget(self.btn_login)
        vbox.addStretch()
        self.setLayout(vbox)

    def toggle_password_visibility(self, state):
        """Обработчик изменения состояния чекбокса 'Показать пароль'"""
        if state == Qt.CheckState.Checked.value:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

    def login_user(self):
        """Проверка логина и пароля пользователя"""
        login = self.input_login.text().strip()
        password = self.input_password.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return

        user = self.db.get_user_by_credentials(login, password)
        if user:
            QMessageBox.information(self, "Успех", f"Добро пожаловать, {user['name_user']}!")

            # Проверяем роль пользователя
            if user["role"] == "Администратор":
                # Показываем промежуточное окно для администратора
                self.intermediate_window = IntermediateWindow(db=self.db, user_id=user["id_user"])
                self.intermediate_window.show()
            else:
                # Обычные пользователи переходят в основное приложение
                self.main_window = MainWindow(user)
                self.main_window.show()

            # Закрываем окно авторизации
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")