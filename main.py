import os
import sys
import webbrowser

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QCheckBox, QDateEdit, QMessageBox,
    QListWidget, QListWidgetItem,
    QDialog, QFormLayout, QDialogButtonBox, QSpinBox, QDoubleSpinBox,
    QMainWindow, QApplication, QTableWidget, QTableWidgetItem, QHeaderView, QCompleter
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from contract_view import ContractViewDialog
from db import Database
from contract_form import ContractForm
from notifications import NotificationsWindow

import traceback
from PyQt6.QtWidgets import QMessageBox


class MainWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()

        self.txt_object = None
        self.txt_counterparty = None
        self.txt_number = None
        self.search_filters = None
        self.btn_notifications = None
        self.btn_delete = None
        self.btn_search = None
        self.btn_edit = None
        self.btn_add = None
        self.top_panel = None
        self.cmb_type = None
        self.setWindowTitle("Система учёта договоров — MODTFIL")
        self.setMinimumSize(1100, 700)
        self.showMaximized()

        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        self.db = Database()

        self.user_id = user_id

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.create_top_panel()

        self.create_contract_table()

        self.create_search_filters()

        main_layout.addWidget(self.top_panel)
        main_layout.addWidget(self.search_filters)
        main_layout.addWidget(self.contract_table)

        self.search_filters.hide()

    def create_top_panel(self):
        self.top_panel = QWidget()
        top_layout = QHBoxLayout()
        self.top_panel.setLayout(top_layout)

        # Кнопки
        self.btn_add = QPushButton("📝 Добавить договор")
        self.btn_edit = QPushButton("🖍️ Редактировать договор")
        self.btn_delete = QPushButton("🗑️ Удалить договор")
        self.btn_search = QPushButton("🔍 Поиск")
        self.btn_notifications = QPushButton("🔔 Уведомления")
        self.btn_view_contract = QPushButton("👁 Просмотреть договор")


        # Подключаем обработчики
        self.btn_add.clicked.connect(self.show_add_contract_dialog)
        self.btn_edit.clicked.connect(self.show_edit_contract_dialog)
        self.btn_delete.clicked.connect(self.delete_contract)
        self.btn_search.clicked.connect(self.toggle_search_filters)
        self.btn_notifications.clicked.connect(self.show_notifications)
        self.btn_view_contract.clicked.connect(self.view_contract)


        # Добавляем кнопки в макет
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_edit)
        top_layout.addWidget(self.btn_delete)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_search)
        top_layout.addWidget(self.btn_notifications)
        top_layout.addWidget(self.btn_view_contract)
        
    # Создает таблицу с договорами
    def create_contract_table(self):
        self.contract_table = QTableWidget()
        self.contract_table.setColumnCount(6)
        self.contract_table.setHorizontalHeaderLabels([
            "ID", "Номер договора", "Тип", "Контрагент", "Объект", "Дата подписания"
        ])
        self.contract_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.load_contracts()
        
    # Загружает договоры из базы данных в таблицу
    def load_contracts(self):
        contracts = self.db.get_all_contracts()
        self.contract_table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            self.contract_table.setItem(row, 0, QTableWidgetItem(str(contract["id_contract"])))
            self.contract_table.setItem(row, 1, QTableWidgetItem(contract["number_contract"]))
            self.contract_table.setItem(row, 2, QTableWidgetItem(contract["name_type"]))
            self.contract_table.setItem(row, 3, QTableWidgetItem(contract["name_counterparty"]))
            self.contract_table.setItem(row, 4, QTableWidgetItem(contract["name_object"]))
            self.contract_table.setItem(row, 5, QTableWidgetItem(str(contract["start_date"])))
            
    # Показывает диалог добавления договора
    def show_add_contract_dialog(self):
        try:
            dialog = ContractForm(self.db, parent=self, current_user_id=self.user_id)
            dialog.exec()
            self.load_contracts()
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)  # вывод в консоль
            QMessageBox.critical(self, "Ошибка при открытии формы", f"Произошла ошибка:\n{e}\n\nПодробности в консоли.")

    # Показывает диалог редактирования договора
    def show_edit_contract_dialog(self):
        try:
            selected_items = self.contract_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Ошибка", "Выберите договор для редактирования.")
                return

            contract_id = selected_items[0].text()
            contract = self.db.get_contract_by_id(contract_id)

            dialog = ContractForm(self.db, contract=contract, parent=self, current_user_id = self.user_id)
            dialog.exec()
            self.load_contracts()

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(tb)
            QMessageBox.critical(self, "Ошибка при редактировании", f"{e}\n\nПодробнее см. консоль.")

    # Удаляет выбранный договор
    def delete_contract(self):
        selected_row = self.contract_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите договор для удаления.")
            return

        contract_id = int(self.contract_table.item(selected_row, 0).text())
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы действительно хотите удалить этот договор?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_contract(contract_id)
            self.load_contracts()
    
    # Создает виджет с фильтрами поиска
    def create_search_filters(self):
        self.search_filters = QWidget()
        search_layout = QVBoxLayout()
        self.search_filters.setLayout(search_layout)

        self.txt_number = QLineEdit()
        self.txt_number.setPlaceholderText("Номер договора")

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("Все типы")
        types = [t["name_type"] for t in self.db.get_types()]
        for t in types:
            self.cmb_type.addItem(t)

        self.txt_counterparty = QLineEdit()
        self.txt_counterparty.setPlaceholderText("Контрагент")

        self.txt_object = QLineEdit()
        self.txt_object.setPlaceholderText("Объект")

        # Автоподсказки для контрагентов
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("SELECT name_counterparty FROM counterparty")
                counterparties = [row[0] for row in cur.fetchall()]
            completer_cp = QCompleter(counterparties)
            completer_cp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.txt_counterparty.setCompleter(completer_cp)
        except Exception as e:
            print(f"[Ошибка автоподстановки контрагентов]: {e}")

        # Автоподсказки для объектов
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("SELECT name_object FROM object")
                objects = [row[0] for row in cur.fetchall()]
            completer_obj = QCompleter(objects)
            completer_obj.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.txt_object.setCompleter(completer_obj)
        except Exception as e:
            print(f"[Ошибка автоподстановки объектов]: {e}")

        # Кнопки фильтрации
        btn_search = QPushButton("🔎 Найти")
        btn_clear = QPushButton("🧹 Очистить фильтры")

        btn_search.clicked.connect(self.on_search)
        btn_clear.clicked.connect(self.on_clear)

        # Размещение фильтров
        filter_layout = QHBoxLayout()
        for w in [self.txt_number, self.cmb_type, self.txt_counterparty, self.txt_object, btn_search, btn_clear]:
            filter_layout.addWidget(w)
        search_layout.addLayout(filter_layout)
    
    # Показывает или скрывает фильтры поиска
    def toggle_search_filters(self):
        if self.search_filters.isHidden():
            self.search_filters.show()
        else:
            self.search_filters.hide()
    
    # Очищает фильтры и таблицу
    def on_clear(self):
        self.txt_number.clear()
        self.cmb_type.setCurrentIndex(0)
        self.txt_counterparty.clear()
        self.txt_object.clear()
        self.contract_table.setRowCount(0)
        self.load_contracts()
    
    # Поиск договоров по фильтрам
    def on_search(self):
        try:
            results = self.db.search_contract(
                number_contract=self.txt_number.text().strip(),
                name_type=self.cmb_type.currentText().strip(),
                name_counterparty=self.txt_counterparty.text().strip(),
                name_object=self.txt_object.text().strip()
            )

            self.contract_table.setRowCount(0)

            if not results:
                QMessageBox.information(self, "Результаты", "Договоры не найдены.")
                return

            for row_idx, row in enumerate(results):
                self.contract_table.insertRow(row_idx)
                for col_idx, col_name in enumerate(row):
                    self.contract_table.setItem(row_idx, col_idx, QTableWidgetItem(str(row[col_name])))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка поиска", str(e))
    
    # Показывает уведомления
    def show_notifications(self):
        dialog = NotificationsWindow(self.db)
        dialog.exec()

    # просмотр карточки договора
    def view_contract(self):
        selected_items = self.contract_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите договор в таблице.")
            return

        contract_id = selected_items[0].text()
        view_dialog = ContractViewDialog(self.db, contract_id, self)
        view_dialog.exec()