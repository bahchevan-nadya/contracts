import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QFont, QRegularExpressionValidator


class AdminPanel(QWidget):

    def __init__(self, db):
        super().__init__()

        self.db = db

        self.setWindowTitle("Панель администратора — управление пользователями")
        self.resize(1000, 600)
        self.setMinimumSize(800, 500)
        self.showMaximized()

        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        self.lbl_title = QLabel("Управление пользователями")
        self.lbl_title.setObjectName("TitleLabel")
        self.lbl_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Таблица пользователей
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Фамилия", "Имя", "Отчество", "Телефон", "Логин", "Должность"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.load_users()

        self.input_last_name = QLineEdit()
        self.input_last_name.setPlaceholderText("Фамилия")

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Имя")

        self.input_partronymic = QLineEdit()
        self.input_partronymic.setPlaceholderText("Отчество")

        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("Телефон")

        self.input_phone.setInputMask("+7(000)000-00-00;_")

        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Логин")

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Пароль")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.input_role = QLineEdit()
        self.input_role.setPlaceholderText("Должность")

        # Кнопки
        self.btn_add = QPushButton("Добавить пользователя")
        self.btn_add.clicked.connect(self.add_user)  # обработчик кнопки добавления

        self.btn_delete = QPushButton("Удалить пользователя")
        self.btn_delete.clicked.connect(self.delete_user)  # обработчик кнопки удаления

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)

        form_layout = QHBoxLayout()
        form_layout.addWidget(self.input_last_name)
        form_layout.addWidget(self.input_name)
        form_layout.addWidget(self.input_partronymic)
        form_layout.addWidget(self.input_phone)
        form_layout.addWidget(self.input_login)
        form_layout.addWidget(self.input_password)
        form_layout.addWidget(self.input_role)
        form_layout.addWidget(self.btn_add)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_delete)
        button_layout.addWidget(self.btn_close)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.lbl_title)
        main_layout.addWidget(self.table)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    # Загрузка всех пользователей
    def load_users(self):
        users = self.db.get_all_users()  # получаем список из db.py
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user["id_user"])))
            self.table.setItem(row, 1, QTableWidgetItem(user["last_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(user["name_user"]))
            self.table.setItem(row, 3, QTableWidgetItem(user["partronymic"]))
            self.table.setItem(row, 4, QTableWidgetItem(user["phone"]))
            self.table.setItem(row, 5, QTableWidgetItem(user["login"]))
            self.table.setItem(row, 6, QTableWidgetItem(user["role"]))

    # Добавление пользователя
    def add_user(self):
        last_name = self.input_last_name.text().strip()
        name_user = self.input_name.text().strip()
        partronymic = self.input_partronymic.text().strip()
        phone = self.input_phone.text().strip()
        login = self.input_login.text().strip()
        password = self.input_password.text().strip()
        role_name = self.input_role.text().strip()

        if not all([last_name, name_user, partronymic, phone, login, password, role_name]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if not all(s.isalpha() for s in [last_name, name_user, partronymic, role_name]):
            QMessageBox.warning(self, "Ошибка", "ФИО и должность должны содержать только буквы!")
            return

        digits_only = re.sub(r'\D', '', phone)  # убираем всё, кроме цифр
        if not digits_only.isdigit():
            QMessageBox.warning(self, "Ошибка", "Телефон должен содержать только цифры!")
            return

        pattern = r'^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$'
        if not re.fullmatch(pattern, phone):
            QMessageBox.warning(self, "Ошибка", "Телефон должен быть в формате +7(XXX)XXX-XX-XX")
            return

        existing = self.db.check_user(login, password=None)
        if existing:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует.")
            return

        role_id = self.db.get_type_id_by_name(role_name)
        if role_id is None:
            role_id = self.db.add_role(role_name)
            if role_id is None:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить роль.")
                return

        success = self.db.add_user(last_name, name_user, partronymic, phone, login, password, role_id)
        if success:
            QMessageBox.information(self, "Успех", f"Пользователь {login} добавлен.")
            self.load_users()
            self.input_last_name.clear()
            self.input_name.clear()
            self.input_partronymic.clear()
            self.input_phone.clear()
            self.input_login.clear()
            self.input_password.clear()
            self.input_role.clear()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось добавить пользователя.")

    # Удаление пользователя
    def delete_user(self):
        selected = self.table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления.")
            return

        user_id = int(self.table.item(selected, 0).text())
        login = self.table.item(selected, 4).text()

        if login == "admin":
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить администратора!")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить пользователя {login}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.delete_user(user_id)
            if success:
                QMessageBox.information(self, "Удалено", f"Пользователь {login} успешно удалён.")
                self.load_users()  # обновляем таблицу
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить пользователя.")