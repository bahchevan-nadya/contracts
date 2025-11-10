import os
import webbrowser

from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDateEdit, QDialogButtonBox, QVBoxLayout, QDoubleSpinBox, \
    QTextEdit, QMessageBox, QFileDialog, QPushButton, QLabel, QWidget, QHBoxLayout, QGroupBox, QComboBox
from PyQt6.QtCore import QDate


class BankGuaranteeDialog(QDialog):
    """Диалог добавления банковской гарантии"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить банковскую гарантию")
        self.resize(400, 350)

        # Сохраняем ссылку на родителя для доступа к БД
        self.parent_window = parent

        # Подключаем стили
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.txt_number = QLineEdit()
        self.txt_number.setPlaceholderText("Введите номер гарантии")

        # Комбобокс для типа гарантии
        self.cmb_type_guarent = QComboBox()
        self.cmb_type_guarent.setEditable(True)
        self.cmb_type_guarent.lineEdit().setPlaceholderText("Выберите или введите тип гарантии")
        self.cmb_type_guarent.lineEdit().setMaxLength(50)

        self.amount = QDoubleSpinBox()
        self.amount.setMaximum(1_000_000_000)
        self.amount.setPrefix("₽ ")
        self.amount.setMinimum(0.01)
        self.amount.setValue(10000.0)

        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate())

        self.date_term = QDateEdit()
        self.date_term.setCalendarPopup(True)
        self.date_term.setDate(QDate.currentDate().addDays(30))

        self.layout.addRow("Номер гарантии:", self.txt_number)
        self.layout.addRow("Тип гарантии:", self.cmb_type_guarent)
        self.layout.addRow("Сумма гарантии:", self.amount)
        self.layout.addRow("Дата начала:", self.date_start)
        self.layout.addRow("Дата окончания:", self.date_term)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        # Загружаем типы гарантий при инициализации
        self.load_type_guarents()

    def load_type_guarents(self):
        """Загружает существующие типы гарантий из базы данных"""
        try:
            self.cmb_type_guarent.clear()

            # Получаем доступ к БД через родительское окно
            if (self.parent_window and
                    hasattr(self.parent_window, 'db') and
                    self.parent_window.db):

                db = self.parent_window.db
                with db.conn.cursor() as cur:
                    cur.execute("SELECT name_type_guarent FROM type_guarent ORDER BY name_type_guarent")
                    types = cur.fetchall()
                    for type_row in types:
                        self.cmb_type_guarent.addItem(type_row[0])

            # Если типов нет в базе или не удалось подключиться, добавляем основные
            if self.cmb_type_guarent.count() == 0:
                default_types = ["Основная", "Дополнительная", "Обеспечительная", "Платежная"]
                for default_type in default_types:
                    self.cmb_type_guarent.addItem(default_type)

        except Exception as e:
            print(f"Ошибка при загрузке типов гарантий: {e}")
            # Добавляем типы по умолчанию при ошибке
            default_types = ["Основная", "Дополнительная", "Обеспечительная", "Платежная"]
            for default_type in default_types:
                self.cmb_type_guarent.addItem(default_type)

    def get_data(self):
        """Возвращает данные из формы"""
        type_guarent = self.cmb_type_guarent.currentText().strip()

        # Если поле пустое, устанавливаем значение по умолчанию
        if not type_guarent:
            type_guarent = "Основная"

        return {
            "number_guarent": self.txt_number.text().strip(),
            "amount": self.amount.value(),
            "type": type_guarent,
            "start_guarent": self.date_start.date().toPyDate(),
            "term_guarent": self.date_term.date().toPyDate()
        }

    def validate_and_accept(self):
        """Обработка нажатия OK с валидацией"""
        data = self.get_data()

        # Валидация данных
        if not data["number_guarent"]:
            QMessageBox.warning(self, "Ошибка", "Введите номер гарантии")
            return

        if data["amount"] <= 0:
            QMessageBox.warning(self, "Ошибка", "Введите сумму гарантии больше 0")
            return

        if data["start_guarent"] >= data["term_guarent"]:
            QMessageBox.warning(self, "Ошибка", "Дата окончания должна быть позже даты начала")
            return

        super().accept()

class WarrantyRetentionDialog(QDialog):
    """Диалог добавления гарантийного удержания"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить гарантийное удержание")
        self.resize(300, 180)

        # Подключаем стили
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.txt_stage = QLineEdit()
        self.amount = QDoubleSpinBox()
        self.amount.setMaximum(1_000_000_000)
        self.amount.setPrefix("₽ ")
        self.date_term = QDateEdit()
        self.date_term.setCalendarPopup(True)
        self.date_term.setDate(QDate.currentDate())

        self.layout.addRow("Этап:", self.txt_stage)
        self.layout.addRow("Сумма:", self.amount)
        self.layout.addRow("Дата окончания:", self.date_term)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def get_data(self):
        return {
            "name_stage": self.txt_stage.text().strip(),
            "amount": self.amount.value(),
            "term_WarrantyRetention": self.date_term.date().toPyDate()
        }

