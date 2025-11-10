# -*- coding: utf-8 -*-
# db.py — модуль для работы с PostgreSQL
# Подключение, авторизация пользователей, базовые операции

import psycopg2
from psycopg2.extras import RealDictRow, RealDictCursor
from contextlib import contextmanager
import os

class Database:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self):
        """Инициализация подключения к БД"""
        try:
            self.conn = psycopg2.connect(
                dbname="modtfil",
                user="postgres",
                password="12345",
                host="127.0.1.45",
                port="5432"
            )
            self.conn.autocommit = True
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")

    def safe_id(self, value, key: str = 'id') -> int | None:
        """
        Возвращает int ID из разных форматов:
        - int -> int
        - str (цифры) -> int
        - dict / RealDictRow -> ищем по ключам key, 'id', 'id_user', ...
        - (x,) / [x] -> рекурсивно
        - объект с атрибутом .id -> int(.id)
        Иначе -> None
        """
        if value is None:
            return None

        # 1) уже int
        if isinstance(value, int):
            return value

        # 2) str с цифрами
        if isinstance(value, str):
            s = value.strip()
            return int(s) if s.isdigit() else None

        # 3) RealDictRow -> dict
        if isinstance(value, RealDictRow):
            value = dict(value)

        # 4) dict c возможными ключами
        if isinstance(value, dict):
            possible_keys = [
                key, 'id',
                'id_user', 'id_type', 'id_contract', 'id_guarent',
                'id_addagreement', 'id_warrantyretention', 'id_obgect_counterparty',
                'id_counterparty', 'id_object'
            ]
            for k in possible_keys:
                if k in value and value[k] is not None:
                    try:
                        return int(value[k])
                    except Exception:
                        pass
            # не нашли
            print(f"⚠️ Не удалось найти ID в словаре: {value}")
            return None

        # 5) одиночные кортеж/список вида (123,) или [123]
        if isinstance(value, (tuple, list)) and len(value) == 1:
            return self.safe_id(value[0], key=key)

        # 6) объект с атрибутом .id
        if hasattr(value, 'id'):
            try:
                return int(getattr(value, 'id'))
            except Exception:
                pass

        # 7) всё прочее — логируем тип для отладки
        print(f"⚠️ Неизвестный тип для safe_id: {value} ({type(value)})")
        return None

    # ---------- ПОЛЬЗОВАТЕЛИ ----------

    def check_user(self, login, password):
        """Проверяет существование пользователя в базе"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM users WHERE login = %s AND password = %s",
                    (login, password)
                )
                return cur.fetchone()
        except Exception as e:
            print(f"Ошибка при проверке пользователя: {e}")
            return None

    def get_all_role(self, name_role):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT name_role FROM role ORDER BY id_role")
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка при получении должности: {e}")
            return []

    def add_role(self, role_name):
        """Добавляет новую роль и возвращает её id"""
        try:
            with self.conn.cursor() as cur:
                # Проверяем, есть ли роль уже
                cur.execute("SELECT id_role FROM role WHERE name_role = %s", (role_name,))
                result = cur.fetchone()
                if result:
                    return result[0]
                # Если нет, добавляем
                cur.execute("INSERT INTO role (name_role) VALUES (%s) RETURNING id_role", (role_name,))
                role_id = cur.fetchone()[0]
                self.conn.commit()
                return role_id
        except Exception as e:
            print(f"Ошибка при добавлении роли: {e}")
            return None

    def delete_role(self, name_role):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("DELETE FROM role WHERE name_role = %s",
                            (name_role,))
                return True
        except Exception as e:
            print(f"Ошибка удаления должности: {e}")
            return False

    def get_all_users(self):
        """Возвращает список всех пользователей с ролью"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                            SELECT u.id_user,
                                   u.last_name,
                                   u.name_user,
                                   u.partronymic,
                                   u.login,
                                   u.phone,
                                   r.name_role AS role
                            FROM users u
                                     LEFT JOIN role r ON u.role_id = r.id_role
                            ORDER BY u.id_user
                            """)
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка при получении пользователей: {e}")
            return []

    def add_user(self, last_name, name_user, partronymic, phone, login, password, role_id=None):
        """Добавляет нового пользователя с ролью"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO users (last_name, name_user, partronymic, phone, login, password, role_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                            (last_name, name_user, partronymic, phone, login, password, role_id))
            return True
        except Exception as e:
            print(f"Ошибка добавления пользователя: {e}")
            return False

    def delete_user(self, user_id):
        """Удаляет пользователя по ID"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id_user = %s",
                            (user_id,))
                return True
        except Exception as e:
            print(f"Ошибка удаления пользователя: {e}")
            return False

    def get_user_by_credentials(self, login, password):
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                            SELECT u.*, r.name_role AS role
                            FROM users u
                                     INNER JOIN role r ON u.role_id = r.id_role
                            WHERE u.login = %s
                              AND u.password = %s
                            """, (login, password))
                return cur.fetchone()
        except Exception as e:
            print(f"Ошибка при проверке пользователя: {e}")
            return None

    # ---------- ТИПЫ ДОГОВОРОВ ----------
    def get_types(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM type ORDER BY name_type")
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка получения типов договоров: {e}")
            return []

    def add_type(self, name_type):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO type (name_type)
                    VALUES (%s) ON CONFLICT (name_type) DO NOTHING
                """, (name_type,))
                self.conn.commit()
        except Exception as e:
            print(f"Ошибка добавления типа договора: {e}")
            self.conn.rollback()

    def get_type_id_by_name(self, name_type):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT id_type FROM type WHERE name_type = %s", (name_type,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Ошибка при получении ID типа: {e}")
            return None
    # ---------- ДОГОВОРЫ ----------
    def add_object(self, name_object, address):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id_object
                    FROM object
                    WHERE name_object = %s AND address = %s
                """, (name_object, address))
                row = cur.fetchone()
                if row:
                    return row[0]

                cur.execute("""
                    INSERT INTO object (name_object, address)
                    VALUES (%s, %s) RETURNING id_object
                """, (name_object, address))
                new_id = cur.fetchone()[0]
                self.conn.commit()
                return new_id
        except Exception as e:
            print(f"Ошибка при добавлении объекта: {e}")
            self.conn.rollback()
            return None

    def link_object_counterparty(self, object_id, counterparty_id):
        try:
            object_id = self.safe_id(object_id, "id_object")
            counterparty_id = self.safe_id(counterparty_id, "id_counterparty")
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT id_obgect_counterparty
                            FROM object_counterparty
                            WHERE object_id = %s
                              AND counterparty_id = %s
                            """, (object_id, counterparty_id))
                existing = cur.fetchone()
                if existing:
                    return existing[0]

                cur.execute("""
                            INSERT INTO object_counterparty (counterparty_id, object_id)
                            VALUES (%s, %s) RETURNING id_obgect_counterparty
                            """, (counterparty_id, object_id))
                new_id = cur.fetchone()[0]
                self.conn.commit()
                return new_id
        except Exception as e:
            print(f"Ошибка при связывании объекта и контрагента: {e}")
            self.conn.rollback()
            return None

    def add_contract(self, number_contract, start_date, term_contract,
                     object_counterparty_id, type_id, user_id, file_contract=None):
        try:
            # Безопасно извлекаем ID-шники
            object_counterparty_id = self.safe_id(object_counterparty_id, "id")  # не "id_obgect_counterparty"
            type_id = self.safe_id(type_id, "id")
            user_id = self.safe_id(user_id, "id")

            with self.conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO contract (number_contract, start_date, term_contract,
                                                  object_counterparty_id, type_id, user_id, file_contract)
                            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_contract
                            """, (number_contract, start_date, term_contract,
                                  object_counterparty_id, type_id, user_id, file_contract))
                result = cur.fetchone()
                self.conn.commit()
                return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при добавлении договора: {e}")
            self.conn.rollback()
            return None

    def get_contract_by_id(self, contract_id):
        """Возвращает все данные по договору"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # --- Основной договор ---
                cur.execute("""
                            SELECT c.id_contract,
                                   c.number_contract,
                                   c.start_date,
                                   c.term_contract,
                                   c.file_contract,
                                   t.name_type          AS type_name,
                                   o.name_object        AS object_name,
                                   o.address,
                                   cp.name_counterparty AS counterparty_name,
                                   cp.inn
                            FROM contract c
                                     LEFT JOIN type t ON c.type_id = t.id_type
                                     LEFT JOIN object_counterparty oc
                                               ON c.object_counterparty_id = oc.id_obgect_counterparty
                                     LEFT JOIN object o ON oc.object_id = o.id_object
                                     LEFT JOIN counterparty cp ON oc.counterparty_id = cp.id_counterparty
                            WHERE c.id_contract = %s
                            """, (contract_id,))
                contract = cur.fetchone()
                if not contract:
                    return None

                # --- Дополнительные соглашения ---
                cur.execute("""
                            SELECT id_addagreement,
                                   number_agreement AS number,
                                   start_date,
                                   description,
                                   file_agreement
                            FROM addagreement
                            WHERE contract_id = %s
                            ORDER BY start_date;
                            """, (contract_id,))
                contract["addagreements"] = cur.fetchall()

                # --- Банковские гарантии ---
                cur.execute("""
                            SELECT bg.id_guarent,
                                   bg.number_guarent    AS number,
                                   bg.start_date,
                                   bg.term_guarent,
                                   tg.name_type_guarent AS type
                            FROM bank_guarent bg
                                     JOIN type_guarent tg ON bg.type_guarent_id = tg.id_type_guarent
                                     JOIN guarent_contract gc ON bg.id_guarent = gc.guarent_id
                            WHERE gc.contract_id = %s
                            ORDER BY bg.start_date;
                            """, (contract_id,))
                contract["bank_guarent"] = cur.fetchall()

                # --- Гарантийные удержания (если есть таблица retention) ---
                try:
                    cur.execute("""
                                SELECT id_warrantyretention,
                                       amount,
                                       term_warrantyretention
                                FROM warrantyretention
                                WHERE contract_id = %s
                                ORDER BY term_warrantyretention;
                                """, (contract_id,))
                    contract["warrantyretention"] = cur.fetchall()
                    return contract
                except Exception:
                    # если таблицы retention нет — просто пропускаем
                    contract["warrantyretention"] = []

                return contract

        except Exception as e:
            print(f"[Ошибка] get_contract_by_id: {e}")
            return None

    def get_contract_by_number(self, number_contract):
        """Проверяет, существует ли договор с таким номером"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT id_contract FROM contract WHERE number_contract = %s", (number_contract,))
                return cur.fetchone()
        except Exception as e:
            print(f"[Ошибка] get_contract_by_number: {e}")
            return None

    def get_all_contracts(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT c.id_contract, c.number_contract, c.start_date, c.term_contract,
                           t.name_type, cp.name_counterparty, cp.inn, o.name_object, o.address
                    FROM contract c
                    LEFT JOIN type t ON c.type_id = t.id_type
                    LEFT JOIN object_counterparty oc ON c.object_counterparty_id = oc.id_obgect_counterparty
                    LEFT JOIN counterparty cp ON oc.counterparty_id = cp.id_counterparty
                    LEFT JOIN object o ON oc.object_id = o.id_object
                    ORDER BY c.id_contract DESC
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка получения договоров: {e}")
            return []

    def delete_contract(self, contract_id):
        """
        Удаляет договор и все связанные с ним записи (доп. соглашения, гарантии, удержания и т.д.)
        благодаря каскадным связям в БД.
        """
        try:
            with self.conn.cursor() as cursor:
                # Удаляем договор — все связанные записи удалятся каскадно
                cursor.execute("DELETE FROM contract WHERE id_contract = %s;", (contract_id,))
                self.conn.commit()
                print(f"[INFO] Договор с id={contract_id} и все связанные записи успешно удалены.")
                return True
        except Exception as e:
            print(f"[Ошибка при удалении договора]: {e}")
            self.conn.rollback()
            return False

    def _convert_to_simple_types(self, data):
        """
        Преобразует только сложные объекты, оставляя даты как есть
        """
        if data is None:
            return None

        result = {}

        for key, value in data.items():
            if value is None:
                result[key] = None
            elif isinstance(value, RealDictRow):
                # Для RealDictRow извлекаем только ID если это user_id
                if key == 'user_id' and 'id_user' in value:
                    result[key] = value['id_user']
                else:
                    result[key] = dict(value)
            elif hasattr(value, '__dict__'):  # Для других объектов
                result[key] = dict(value)
            elif hasattr(value, '_asdict'):  # Для namedtuple
                result[key] = value._asdict()
            else:
                # Оставляем даты и простые типы как есть
                result[key] = value

        return result

    def update_contract(self, contract_data):
        try:
            if isinstance(contract_data, RealDictRow):
                contract_data = dict(contract_data)
            print("Original data: bebebe", contract_data)

            contract_data = self._convert_to_simple_types(contract_data)
            print("Converted data:", contract_data)

            contract_id = contract_data.get("id_contract")
            if not contract_id:
                raise ValueError("ID контракта обязателен для обновления")

            # Извлекаем user_id из объекта, если он передан как словарь
            user_id = contract_data.get("user_id")
            if isinstance(user_id, dict) and 'id_user' in user_id:
                user_id = user_id['id_user']
            elif user_id is not None:
                user_id = self.safe_id(user_id, "id_user")
            else:
                user_id = None

            # Обрабатываем остальные ID
            type_id = self.safe_id(contract_data.get("type_id"), "id_type")
            object_counterparty_id = self.safe_id(contract_data.get("object_counterparty_id"), "id_obgect_counterparty")

            print(
                f"Processed IDs - user_id: {user_id}, type_id: {type_id}, object_counterparty_id: {object_counterparty_id}")

            with self.conn.cursor() as cur:
                cur.execute("""
                            UPDATE contract
                            SET number_contract        = %s,
                                start_date             = %s,
                                term_contract          = %s,
                                user_id                = %s,
                                type_id                = %s,
                                object_counterparty_id = %s,
                                file_contract          = %s
                            WHERE id_contract = %s
                            """, (
                                contract_data.get("number_contract"),
                                contract_data.get("start_date"),  # Теперь это строка в формате YYYY-MM-DD
                                contract_data.get("term_contract"),  # Теперь это строка в формате YYYY-MM-DD
                                user_id,
                                type_id,
                                object_counterparty_id,
                                contract_data.get("file_contract"),
                                contract_id
                            ))

                self.conn.commit()
                print(f"Успешно обновлен контракт с ID {contract_id}")
                return True

        except Exception as e:
            print(f"[Ошибка] update_contract: {e}")
            self.conn.rollback()
            return False

    # ---------- КОНТРАГЕНТЫ ----------
    def get_counterparty_id_by_inn(self, inn):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT id_counterparty FROM counterparty WHERE inn = %s", (inn,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Ошибка при поиске контрагента по ИНН: {e}")
            return None

    def get_counterparty_id_by_name(self, name):
        """Возвращает ID контрагента по имени (если найден)"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT id_counterparty
                            FROM counterparty
                            WHERE TRIM(LOWER(name_counterparty)) = TRIM(LOWER(%s)) LIMIT 1
                            """, (name,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"[Ошибка] get_counterparty_id_by_name: {e}")
            return None

    def get_object_id_by_address(self, address):
        """Возвращает ID объекта по адресу (если найден)"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT id_object
                            FROM object
                            WHERE TRIM(LOWER(address)) = TRIM(LOWER(%s)) LIMIT 1
                            """, (address,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"[Ошибка] get_object_id_by_address: {e}")
            return None

    def ensure_object_counterparty_link(self, counterparty_id, object_id):
        """Возвращает существующую или создаёт новую связь объект–контрагент"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT id_object_counterparty
                            FROM object_counterparty
                            WHERE counterparty_id = %s
                              AND object_id = %s LIMIT 1
                            """, (counterparty_id, object_id))
                row = cur.fetchone()
                if row:
                    return row[0]

                cur.execute("""
                            INSERT INTO object_counterparty (counterparty_id, object_id)
                            VALUES (%s, %s) RETURNING id_object_counterparty
                            """, (counterparty_id, object_id))
                new_id = cur.fetchone()[0]
                self.conn.commit()
                return new_id
        except Exception as e:
            print(f"[Ошибка] ensure_object_counterparty_link: {e}")
            self.conn.rollback()
            return None

    def add_counterparty(self, name, inn=None):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO counterparty (name_counterparty, inn)
                    VALUES (%s, %s)
                    ON CONFLICT (inn) DO NOTHING
                    RETURNING id_counterparty
                """, (name, inn))
                row = cur.fetchone()
                if row:
                    self.conn.commit()
                    return row[0]
                else:
                    cur.execute("SELECT id_counterparty FROM counterparty WHERE inn = %s", (inn,))
                    existing = cur.fetchone()
                    return existing[0] if existing else None
        except Exception as e:
            print(f"Ошибка при добавлении контрагента: {e}")
            return None

    def update_counterparty(self, counterparty_id, name, inn):
        """Обновляет контрагента по ID"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            UPDATE counterparty
                            SET name_counterparty = %s,
                                inn               = %s
                            WHERE id_counterparty = %s
                            """, (name, inn, counterparty_id))
            self.conn.commit()
            print(f"✅ Контрагент {counterparty_id} обновлён: {name} ({inn})")
            return True
        except Exception as e:
            print(f"[Ошибка] update_counterparty: {e}")
            self.conn.rollback()
            return False

    def update_object(self, object_id, name, address):
        """Обновляет объект с заданным ID"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            UPDATE object
                            SET name    = %s,
                                address = %s
                            WHERE id_object = %s
                            """, (name, address, object_id))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"[Ошибка] update_object: {e}")
            self.conn.rollback()
            return False

    # ПОИСК ДОГОВОРОВ

    def search_contract(self, number_contract=None, name_counterparty=None, name_type=None, name_object=None):
        """Поиск договора по номеру, типу, контрагенту и объекту (без учета регистра)"""
        try:
            with self.conn.cursor() as cur:
                query = """
                        SELECT c.id_contract,
                               c.number_contract,
                               t.name_type,
                               cp.name_counterparty,
                               o.name_object,
                               c.start_date
                        FROM contract c
                                 LEFT JOIN type t ON c.type_id = t.id_type
                                 LEFT JOIN object_counterparty oc \
                                           ON c.object_counterparty_id = oc.id_obgect_counterparty
                                 LEFT JOIN counterparty cp ON oc.counterparty_id = cp.id_counterparty
                                 LEFT JOIN object o ON oc.object_id = o.id_object
                        WHERE 1 = 1 \
                        """
                params = []

                if number_contract:
                    query += " AND c.number_contract ILIKE %s"
                    params.append(f"%{number_contract}%")

                if name_type and name_type.lower() != "все типы":
                    query += " AND t.name_type ILIKE %s"
                    params.append(f"%{name_type}%")

                if name_counterparty:
                    query += " AND cp.name_counterparty ILIKE %s"
                    params.append(f"%{name_counterparty}%")

                if name_object:
                    query += " AND o.name_object ILIKE %s"
                    params.append(f"%{name_object}%")

                query += " ORDER BY c.start_date DESC"

                cur.execute(query, params)
                rows = cur.fetchall()

                if not cur.description:
                    print("⚠️ Нет описания курсора (возможно, ошибка SQL).")
                    return []

                col_names = [desc[0] for desc in cur.description]
                results = [dict(zip(col_names, row)) for row in rows]
                return results

        except Exception as e:
            print(f"[Ошибка] search_contract: {e}")
            return []

    def get_expiring_items(self, today, soon):
        """
        Возвращает список договоров, банковских гарантий и гарантийных удержаний,
        срок действия которых истекает между today и soon.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT 'Договор'                         AS category,
                                   number_contract                   AS name,
                                   term_contract                     AS end_date,
                                   'Срок действия договора истекает' AS note
                            FROM contract
                            WHERE term_contract IS NOT NULL
                              AND term_contract BETWEEN %s AND %s

                            UNION ALL

                            SELECT 'Банковская гарантия'               AS category,
                                   number_guarent                      AS name,
                                   term_guarent                        AS end_date,
                                   'Срок банковской гарантии истекает' AS note
                            FROM bank_guarent
                            WHERE term_guarent IS NOT NULL
                              AND term_guarent BETWEEN %s AND %s

                            UNION ALL

                            SELECT 'Гарантийное удержание' AS category,
                                    ('Удержание №' || id_warrantyretention)::text AS name,
                                    term_warrantyretention AS end_date,
                                    CONCAT('Истекает срок гарантийного удержания (сумма ', amount, ' руб.)') AS note
                                    FROM warrantyretention
                                    WHERE term_warrantyretention IS NOT NULL
                                      AND term_warrantyretention BETWEEN %s AND %s
                            """, (today, soon, today, soon, today, soon))

                rows = cur.fetchall()
                return [
                    dict(zip(["category", "name", "end_date", "note"], row))
                    for row in rows
                ]

        except Exception as e:
            print(f"Ошибка при получении уведомлений: {e}")
            return []

    # ---------- ДОПОЛНИТЕЛЬНЫЕ СУЩНОСТИ ----------

    def add_bank_guarent(self, number_guarent, start_date, term_date, type_guarent_id):
        """Добавляет банковскую гарантию"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO bank_guarent (number_guarent, start_date, term_guarent, type_guarent_id)
                            VALUES (%s, %s, %s, %s) RETURNING id_guarent
                            """, (number_guarent, start_date, term_date, type_guarent_id))
                result = cur.fetchone()
                self.conn.commit()
                return result[0] if result else None
        except Exception as e:
            print(f"[Ошибка] add_bank_guarent: {e}")
            self.conn.rollback()
            return None

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

    def update_bank_guarent(self, guarent_id, number_guarent, start_date, term_date, type_guarent_id):
        """Обновляет банковскую гарантию"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            UPDATE bank_guarent
                            SET number_guarent  = %s,
                                start_date      = %s,
                                term_guarent    = %s,
                                type_guarent_id = %s
                            WHERE id_guarent = %s
                            """, (number_guarent, start_date, term_date, type_guarent_id, guarent_id))
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(f"[Ошибка] update_bank_guarent: {e}")
            self.conn.rollback()
            return False

    def get_type_guarent_id(self, type_name):
        """Получает ID типа гарантии по названию"""
        try:
            with self.conn.cursor() as cur:
                # Сначала пробуем найти в таблице type_guarent
                cur.execute("""
                            SELECT id_type_guarent
                            FROM type_guarent
                            WHERE name_type_guarent = %s
                            """, (type_name,))
                result = cur.fetchone()
                if result:
                    return result[0]

                # Если не найдено, пробуем создать новый тип
                cur.execute("""
                            INSERT INTO type_guarent (name_type_guarent)
                            VALUES (%s) ON CONFLICT (name_type_guarent) DO NOTHING
                    RETURNING id_type_guarent
                            """, (type_name,))

                result = cur.fetchone()
                if result:
                    return result[0]

                # Если все еще нет, получаем существующий
                cur.execute("SELECT id_type_guarent FROM type_guarent WHERE name_type_guarent = %s", (type_name,))
                result = cur.fetchone()
                return result[0] if result else 1

        except Exception as e:
            print(f"[Ошибка] get_type_guarent_id: {e}")
            return 1

    def ensure_type_guarent_exists(self, type_name):
        """Убеждается, что тип гарантии существует, возвращает ID"""
        try:
            print(f"    🔍 ensure_type_guarent_exists: ищем тип '{type_name}'")
            with self.conn.cursor() as cur:
                # Сначала ищем существующий тип
                cur.execute("SELECT id_type_guarent FROM type_guarent WHERE name_type_guarent = %s", (type_name,))
                result = cur.fetchone()
                if result:
                    print(f"    ✅ Тип найден: ID {result[0]}")
                    return result[0]

                # Если не найден, создаем новый
                print(f"    🆕 Создаем новый тип: '{type_name}'")
                cur.execute("""
                            INSERT INTO type_guarent (name_type_guarent)
                            VALUES (%s) RETURNING id_type_guarent
                            """, (type_name,))

                result = cur.fetchone()
                if result:
                    self.conn.commit()
                    print(f"    ✅ Новый тип создан: ID {result[0]}")
                    return result[0]

                # Если конфликт, снова ищем
                cur.execute("SELECT id_type_guarent FROM type_guarent WHERE name_type_guarent = %s", (type_name,))
                result = cur.fetchone()
                if result:
                    print(f"    ✅ Тип найден после конфликта: ID {result[0]}")
                else:
                    print(f"    ❌ Тип не найден даже после попытки создания")
                return result[0] if result else None

        except Exception as e:
            print(f"    💥 Ошибка в ensure_type_guarent_exists: {e}")
            self.conn.rollback()
            return None

    def add_bank_guarent(self, number_guarent, start_date, term_date, type_guarent_id):
        """Добавляет банковскую гарантию"""
        try:
            print(f"    🆕 add_bank_guarent: создаем гарантию '{number_guarent}' с типом ID {type_guarent_id}")
            with self.conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO bank_guarent (number_guarent, start_date, term_guarent, type_guarent_id)
                            VALUES (%s, %s, %s, %s) RETURNING id_guarent
                            """, (number_guarent, start_date, term_date, type_guarent_id))
                result = cur.fetchone()
                self.conn.commit()

                if result:
                    print(f"    ✅ Гарантия создана: ID {result[0]}")
                else:
                    print(f"    ❌ Не удалось создать гарантию")

                return result[0] if result else None
        except Exception as e:
            print(f"    💥 Ошибка в add_bank_guarent: {e}")
            self.conn.rollback()
            return None

    def add_warranty_retention(self, contract_id, term_warrantyretention, amount):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO warrantyretention (contract_id, term_warrantyretention, amount)
                            VALUES (%s, %s, %s) RETURNING id_warrantyretention
                            """, (contract_id, term_warrantyretention, amount))
                retention_id = cur.fetchone()[0]
                self.conn.commit()
                return retention_id
        except Exception as e:
            print(f"[Ошибка] add_warranty_retention: {e}")
            self.conn.rollback()
            return None

    def update_warranty_retention(self, retention_id, term_warrantyretention=None, amount=None):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE warrantyretention
                    SET term_warrantyretention = COALESCE(%s, term_warrantyretention),
                        amount = COALESCE(%s, amount)
                    WHERE id_warrantyretention = %s
                """, (term_warrantyretention, amount, retention_id))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"[Ошибка] update_warranty_retention: {e}")
            self.conn.rollback()
            return False

    def add_addagreement_entry(self, contract_id, number_agreement, start_date, description, file_path):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT id_addagreement FROM addagreement WHERE number_agreement = %s", (number_agreement,))
                existing = cur.fetchone()
                if existing:
                    cur.execute("""
                        UPDATE addagreement
                        SET contract_id=%s, start_date=%s, description=%s, file_agreement=%s
                        WHERE id_addagreement=%s
                    """, (contract_id, start_date, description, file_path, existing[0]))
                    new_id = existing[0]
                else:
                    cur.execute("""
                        INSERT INTO addagreement (contract_id, number_agreement, start_date, description, file_agreement)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id_addagreement
                    """, (contract_id, number_agreement, start_date, description, file_path))
                    new_id = cur.fetchone()[0]
                self.conn.commit()
                return new_id
        except Exception as e:
            print(f"[Ошибка] add_addagreement_entry: {e}")
            self.conn.rollback()
            return None

    def update_addagreement(self, agreement_id, number_agreement, start_date, description, file_path):
        """Обновляет дополнительное соглашение"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            UPDATE addagreement
                            SET number_agreement = %s,
                                start_date       = %s,
                                description      = %s,
                                file_agreement   = %s
                            WHERE id_addagreement = %s
                            """, (number_agreement, start_date, description, file_path, agreement_id))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"[Ошибка] update_addagreement: {e}")
            self.conn.rollback()
            return False

    # извлечение данных из базы данных
    def get_guarantees_by_contract(self, contract_id):
        """Возвращает список банковских гарантий для указанного договора."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                            SELECT bg.id_guarent     AS id,
                                   bg.number_guarent AS number,
                                   bg.start_date,
                                   bg.term_guarent   AS term,
                                   bg.amount,
                                   bg.type_guarent_id
                            FROM bank_guarent bg
                                     JOIN guarent_contract gc ON bg.id_guarent = gc.guarent_id
                            WHERE gc.contract_id = %s
                            """, (contract_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка получения банковских гарантий: {e}")
            return []

    def get_guarent_by_number(self, number_guarent, contract_id=None):
        """Получает гарантию по номеру (исправленная версия)"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if contract_id:
                    # Правильное сравнение типов - передаем строку как строку
                    cur.execute("""
                                SELECT bg.*
                                FROM bank_guarent bg
                                         JOIN guarent_contract gc ON bg.id_guarent = gc.guarent_id
                                WHERE bg.number_guarent = %s
                                  AND gc.contract_id = %s
                                """, (str(number_guarent), contract_id))
                else:
                    cur.execute("""
                                SELECT *
                                FROM bank_guarent
                                WHERE number_guarent = %s
                                """, (str(number_guarent),))
                return cur.fetchone()
        except Exception as e:
            print(f"[Ошибка] get_guarent_by_number: {e}")
            return None

    def get_retention_by_contract(self, contract_id):
        """Возвращает список гарантийных удержаний для указанного договора."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                            SELECT id_warrantyretention   AS id,
                                   contract_id,
                                   term_warrantyretention AS term,
                                   amount
                            FROM warrantyretention
                            WHERE contract_id = %s
                            """, (contract_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка получения гарантийных удержаний: {e}")
            return []

    def get_addagreements_by_contract(self, contract_id):
        """Возвращает список дополнительных соглашений для указанного договора."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                            SELECT id_addagreement  AS id,
                                   contract_id,
                                   number_agreement AS number,
                                   start_date,
                                   description,
                                   file_agreement
                            FROM addagreement
                            WHERE contract_id = %s
                            """, (contract_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка получения дополнительных соглашений: {e}")
            return []

    def get_warranty_retention_by_contract(self, contract_id):
        """Получить гарантийное удержание по договору"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                            SELECT id_warrantyretention, term_warrantyretention, amount
                            FROM warrantyretention
                            WHERE contract_id = %s
                            """, (contract_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"[Ошибка] get_warranty_retention_by_contract: {e}")
            return []

    def get_addagreement_by_number(self, number_agreement, contract_id=None):
        """Возвращает запись дополнительного соглашения по номеру и договору"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if contract_id:
                    cur.execute("""
                                SELECT id_addagreement,
                                       contract_id,
                                       number_agreement,
                                       start_date,
                                       description,
                                       file_agreement
                                FROM addagreement
                                WHERE contract_id = %s
                                  AND number_agreement = %s
                                """, (contract_id, str(number_agreement)))  # Исправлено: number_agreement как строка
                else:
                    cur.execute("""
                                SELECT id_addagreement,
                                       contract_id,
                                       number_agreement,
                                       start_date,
                                       description,
                                       file_agreement
                                FROM addagreement
                                WHERE number_agreement = %s
                                """, (str(number_agreement),))  # Исправлено: number_agreement как строка
                return cur.fetchone()
        except Exception as e:
            print(f"[Ошибка] get_addagreement_by_number: {e}")
            return None

    def delete_warranty_retention(self, retention_id):
        """Удаляет гарантийное удержание"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM warrantyretention WHERE id_warrantyretention = %s", (retention_id,))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"[Ошибка] delete_warranty_retention: {e}")
            self.conn.rollback()
            return False

    # Управление всеми табличами

    def _get_primary_key(self, table_name):
        """Возвращает имя первичного ключа таблицы"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT a.attname
                            FROM pg_index i
                                     JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY (i.indkey)
                            WHERE i.indrelid = %s::regclass
                    AND i.indisprimary;
                            """, (table_name,))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Ошибка получения первичного ключа таблицы {table_name}: {e}")
            return None

    def get_table_columns(self, table_name):
        """Возвращает список колонок указанной таблицы с информацией о типах"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT column_name, data_type, is_nullable, column_default
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = %s
                            ORDER BY ordinal_position
                            """, (table_name,))
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print(f"Ошибка получения колонок таблицы {table_name}: {e}")
            return []

    def get_foreign_key_reference(self, table_name, column_name):
        """
        Возвращает имя таблицы, на которую ссылается внешний ключ.
        """
        sql = """
              SELECT ccu.table_name AS reference_table
              FROM information_schema.table_constraints AS tc
                       JOIN information_schema.key_column_usage AS kcu
                            ON tc.constraint_name = kcu.constraint_name
                                AND tc.table_schema = kcu.table_schema
                       JOIN information_schema.constraint_column_usage AS ccu
                            ON ccu.constraint_name = tc.constraint_name
                                AND ccu.table_schema = tc.table_schema
              WHERE tc.constraint_type = 'FOREIGN KEY'
                AND kcu.table_schema = 'public'
                AND LOWER(kcu.table_name) = LOWER(%s)
                AND LOWER(kcu.column_name) = LOWER(%s); \
              """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (table_name, column_name))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Ошибка получения внешнего ключа {column_name} в {table_name}: {e}")
            return None

    def get_foreign_key_values(self, foreign_table):
        """
        Возвращает список значений внешнего ключа для указанной таблицы.
        :return: Список кортежей (id, описание)
        """
        try:
            # Получаем имя первичного ключа таблицы (обычно id или id_xxx)
            pk_field = self._get_primary_key(foreign_table)
            if not pk_field:
                print(f"⚠️ Не найден первичный ключ для таблицы {foreign_table}")
                return []

            # Находим первое текстовое поле (для отображения)
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = %s
                              AND data_type IN ('character varying', 'text')
                            ORDER BY ordinal_position LIMIT 1;
                            """, (foreign_table,))
                text_col = cur.fetchone()
                text_col = text_col[0] if text_col else pk_field  # fallback — показываем сам id

            sql = f"""
                SELECT {pk_field}::text, COALESCE({text_col}::text, '') 
                FROM {foreign_table}
                ORDER BY {pk_field};
            """

            with self.conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                return [(r[0], r[1]) for r in rows]

        except Exception as e:
            print(f"❌ Ошибка получения значений внешнего ключа из {foreign_table}: {e}")
            return []

    def insert_record(self, table_name, data):
        """Добавляет запись в любую таблицу"""
        try:
            # Фильтруем пустые значения для числовых полей
            filtered_data = {}
            for key, value in data.items():
                if value == "":
                    # Для пустых строк в числовых полях устанавливаем NULL
                    if self._is_numeric_field(table_name, key):
                        filtered_data[key] = None
                    else:
                        filtered_data[key] = value
                else:
                    filtered_data[key] = value

            columns = ", ".join(filtered_data.keys())
            placeholders = ", ".join(["%s"] * len(filtered_data))
            values = list(filtered_data.values())

            with self.conn.cursor() as cur:
                cur.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления записи в {table_name}: {e}")
            self.conn.rollback()
            return False

    def _is_numeric_field(self, table_name, column_name):
        """Проверяет, является ли поле числовым"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                            SELECT data_type
                            FROM information_schema.columns
                            WHERE table_name = %s
                              AND column_name = %s
                            """, (table_name, column_name))
                result = cur.fetchone()
                if result:
                    data_type = result[0]
                    return data_type in ['integer', 'bigint', 'smallint', 'decimal', 'numeric', 'real',
                                         'double precision']
                return False
        except Exception as e:
            print(f"Ошибка проверки типа поля: {e}")
            return False

    def get_table_records(self, table_name):
        """Получает все записи любой таблицы"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name}")
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка получения данных из {table_name}: {e}")
            return []

    def add_record(self, table_name, data: dict):
        """Добавляет запись в указанную таблицу (универсально)"""
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            values = list(data.values())

            with self.conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING *;",
                    values
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления записи в {table_name}: {e}")
            return False

    def update_record(self, table_name, record_id, data: dict, id_field=None):
        """Редактирует запись в таблице (универсально)"""
        try:
            # Обрабатываем данные перед обновлением
            processed_data = {}
            for key, value in data.items():
                # Для полей даты: если пустое или строка 'None' - используем NULL
                if any(date_keyword in key.lower() for date_keyword in ['date', 'term']):
                    if value is None or value == "" or str(value).lower() == 'none':
                        processed_data[key] = None  # Будет преобразовано в NULL
                    else:
                        processed_data[key] = value
                else:
                    # Для остальных полей оставляем как есть
                    processed_data[key] = value

            id_field = id_field or self._get_primary_key(table_name)

            # Формируем SET выражение с учетом NULL для дат
            set_parts = []
            values = []
            for key, value in processed_data.items():
                if value is None and any(date_keyword in key.lower() for date_keyword in ['date', 'term']):
                    set_parts.append(f"{key}=NULL")  # NULL для пустых дат
                else:
                    set_parts.append(f"{key}=%s")
                    values.append(value)

            set_expr = ', '.join(set_parts)
            values.append(record_id)

            with self.conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {table_name} SET {set_expr} WHERE {id_field}=%s;",
                    values
                )
                self.conn.commit()
                print(f"✅ Запись {record_id} в таблице {table_name} успешно обновлена")
                return True
        except Exception as e:
            print(f"❌ Ошибка обновления записи {record_id} в {table_name}: {e}")
            self.conn.rollback()
            return False

    def delete_record(self, table_name, record_id, id_field=None):
        """Удаляет запись из таблицы (универсально)"""
        try:
            id_field = id_field or self._get_primary_key(table_name)
            with self.conn.cursor() as cur:
                cur.execute(f"DELETE FROM {table_name} WHERE {id_field}=%s;", (record_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка удаления записи {record_id} из {table_name}: {e}")
            return False
    # ---------- ЗАКРЫТИЕ ----------
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()