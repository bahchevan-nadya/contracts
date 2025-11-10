# contract_view.py — диалог просмотра договора
import os
import webbrowser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                             QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ContractViewDialog(QDialog):
    """Диалог для просмотра карточки договора без возможности редактирования"""

    def __init__(self, db, contract_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.contract_id = contract_id
        self.setWindowTitle("Просмотр договора")
        self.setMinimumSize(800, 900)

        self.init_ui()
        self.load_contract_data()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("Карточка договора (просмотр)")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # --- Основная информация о договоре ---
        main_info_group = QGroupBox("Основная информация")
        main_info_layout = QVBoxLayout()

        # Основные поля договора
        self.lbl_number = QLabel()
        self.lbl_type = QLabel()
        self.lbl_counterparty = QLabel()
        self.lbl_inn = QLabel()
        self.lbl_object = QLabel()
        self.lbl_address = QLabel()
        self.lbl_start_date = QLabel()
        self.lbl_term_date = QLabel()

        for lbl, text in [
            ("Номер договора:", self.lbl_number),
            ("Тип договора:", self.lbl_type),
            ("Контрагент:", self.lbl_counterparty),
            ("ИНН:", self.lbl_inn),
            ("Объект:", self.lbl_object),
            ("Адрес объекта:", self.lbl_address),
            ("Дата подписания:", self.lbl_start_date),
            ("Срок действия:", self.lbl_term_date)
        ]:
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(f"<b>{lbl}</b>"))
            row_layout.addWidget(text)
            main_info_layout.addLayout(row_layout)

        main_info_group.setLayout(main_info_layout)
        layout.addWidget(main_info_group)

        # --- Файл договора ---
        file_group = QGroupBox("Файлы договора")
        file_layout = QVBoxLayout()

        # Основной договор
        contract_file_layout = QHBoxLayout()
        contract_file_layout.addWidget(QLabel("<b>Основной договор:</b>"))
        self.lbl_contract_file = QLabel("Файл не прикреплен")
        self.btn_open_contract_file = QPushButton("📄 Открыть договор")
        self.btn_open_contract_file.clicked.connect(self.open_contract_file)
        self.btn_open_contract_file.setEnabled(False)

        contract_file_layout.addWidget(self.lbl_contract_file)
        contract_file_layout.addWidget(self.btn_open_contract_file)
        contract_file_layout.addStretch()
        file_layout.addLayout(contract_file_layout)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # --- Банковские гарантии ---
        guarantees_group = QGroupBox("Банковские гарантии")
        guarantees_layout = QVBoxLayout()
        self.list_guarantees = QListWidget()
        guarantees_layout.addWidget(self.list_guarantees)
        guarantees_group.setLayout(guarantees_layout)
        layout.addWidget(guarantees_group)

        # --- Гарантийные удержания ---
        retentions_group = QGroupBox("Гарантийные удержания")
        retentions_layout = QVBoxLayout()
        self.list_retentions = QListWidget()
        retentions_layout.addWidget(self.list_retentions)
        retentions_group.setLayout(retentions_layout)
        layout.addWidget(retentions_group)

        # --- Дополнительные соглашения ---
        agreements_group = QGroupBox("Дополнительные соглашения")
        agreements_layout = QVBoxLayout()

        # Информация о выбранном соглашении
        self.lbl_selected_agreement = QLabel("Выберите соглашение из списка")
        self.lbl_selected_agreement.setStyleSheet("color: gray; font-style: italic;")

        # Кнопка открытия файла соглашения
        self.btn_open_agreement_file = QPushButton("📄 Открыть файл соглашения")
        self.btn_open_agreement_file.clicked.connect(self.open_selected_agreement_file)
        self.btn_open_agreement_file.setEnabled(False)

        # Список соглашений
        self.list_agreements = QListWidget()
        self.list_agreements.itemSelectionChanged.connect(self.on_agreement_selection_changed)
        self.list_agreements.itemDoubleClicked.connect(self.open_agreement_file)

        # Layout для кнопки и информации
        agreement_controls_layout = QHBoxLayout()
        agreement_controls_layout.addWidget(self.lbl_selected_agreement)
        agreement_controls_layout.addStretch()
        agreement_controls_layout.addWidget(self.btn_open_agreement_file)

        agreements_layout.addLayout(agreement_controls_layout)
        agreements_layout.addWidget(self.list_agreements)
        agreements_group.setLayout(agreements_layout)
        layout.addWidget(agreements_group)

        # --- Кнопки управления ---
        button_layout = QHBoxLayout()
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_close)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_agreement_selection_changed(self):
        """Обрабатывает изменение выбора соглашения в списке"""
        selected_items = self.list_agreements.selectedItems()
        if selected_items:
            item = selected_items[0]
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.exists(file_path):
                self.lbl_selected_agreement.setText(f"Выбрано: {os.path.basename(file_path)}")
                self.btn_open_agreement_file.setEnabled(True)
            else:
                self.lbl_selected_agreement.setText("Файл соглашения не найден")
                self.btn_open_agreement_file.setEnabled(False)
        else:
            self.lbl_selected_agreement.setText("Выберите соглашение из списка")
            self.btn_open_agreement_file.setEnabled(False)

    def load_contract_data(self):
        """Загружает данные договора для просмотра"""
        try:
            contract = self.db.get_contract_by_id(self.contract_id)
            if not contract:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить данные договора.")
                self.close()
                return

            # Основные поля договора
            self.lbl_number.setText(str(contract.get("number_contract", "")))
            self.lbl_type.setText(contract.get("type_name", ""))
            self.lbl_counterparty.setText(contract.get("counterparty_name", ""))
            self.lbl_inn.setText(str(contract.get("inn", "")))
            self.lbl_object.setText(contract.get("object_name", ""))
            self.lbl_address.setText(contract.get("address", ""))

            # Даты
            start_date = contract.get("start_date")
            term_date = contract.get("term_contract")

            self.lbl_start_date.setText(start_date.strftime("%d.%m.%Y") if start_date else "Не указана")
            self.lbl_term_date.setText(term_date.strftime("%d.%m.%Y") if term_date else "Не указан")

            # Файл договора
            file_contract = contract.get("file_contract")
            if file_contract and os.path.exists(file_contract):
                self.lbl_contract_file.setText(os.path.basename(file_contract))
                self.contract_file_path = file_contract
                self.btn_open_contract_file.setEnabled(True)
            else:
                self.lbl_contract_file.setText("Файл не найден")
                self.btn_open_contract_file.setEnabled(False)

            # Банковские гарантии
            self.load_guarantees(contract.get("bank_guarent", []))

            # Гарантийные удержания
            self.load_retentions(contract.get("warrantyretention", []))

            # Дополнительные соглашения
            self.load_agreements(contract.get("addagreements", []))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {e}")

    def load_guarantees(self, guarantees):
        """Загружает список банковских гарантий"""
        self.list_guarantees.clear()
        if not guarantees:
            self.list_guarantees.addItem("Банковские гарантии отсутствуют")
            return

        if isinstance(guarantees, dict):
            guarantees = [guarantees]

        for bg in guarantees:
            display = f"{bg.get('number_guarent', '')} — {bg.get('type', '')} ({bg.get('start_date', '')} → {bg.get('term_guarent', '')})"
            item = QListWidgetItem(display)
            self.list_guarantees.addItem(item)

    def load_retentions(self, retentions):
        """Загружает список гарантийных удержаний"""
        self.list_retentions.clear()
        if not retentions:
            self.list_retentions.addItem("Гарантийные удержания отсутствуют")
            return

        if isinstance(retentions, dict):
            retentions = [retentions]

        for w in retentions:
            display = f"Сумма: {w.get('amount', 0)} ₽ (до {w.get('term_warrantyretention', '')})"
            item = QListWidgetItem(display)
            self.list_retentions.addItem(item)

    def load_agreements(self, agreements):
        """Загружает список дополнительных соглашений"""
        self.list_agreements.clear()
        if not agreements:
            self.list_agreements.addItem("Дополнительные соглашения отсутствуют")
            return

        if isinstance(agreements, dict):
            agreements = [agreements]

        for ag in agreements:
            number = ag.get('number_agreement', '')
            start_date = ag.get('start_date', '')
            description = ag.get('description', '')
            file_path = ag.get('file_agreement', '')

            display = f"{number} — {start_date} ({description})"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, file_path)

            # Добавляем иконку если файл существует
            if file_path and os.path.exists(file_path):
                item.setToolTip(f"Файл: {os.path.basename(file_path)}\nДвойной клик для открытия")
            else:
                item.setToolTip("Файл не найден")
                item.setForeground(Qt.GlobalColor.red)

            self.list_agreements.addItem(item)

    def open_contract_file(self):
        """Открывает файл основного договора"""
        if hasattr(self, 'contract_file_path') and self.contract_file_path:
            try:
                webbrowser.open(self.contract_file_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл договора:\n{e}")

    def open_agreement_file(self, item):
        """Открывает файл дополнительного соглашения при двойном клике"""
        self.open_agreement_file_by_item(item)

    def open_selected_agreement_file(self):
        """Открывает файл выбранного дополнительного соглашения"""
        selected_items = self.list_agreements.selectedItems()
        if selected_items:
            self.open_agreement_file_by_item(selected_items[0])

    def open_agreement_file_by_item(self, item):
        """Открывает файл соглашения по переданному элементу списка"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            try:
                webbrowser.open(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл соглашения:\n{e}")
        else:
            QMessageBox.warning(self, "Ошибка", "Файл дополнительного соглашения не найден")