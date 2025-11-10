# contract_form.py — форма создания и редактирования договоров
import os
import webbrowser

import psycopg2
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QCheckBox, QDateEdit, QMessageBox,
    QListWidget, QListWidgetItem, QScrollArea, QDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from dialogs import BankGuaranteeDialog, WarrantyRetentionDialog, Add_agreement_dialog


class ContractForm(QDialog):
    """Форма создания договоров"""

    def __init__(self, db, current_user_id, contract=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_user_id = current_user_id
        # Подключаем стили
        self.setStyleSheet(open("modtfil_app/styles.qss", "r", encoding="utf-8").read())

        self.setWindowTitle("Карточка договора")
        self.setMinimumSize(800, 600)

        self.contract = contract
        self.contract_id = None
        self.file_path = None

        # Основной layout для формы
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Создаем контейнер и layout для содержимого
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)

        # Оборачиваем содержимое в QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)

        # Добавляем scrollArea в основной layout
        self.main_layout.addWidget(self.scroll_area)

        # --- Заголовок ---
        title = QLabel("Карточка договора")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title)

        # ===============================
        # Поля ввода
        # ===============================
        self.cmb_type = QComboBox()
        self.cmb_type.setEditable(True)
        self.cmb_type.lineEdit().setMaxLength(50)
        self.cmb_type.lineEdit().setPlaceholderText("Тип договора (до 50 символов)")
        self.load_types()

        self.txt_number = QLineEdit()
        self.txt_number.setPlaceholderText("Номер договора")

        self.txt_counterparty = QLineEdit()
        self.txt_counterparty.setPlaceholderText("Контрагент")

        self.txt_inn = QLineEdit()
        self.txt_inn.setPlaceholderText("ИНН")

        self.txt_object = QLineEdit()
        self.txt_object.setPlaceholderText("Объект")

        self.txt_address = QLineEdit()
        self.txt_address.setPlaceholderText("Адрес объекта")

        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate())

        self.chk_term = QCheckBox("Есть срок договора")
        self.date_term = QDateEdit()
        self.date_term.setCalendarPopup(True)
        self.date_term.setDate(QDate.currentDate())
        self.date_term.setEnabled(False)
        self.chk_term.stateChanged.connect(lambda state: self.date_term.setEnabled(bool(state)))

        # --- Банковская гарантия ---
        self.chk_guarent = QCheckBox("Добавить банковские гарантии")
        self.btn_add_guarent = QPushButton("➕ Добавить гарантию")
        self.list_guarents = QListWidget()
        self.btn_add_guarent.setVisible(False)
        self.list_guarents.setVisible(False)
        self.chk_guarent.stateChanged.connect(self.toggle_guarents)
        self.btn_add_guarent.clicked.connect(self.add_guarent_entry)

        # --- Гарантийное удержание ---
        self.chk_retention = QCheckBox("Добавить гарантийные удержания")
        self.btn_add_retention = QPushButton("➕ Добавить удержание")
        self.list_retentions = QListWidget()
        self.btn_add_retention.setVisible(False)
        self.list_retentions.setVisible(False)
        self.chk_retention.stateChanged.connect(self.toggle_retentions)
        self.btn_add_retention.clicked.connect(self.add_retention_entry)

        # --- Дополнительное соглашение ---
        self.chk_addagreement = QCheckBox("Есть дополнительное соглашение")
        self.chk_addagreement.stateChanged.connect(self.toggle_add_agreement_section)

        self.btn_add_agreement = QPushButton("➕ Добавить дополнительное соглашение")
        self.btn_add_agreement.setVisible(False)
        self.btn_add_agreement.clicked.connect(self.add_agreement_entry)

        self.list_agreement = QListWidget()
        self.list_agreement.setVisible(False)

        # --- Файл договора ---
        self.btn_file = QPushButton("📎 Прикрепить файл договора (PDF)")
        self.lbl_file = QLabel("Файл не выбран")
        self.btn_file.clicked.connect(self.attach_file)

        # ===============================
        # Компоновка
        # ===============================

        for lbl, field in [
            ("Тип договора:", self.cmb_type),
            ("Номер договора:", self.txt_number),
            ("Контрагент:", self.txt_counterparty),
            ("ИНН:", self.txt_inn),
            ("Объект:", self.txt_object),
            ("Адрес объекта:", self.txt_address),
            ("Дата подписания:", self.date_start),
        ]:
            self.content_layout.addWidget(QLabel(lbl))
            self.content_layout.addWidget(field)

        self.content_layout.addWidget(self.chk_term)
        self.content_layout.addWidget(self.date_term)

        # Блок банковских гарантий
        self.content_layout.addWidget(self.chk_guarent)
        self.content_layout.addWidget(self.btn_add_guarent)
        self.content_layout.addWidget(self.list_guarents)

        # Блок гарантийных удержаний
        self.content_layout.addWidget(self.chk_retention)
        self.content_layout.addWidget(self.btn_add_retention)
        self.content_layout.addWidget(self.list_retentions)

        # Файл договора
        self.content_layout.addWidget(self.btn_file)
        self.content_layout.addWidget(self.lbl_file)

        # Доп. соглашения
        self.content_layout.addWidget(self.chk_addagreement)
        self.content_layout.addWidget(self.btn_add_agreement)
        self.content_layout.addWidget(self.list_agreement)

        # --- Кнопки управления ---
        btns = QHBoxLayout()
        self.btn_save = QPushButton("💾 Сохранить договор")
        self.btn_clear = QPushButton("🧹 Очистить форму")

        for b in [self.btn_save, self.btn_clear]:
            btns.addWidget(b)
        self.content_layout.addLayout(btns)

        # Подключения
        self.btn_save.clicked.connect(self.save_contract)
        self.btn_clear.clicked.connect(self.clear_form)

        # Загружаем данные договора, если он передан
        if self.contract:
            self.load_contract_data(contract)
    # Методы интерфейса
    def load_types(self):
        self.cmb_type.clear()
        for t in self.db.get_types():
            self.cmb_type.addItem(t["name_type"])

    def toggle_guarents(self, state):
        visible = bool(state)
        self.list_guarents.setVisible(visible)
        self.btn_add_guarent.setVisible(visible)

    def toggle_retentions(self, state):
        visible = bool(state)
        self.list_retentions.setVisible(visible)
        self.btn_add_retention.setVisible(visible)

    def toggle_add_agreement_section(self, state):
        visible = bool(state)
        self.btn_add_agreement.setVisible(visible)
        self.list_agreement.setVisible(visible)

    def add_guarent_entry(self):
        """Добавляет банковскую гарантию через диалог"""
        try:
            dialog = BankGuaranteeDialog(self)  # Передаем self как parent

            if dialog.exec():
                data = dialog.get_data()

                # Валидация данных
                if not data["number_guarent"]:
                    QMessageBox.warning(self, "Ошибка", "Номер гарантии не может быть пустым")
                    return

                display = f"{data['number_guarent']} — {data['amount']:,.2f} ₽ ({data['start_guarent']} → {data['term_guarent']}) - {data['type']}"
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, data)
                self.list_guarents.addItem(item)
                print(f"✅ Добавлена гарантия в список: {data['number_guarent']}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить гарантию: {e}")
            print(f"Ошибка в add_guarent_entry: {e}")
            import traceback
            traceback.print_exc()

    def link_guarent_contract(self, contract_id, guarent_id):
        """Связывает гарантию с договором"""
        try:
            with self.conn.cursor() as cur:
                # Простая вставка без ON CONFLICT
                cur.execute("""
                            INSERT INTO guarent_contract (contract_id, guarent_id)
                            VALUES (%s, %s) RETURNING id_guarent_contract
                            """, (contract_id, guarent_id))

                result = cur.fetchone()
                self.conn.commit()

                if result:
                    print(f"✅ Создана связь договора {contract_id} с гарантией {guarent_id}")
                    return True
                else:
                    print(f"❌ Не удалось создать связь договора {contract_id} с гарантией {guarent_id}")
                    return False

        except psycopg2.IntegrityError:
            # Если связь уже существует (нарушение уникальности)
            print(f"ℹ️ Связь договора {contract_id} с гарантией {guarent_id} уже существует")
            self.conn.rollback()
            return True
        except Exception as e:
            print(f"[Ошибка] link_guarent_contract: {e}")
            self.conn.rollback()
            return False

    def add_retention_entry(self):
        dialog = WarrantyRetentionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            display = f"{data['name_stage']} — {data['amount']} ₽ (до {data['term_WarrantyRetention']})"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, data)
            self.list_retentions.addItem(item)

    def add_agreement_entry(self):
        """Открывает диалог для добавления дополнительного соглашения"""
        try:
            dialog = Add_agreement_dialog(self)
            if dialog.exec():
                data = dialog.get_data()

                # Проверяем, чтобы поля не были пустыми
                if not data["number_agreement"]:
                    QMessageBox.warning(self, "Ошибка", "Заполните номер дополнительного соглашения.")
                    return

                # Проверяем, что файл выбран
                if not data["file_agreement"]:
                    QMessageBox.warning(self, "Ошибка", "Пожалуйста, прикрепите PDF-файл доп. соглашения.")
                    return

                # Отображаем в списке
                display = f"{data['number_agreement']} — {data['start_date']} ({data['description']})"
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, data)
                self.list_agreement.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии диалога: {e}")

    def attach_file(self):
        """Прикрепление файла основного договора через проводник"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите PDF файл договора",
            "",
            "PDF Files (*.pdf)"
        )
        if path:
            self.file_path = path
            self.lbl_file.setText(os.path.basename(path))
            print(f"DEBUG: Выбран файл договора: {path}")

    def clear_form(self):
        self.txt_number.clear()
        self.txt_counterparty.clear()
        self.txt_inn.clear()
        self.txt_object.clear()
        self.txt_address.clear()
        self.chk_term.setChecked(False)
        self.chk_guarent.setChecked(False)
        self.chk_retention.setChecked(False)
        self.chk_addagreement.setChecked(False)
        self.list_guarents.clear()
        self.list_retentions.clear()
        self.list_agreement.clear()
        self.lbl_file.setText("Файл не выбран")
        self.file_path = None
        self.contract_id = None

    # ----------------------------------------------------------------------
    # Работа с БД
    # ----------------------------------------------------------------------

    def save_contract(self):
        """Сохраняет или обновляет договор и все связанные объекты"""
        try:
            # --- Сбор данных ---
            number_contract = self.txt_number.text().strip()
            counterparty_name = self.txt_counterparty.text().strip()
            inn = self.txt_inn.text().strip()
            object_name = self.txt_object.text().strip()
            address = self.txt_address.text().strip()
            type_name = self.cmb_type.currentText().strip()
            start_date = self.date_start.date().toPyDate()
            term_contract = self.date_term.date().toPyDate() if self.chk_term.isChecked() else None

            # Проверяем, что файл прикреплен
            if not self.file_path:
                QMessageBox.warning(self, "Ошибка", "Пожалуйста, прикрепите PDF-файл договора!")
                return

            file_contract = self.file_path  # путь к файлу

            if not number_contract or not counterparty_name or not inn:
                QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля: Номер, Контрагент, ИНН!")
                return

            # --- Контрагент ---
            counterparty_id = self.db.get_counterparty_id_by_inn(inn)

            if getattr(self, "is_edit_mode", False):
                # режим редактирования
                if not counterparty_id:
                    # Если почему-то не нашли по ИНН — попробуем по имени
                    counterparty_id = self.db.get_counterparty_id_by_name(counterparty_name)
                if not counterparty_id:
                    # Если всё равно не нашли — просто оставляем старого
                    counterparty_id = self.contract.get("counterparty_id")
                else:
                    # Если нашли, можно обновить имя или ИНН, если нужно
                    self.db.update_counterparty(counterparty_id, counterparty_name, inn)
            else:
                # режим добавления нового договора
                if not counterparty_id:
                    counterparty_id = self.db.add_counterparty(counterparty_name, inn)

            # --- Тип договора ---
            type_id = self.db.get_type_id_by_name(type_name)
            if not type_id:
                self.db.add_type(type_name)
                type_id = self.db.get_type_id_by_name(type_name)

            # --- Объект ---
            if getattr(self, "is_edit_mode", False):
                object_id = (self.contract or {}).get("object_id")
                if object_id:
                    object_id = self.db.update_object(object_id, object_name, address)  # верни id
                else:
                    # если в контракте нет object_id — создаём новый объект
                    object_id = self.db.add_object(object_name, address)
            else:
                object_id = self.db.add_object(object_name, address)

            # --- Связка объект <-> контрагент ---
            if not object_id:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить ID объекта (object_id is None).")
                return
            if not counterparty_id:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить ID контрагента (counterparty_id is None).")
                return

            object_counterparty_id = self.db.link_object_counterparty(object_id, counterparty_id)

            # --- Добавление или обновление договора ---
            contract_data = {
                "number_contract": number_contract,
                "start_date": start_date,
                "term_contract": term_contract,
                "user_id": self.current_user_id,
                "type_id": type_id,
                "object_counterparty_id": object_counterparty_id,
                "file_contract": file_contract
            }

            if self.contract_id:  # обновление
                contract_data["id_contract"] = self.contract_id
                self.db.update_contract(contract_data)
            else:  # создание нового договора
                existing_contract = self.db.get_contract_by_number(number_contract)
                if existing_contract:
                    QMessageBox.warning(self, "Ошибка", f"Договор с номером '{number_contract}' уже существует!")
                    return
                contract_id = self.db.add_contract(
                    number_contract=number_contract,
                    start_date=start_date,
                    term_contract=term_contract,
                    object_counterparty_id=object_counterparty_id,
                    type_id=type_id,
                    user_id=self.current_user_id,
                    file_contract=file_contract
                )
                self.contract_id = contract_id

            # --- Доп.соглашения, гарантии, удержания ---
            self.save_addagreements()
            self.save_guarents()      # уже обновленная версия, предотвращает дубли
            self.save_retentions()

            QMessageBox.information(self, "Успешно", "✅ Договор и все связанные данные сохранены!")
            self.clear_form()

        except Exception as e:
             QMessageBox.critical(self, "Ошибка при сохранении", f"❌ {e}")

    def save_addagreements(self):
        """Сохраняет или обновляет доп. соглашения"""
        if not self.chk_addagreement.isChecked() or self.list_agreement.count() == 0:
            return

        for i in range(self.list_agreement.count()):
            item = self.list_agreement.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)

            number_agreement = data.get("number_agreement") or data.get("number")
            start_date_ag = data.get("start_date")
            description = data.get("description", "")
            file_path_ag = data.get("file_agreement")  # Берем путь из данных диалога

            if not number_agreement:
                print("⚠️ Пропущено доп. соглашение без номера")
                continue

            # Проверяем, что файл прикреплен
            if not file_path_ag:
                print(f"⚠️ Пропущено доп. соглашение {number_agreement} без файла")
                continue

            existing = self.db.get_addagreement_by_number(number_agreement, self.contract_id)
            if existing:
                existing_id = self.db.safe_id(existing, "id_addagreement")
                if existing_id:
                    success = self.db.update_addagreement(existing_id, number_agreement, start_date_ag, description,
                                                          file_path_ag)
                    if success:
                        print(f"✅ Обновлено доп. соглашение: {number_agreement}")
                else:
                    print(f"⚠️ Не удалось получить ID для доп. соглашения: {number_agreement}")
            else:
                new_id = self.db.add_addagreement_entry(
                    contract_id=self.contract_id,
                    number_agreement=number_agreement,
                    start_date=start_date_ag,
                    description=description,
                    file_path=file_path_ag
                )
                if new_id:
                    print(f"✅ Добавлено доп. соглашение: {number_agreement}")

    def save_guarents(self):
        """Сохраняет или обновляет банковские гарантии"""
        if not self.chk_guarent.isChecked() or self.list_guarents.count() == 0:
            print("ℹ️ Нет гарантий для сохранения")
            return

        successful_saves = 0
        total_guarents = self.list_guarents.count()

        for i in range(total_guarents):
            data = self.list_guarents.item(i).data(Qt.ItemDataRole.UserRole)
            number_guarent = str(data.get("number_guarent") or data.get("number"))
            start_guarent = data.get("start_guarent") or data.get("start_date")
            term_guarent = data.get("term_guarent")
            type_guarent = data.get("type")

            if not number_guarent or number_guarent == "None":
                print("⚠️ Пропущена банковская гарантия без номера")
                continue

            try:
                print(f"🔧 Обрабатываем гарантию: {number_guarent}")

                type_id = self.db.ensure_type_guarent_exists(type_guarent)
                if not type_id:
                    print(f"❌ Не удалось получить/создать тип гарантии: {type_guarent}")
                    continue

                # Проверяем существующую гарантию
                existing = self.db.get_guarent_by_number(number_guarent)

                if existing:
                    # Обновляем существующую гарантию
                    existing_id = self.db.safe_id(existing, "id_guarent")
                    if existing_id:
                        success = self.db.update_bank_guarent(existing_id, number_guarent, start_guarent, term_guarent,
                                                              type_id)
                        if success:
                            link_success = self.db.link_guarent_contract(self.contract_id, existing_id)
                            if link_success:
                                successful_saves += 1
                                print(f"✅ Гарантия обновлена и привязана: {number_guarent}")
                            else:
                                print(f"⚠️ Гарантия обновлена, но не привязана: {number_guarent}")
                        else:
                            print(f"❌ Не удалось обновить гарантию: {number_guarent}")
                else:
                    # Создаем новую гарантию
                    guarent_id = self.db.add_bank_guarent(number_guarent, start_guarent, term_guarent, type_id)
                    if guarent_id:
                        link_success = self.db.link_guarent_contract(self.contract_id, guarent_id)
                        if link_success:
                            successful_saves += 1
                            print(f"✅ Гарантия создана и привязана: {number_guarent}")
                        else:
                            print(f"⚠️ Гарантия создана, но не привязана: {number_guarent}")
                    else:
                        print(f"❌ Не удалось создать гарантию: {number_guarent}")

            except Exception as e:
                print(f"💥 ОШИБКА при сохранении гарантии {number_guarent}: {e}")
                import traceback
                traceback.print_exc()

        print(f"📊 Итог по гарантиям: {successful_saves}/{total_guarents} успешно сохранено")

    def save_retentions(self):
        """Сохраняет или обновляет гарантийные удержания"""
        if not self.chk_retention.isChecked() or self.list_retentions.count() == 0:
            return

        for i in range(self.list_retentions.count()):
            data = self.list_retentions.item(i).data(Qt.ItemDataRole.UserRole)
            term_warrantyretention = data.get("term_WarrantyRetention") or data.get("term")
            amount = data.get("amount")

            if not term_warrantyretention or amount is None:
                continue

            existing = self.db.get_retention_by_contract(self.contract_id)
            if existing and len(existing) > 0:
                existing_id = self.db.safe_id(existing[0], "id_warrantyretention")
                if existing_id:
                    success = self.db.update_warranty_retention(existing_id,
                                                                term_warrantyretention=term_warrantyretention,
                                                                amount=amount)
                    if success:
                        print(f"✅ Обновлено гарантийное удержание: {amount} руб.")
                else:
                    print(f"⚠️ Не удалось получить ID для гарантийного удержания")
            else:
                new_id = self.db.add_warranty_retention(
                    contract_id=self.contract_id,
                    term_warrantyretention=term_warrantyretention,
                    amount=amount
                )
                if new_id:
                    print(f"✅ Добавлено гарантийное удержание: {amount} руб.")

    # редактирование
    def load_contract_data(self, contract_data):
        """Загружает данные договора и связанных таблиц в форму"""
        try:
            # --- Сохраняем ссылку на текущий договор ---
            self.contract = contract_data
            self.contract_id = contract_data.get("id_contract")
            print(f"DEBUG: Загружаен договор ID: {self.contract_id}")

            self.is_edit_mode = True
            # --- Основные поля договора ---
            self.txt_number.setText(str(contract_data.get("number_contract", "")))
            self.cmb_type.setCurrentText(contract_data.get("type_name", ""))
            self.txt_counterparty.setText(contract_data.get("counterparty_name", ""))
            self.txt_inn.setText(str(contract_data.get("inn", "")))
            self.txt_object.setText(contract_data.get("object_name", ""))
            self.txt_address.setText(contract_data.get("address", ""))

            # --- Даты ---
            start_date = contract_data.get("start_date")
            term_date = contract_data.get("term_contract")

            if start_date:
                self.date_start.setDate(QDate(start_date.year, start_date.month, start_date.day))
            if term_date:
                self.chk_term.setChecked(True)
                self.date_term.setDate(QDate(term_date.year, term_date.month, term_date.day))
            else:
                self.chk_term.setChecked(False)
                self.date_term.setEnabled(False)

            # --- Файл договора ---
            file_contract = contract_data.get("file_contract")
            if file_contract:
                self.lbl_file.setText(os.path.basename(file_contract))
                self.file_path = file_contract
            else:
                self.lbl_file.setText("Файл не выбран")
                self.file_path = None

            # --- Банковские гарантии ---
            self.list_guarents.clear()
            bank_guarents = contract_data.get("bank_guarent", [])
            if bank_guarents:
                self.chk_guarent.setChecked(True)
                self.toggle_guarents(True)

                if isinstance(bank_guarents, dict):
                    bank_guarents = [bank_guarents]

                for bg in bank_guarents:
                    display = f"{bg.get('number_guarent', '')} — {bg.get('type', '')} ({bg.get('start_date', '')} → {bg.get('term_guarent', '')})"
                    item = QListWidgetItem(display)
                    item.setData(Qt.ItemDataRole.UserRole, bg)
                    self.list_guarents.addItem(item)

            # --- Гарантийные удержания ---
            self.list_retentions.clear()
            warrantyret = contract_data.get("warrantyretention", [])
            if warrantyret:
                self.chk_retention.setChecked(True)
                self.toggle_retentions(True)

                if isinstance(warrantyret, dict):
                    warrantyret = [warrantyret]

                for w in warrantyret:
                    display = f"Сумма: {w.get('amount', 0)} ₽ (до {w.get('term_warrantyretention', '')})"
                    item = QListWidgetItem(display)
                    item.setData(Qt.ItemDataRole.UserRole, w)
                    self.list_retentions.addItem(item)

            # --- Дополнительные соглашения ---
            self.list_agreement.clear()
            addagreements = contract_data.get("addagreements", [])
            if addagreements:
                self.chk_addagreement.setChecked(True)
                self.toggle_add_agreement_section(True)

                if isinstance(addagreements, dict):
                    addagreements = [addagreements]

                for ag in addagreements:
                    display = f"{ag.get('number_agreement', '')} — {ag.get('start_date', '')} ({ag.get('description', '')})"
                    item = QListWidgetItem(display)
                    item.setData(Qt.ItemDataRole.UserRole, ag)
                    self.list_agreement.addItem(item)

        except KeyError as ke:
            print("KeyError при сохранении — отсутствует ключ:", ke)
            print("Данные, которые пытались сохранить:", repr(contract_data))
            raise

    def exec(self):
        # Запуск модального диалога
        return super().exec()