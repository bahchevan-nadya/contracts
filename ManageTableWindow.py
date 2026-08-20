from pathlib import Path

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from db import Database
from psycopg2.extras import RealDictCursor
import traceback


class FileField(QWidget):
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None, filters: str = "Все файлы (*);;PDF (*.pdf);;DOCX (*.docx)"):
        super().__init__(parent)
        self._filters = filters
        self.le = QLineEdit()
        self.le.setReadOnly(True)
        self.btn = QPushButton("Выбрать…")
        self.btn.clicked.connect(self.pick_file)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.le)
        lay.addWidget(self.btn)

    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл", "", self._filters)
        if path:
            self.le.setText(path)
            self.path_changed.emit(path)

    def value(self) -> str:
        return self.le.text()

    def file_bytes(self) -> bytes | None:
        p = self.value()
        return Path(p).read_bytes() if p else None

class AddRecordDialog(QDialog):
    def __init__(self, columns, table_name, parent=None, opt=None, db_instane=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление записи")
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        self.inputs = {}
        self.table_name = table_name
        self.db = db_instane

        layout = QVBoxLayout()

        for col in columns:
            pk_name = self.db._get_primary_key(self.table_name)
            if pk_name and col == pk_name:
                continue

            label = QLabel(col)
            try:
                if self._is_date_field(col):
                    edit = QDateEdit()
                    edit.setCalendarPopup(True)
                    edit.setDate(QDate.currentDate())
                    edit.setDisplayFormat("dd.MM.yyyy")
                elif col in ["file_agreement", "file_contract"]:
                    edit = FileField()
                else:
                    foreign_key_table = self.db.get_foreign_key_reference(self.table_name, col)
                    if foreign_key_table:
                        edit = QComboBox()
                        options = self.db.get_foreign_key_values(foreign_key_table)
                        for id_value, display_text in options:
                            edit.addItem(f"{id_value} - {display_text}")
                    else:
                        edit = QLineEdit()
            except Exception as e:
                print(f"⚠️ Ошибка при создании поля {col}: {e}")
                edit = QLineEdit()

            self.inputs[col] = edit
            layout.addWidget(label)
            layout.addWidget(edit)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.accept)
        layout.addWidget(self.btn_save)
        self.setLayout(layout)
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.adjustSize()

    def _is_auto_increment_field(self, column_name):
        return column_name.lower() == 'id'

    def _is_date_field(self, column_name):
        date_indicators = ['date', 'срок', 'дата', 'подписания', 'создания', 'term']
        return any(indicator in column_name.lower() for indicator in date_indicators)

    def get_data(self):
        data = {}
        for col, inp in self.inputs.items():
            if isinstance(inp, QDateEdit):
                data[col] = inp.date().toString("yyyy-MM-dd")
            elif isinstance(inp, QComboBox):
                current_text = inp.currentText()
                if current_text:
                    parts = current_text.split(' - ')
                    data[col] = int(parts[0])
            elif isinstance(inp, FileField):
                data[col] = inp.value()
            else:
                data[col] = inp.text().strip()
        return data

class ManageTableWindow(QDialog):

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_table = None
        self.setWindowTitle("Управление таблицами")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Выбор таблицы
        self.table_selector = QComboBox()
        self.tables = [
            "addagreement", "bank_guarent", "contract", "counterparty", "guarent_contract",
            "object", "object_counterparty", "role", "type", "type_guarent", "users", "warrantyretention"
        ]
        self.table_selector.addItems(self.tables)
        self.table_selector.currentIndexChanged.connect(self.load_table_data)
        main_layout.addWidget(self.table_selector)

        # Таблица данных
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.clicked.connect(self.load_table_data)
        self.btn_add = QPushButton("Добавить запись")
        self.btn_add.clicked.connect(self.add_record)
        self.btn_edit = QPushButton("Редактировать запись")
        self.btn_edit.clicked.connect(self.edit_record)
        self.btn_delete = QPushButton("Удалить запись")
        self.btn_delete.clicked.connect(self.delete_record)

        for btn in [self.btn_refresh, self.btn_add, self.btn_edit, self.btn_delete]:
            btn_layout.addWidget(btn)
        main_layout.addLayout(btn_layout)

        # Загрузка первой таблицы
        self.load_table_data()

    def load_table_data(self):
        try:
            self.current_table = self.table_selector.currentText()
            records = self.db.get_table_records (self.current_table)
            headers = list(records[0].keys()) if records else []
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(len(records))

            for row_idx, record in enumerate(records):
                for col_idx, header in enumerate(headers):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(record.get(header, ""))))
            self.table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки таблицы", str(e))

    def selected_record_id(self):
        selection = self.table.selectionModel().selectedRows()
        if not selection:
            return None
        row = selection[0].row()
        for col in range(self.table.columnCount()):
            if self.table.horizontalHeaderItem(col).text().lower().startswith("id"):
                return self.table.item(row, col).text()
        return None

    def add_record(self):
        try:
            table = self.current_table
            columns = self.db.get_table_columns(table)

            editable_columns = [col for col in columns if not self._is_auto_increment_field(col)]

            if not editable_columns:
                QMessageBox.warning(self, "Ошибка", "Нет полей для редактирования в этой таблице.")
                return

            dialog = AddRecordDialog(editable_columns, table, parent=self, db_instane=self.db)
            if dialog.exec():
                data = dialog.get_data()

                for field, value in data.items():
                    if value == "" and self._is_required_field(field):
                        QMessageBox.warning(self, "Ошибка", f"Поле '{field}' обязательно для заполнения.")
                        return

                if self.db.insert_record(table, data):
                    QMessageBox.information(self, "✅ Успех", "Запись добавлена.")
                    self.load_table_data()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка добавления", str(e))
            print(traceback.format_exc())

    def _is_auto_increment_field(self, column_name):
        return column_name.lower() == 'id'

    def _is_required_field(self, column_name):
        return False

    def edit_record(self):
        try:
            record_id = self.selected_record_id()
            if not record_id:
                QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования.")
                return

            data = self.collect_input_data()
            if self.db.update_record(self.current_table, record_id, data):
                self.load_table_data()
                QMessageBox.information(self, "Успех", "Запись успешно отредактирована.")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось отредактировать запись.")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(tb)
            QMessageBox.critical(self, "Ошибка", str(e))

    def delete_record(self):
        record_id = self.selected_record_id()
        if not record_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления.")
            return
        if self.db.delete_record(self.current_table, record_id):
            self.load_table_data()

    def collect_input_data(self):
        data = {}
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            item = self.table.item(self.table.currentRow(), col)
            if header.lower().startswith("id"):  # не редактируем id
                continue
            if item:
                data[header] = item.text()
        return data