class Add_agreement_dialog(QDialog):
    """Диалоговое окно для добавления дополнительного соглашения"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить дополнительное соглашение")
        self.resize(500, 400)

        # Подключаем стили
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Основная форма
        self.form_layout = QFormLayout()

        self.txt_number = QLineEdit()
        self.txt_number.setPlaceholderText("Введите номер доп. соглашения")

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())

        self.txt_description = QTextEdit()
        self.txt_description.setMaximumHeight(80)
        self.txt_description.setPlaceholderText("Введите описание соглашения...")

        self.form_layout.addRow("Номер доп. соглашения:", self.txt_number)
        self.form_layout.addRow("Дата подписания:", self.start_date)
        self.form_layout.addRow("Описание:", self.txt_description)

        self.layout.addLayout(self.form_layout)

        # --- Блок прикрепления файла ---
        file_group = QGroupBox("Файл дополнительного соглашения")
        file_layout = QVBoxLayout()
        file_group.setLayout(file_layout)

        # Контейнер для кнопки и поля ввода
        file_container = QWidget()
        file_container_layout = QHBoxLayout()
        file_container.setLayout(file_container_layout)

        # Текстовое поле для пути файла (как сейчас)
        self.txt_file_path = QLineEdit()
        self.txt_file_path.setPlaceholderText("Путь к файлу...")

        # Кнопка выбора файла через проводник
        self.btn_browse = QPushButton("Обзор...")
        self.btn_browse.setMinimumHeight(35)
        self.btn_browse.clicked.connect(self.browse_file)

        file_container_layout.addWidget(self.txt_file_path)
        file_container_layout.addWidget(self.btn_browse)

        file_layout.addWidget(file_container)

        self.lbl_file = QLabel("Файл не выбран")
        self.lbl_file.setStyleSheet("color: gray; font-style: italic;")
        file_layout.addWidget(self.lbl_file)

        self.layout.addWidget(file_group)

        # --- Кнопки диалога ---
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def browse_file(self):
        """Открывает проводник для выбора файла"""
        try:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите PDF файл дополнительного соглашения",
                "",
                "PDF Files (*.pdf);;All Files (*)"
            )
            if path:
                self.txt_file_path.setText(path)
                self.selected_file_path = path  # на будущее
                file_name = os.path.basename(path)  # или Path(path).name
                self.lbl_file.setText(f"Выбран файл: {file_name}")
                self.lbl_file.setStyleSheet("color: green; font-style: normal;")
        except Exception as e:
            # Чтобы видеть ошибки, если вдруг что-то ещё упадёт
            import traceback
            traceback.print_exc()


    def get_data(self):
        """Возвращает введённые данные"""
        return {
            "number_agreement": self.txt_number.text().strip(),
            "start_date": self.start_date.date().toPyDate(),
            "description": self.txt_description.toPlainText().strip(),
            "file_agreement": self.txt_file_path.text().strip()  # Берем путь из текстового поля
        }

    def accept(self):
        """Проверка перед закрытием диалога"""
        # Проверяем, что номер соглашения заполнен
        if not self.txt_number.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите номер дополнительного соглашения!")
            return

        # Проверяем, что файл выбран
        if not self.txt_file_path.text().strip():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите файл дополнительного соглашения!")
            return

        # Проверяем, что файл существует
        file_path = self.txt_file_path.text().strip()
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Ошибка", "Выбранный файл не существует!")
            return

        super().accept()