from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout

import random
import sqlite3


def format_number(number):
    """Форматирует число с добавлением приставок (тыс., млн., млрд., трлн., квадр., квинт., секст., септил., октил., нонил., децил., андец.)"""
    if number >= 1_000_000_000_000_000_000_000_000_000_000_000_000:  # 1e36
        return f"{number / 1e36:.1f} андец."
    elif number >= 1_000_000_000_000_000_000_000_000_000_000_000:  # 1e33
        return f"{number / 1e33:.1f} децил."
    elif number >= 1_000_000_000_000_000_000_000_000_000_000:  # 1e30
        return f"{number / 1e30:.1f} нонил."
    elif number >= 1_000_000_000_000_000_000_000_000_000:  # 1e27
        return f"{number / 1e27:.1f} октил."
    elif number >= 1_000_000_000_000_000_000_000_000:  # 1e24
        return f"{number / 1e24:.1f} септил."
    elif number >= 1_000_000_000_000_000_000_000:  # 1e21
        return f"{number / 1e21:.1f} секст."
    elif number >= 1_000_000_000_000_000_000:  # 1e18
        return f"{number / 1e18:.1f} квинт."
    elif number >= 1_000_000_000_000_000:  # 1e15
        return f"{number / 1e15:.1f} квадр."
    elif number >= 1_000_000_000_000:  # 1e12
        return f"{number / 1e12:.1f} трлн."
    elif number >= 1_000_000_000:  # 1e9
        return f"{number / 1e9:.1f} млрд."
    elif number >= 1_000_000:  # 1e6
        return f"{number / 1e6:.1f} млн."
    elif number >= 1_000:  # 1e3
        return f"{number / 1e3:.1f} тыс."
    else:
        return str(number)


def save_building_change(faction_name, city, building_type, delta):
    """
    Обновляет количество зданий для указанного города в базе данных.
    delta — изменение (например, +1 или -1).
    """
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()

    try:
        # Проверяем, существует ли запись для данного города и типа здания
        cursor.execute('''
            SELECT count 
            FROM buildings 
            WHERE city_name = ? AND faction = ? AND building_type = ?
        ''', (city, faction_name, building_type))
        row = cursor.fetchone()

        if row:
            # Обновляем существующую запись
            new_count = row[0] + delta
            if new_count < 0:
                new_count = 0  # Предотвращаем отрицательные значения
            cursor.execute('''
                UPDATE buildings 
                SET count = ? 
                WHERE city_name = ? AND faction = ? AND building_type = ?
            ''', (new_count, city, faction_name, building_type))
        else:
            # Добавляем новую запись
            cursor.execute('''
                INSERT INTO buildings (city_name, faction, building_type, count)
                VALUES (?, ?, ?, ?)
            ''', (city, faction_name, building_type, delta))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении изменений в зданиях: {e}")
    finally:
        conn.close()


class Faction:
    def __init__(self, name):
        self.city_count = None
        self.faction = name
        self.db_path = 'game_data.db'  # Путь к базе данных
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.resources = self.load_resources_from_db()  # Загрузка ресурсов
        self.buildings = self.load_buildings()  # Загрузка зданий
        self.trade_agreements = self.load_trade_agreements()  # Загрузка торговых соглашений
        self.cities = self.load_cities()  # Загрузка городов
        self.hospitals = 0
        self.factories = 0
        self.taxes = 0
        self.food_info = 0
        self.work_peoples = 0
        self.money_info = 0
        self.born_peoples = 0
        self.money_up = 0
        self.taxes_info = 0
        self.food_peoples = 0
        self.tax_effects = 0
        self.clear_up_peoples = 0
        self.max_army_limit = 0
        self.current_consumption = 0
        self.turn = 0
        self.last_turn_loaded = -1  # Последний загруженный номер хода
        self.raw_material_price_history = []  # История цен на еду
        self.current_tax_rate = 0  # Начальная ставка налога — по умолчанию 0%
        self.turns = 0  # Счетчик ходов
        self.tax_set = False  # Флаг, установлен ли налог
        self.custom_tax_rate = 0  # Новый атрибут для хранения пользовательской ставки налога
        self.cities_buildings = {city['name']: {'Больница': 0, 'Фабрика': 0} for city in self.cities}

        self.resources = {
            'Кроны': self.money,
            'Рабочие': self.free_peoples,
            'Сырье': self.raw_material,
            'Население': self.population,
            'Текущее потребление': self.current_consumption,
            'Лимит армии': self.max_army_limit
        }
        self.economic_params = {
            "Аркадия": {"tax_rate": 0.03},
            "Селестия": {"tax_rate": 0.015},
            "Хиперион": {"tax_rate": 0.02},
            "Этерия": {"tax_rate": 0.012},
            "Халидон": {"tax_rate": 0.01},
        }

        self.is_first_run = True  # Флаг для первого запуска
        self.generate_raw_material_price()  # Генерация начальной цены на еду

    def load_data(self, table, columns, condition=None, params=None):
        """
        Универсальный метод для загрузки данных из таблицы базы данных.
        :param table: Имя таблицы.
        :param columns: Список колонок для выборки.
        :param condition: Условие WHERE (строка).
        :param params: Параметры для условия.
        :return: Список кортежей с данными.
        """
        try:
            query = f"SELECT {', '.join(columns)} FROM {table}"
            if condition:
                query += f" WHERE {condition}"
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных из таблицы {table}: {e}")
            return []

    def load_resources(self):
        """Загружает ресурсы из таблицы resources."""
        rows = self.load_data("resources", ["resource_type", "amount"], "faction = ?", (self.faction,))
        resources = {"Рабочие": 0, "Кроны": 0, "Сырье": 0, "Население": 0}
        for resource_type, amount in rows:
            resources[resource_type] = amount
        return resources

    def load_buildings(self):
        """
        Загружает данные о зданиях для текущей фракции из таблицы buildings.
        """
        try:
            self.cursor.execute('''
                SELECT city_name, building_type, count 
                FROM buildings 
                WHERE faction = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Сброс текущих данных о зданиях
            self.cities_buildings = {}
            total_hospitals = 0
            total_factories = 0

            for row in rows:
                city_name, building_type, count = row
                if city_name not in self.cities_buildings:
                    self.cities_buildings[city_name] = {"Больница": 0, "Фабрика": 0}

                # Обновление данных для конкретного города
                if building_type == "Больница":
                    self.cities_buildings[city_name]["Больница"] += count
                    total_hospitals += count
                elif building_type == "Фабрика":
                    self.cities_buildings[city_name]["Фабрика"] += count
                    total_factories += count

            # Обновление глобальных показателей
            self.hospitals = total_hospitals
            self.factories = total_factories

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке зданий: {e}")

    def load_trade_agreements(self):
        """Загружает данные о торговых соглашениях для текущей фракции из таблицы trade_agreements."""
        rows = self.load_data(
            "trade_agreements",
            ["initiator_faction", "target_faction", "initiator_type_resource",
             "initiator_summ_resource", "target_type_resource", "target_summ_resource"],
            "initiator_faction = ? OR target_faction = ?",
            (self.faction, self.faction)
        )
        trade_agreements = []
        for row in rows:
            trade_agreements.append({
                "initiator_faction": row[0],
                "target_faction": row[1],
                "initiator_type_resource": row[2],
                "initiator_summ_resource": row[3],
                "target_type_resource": row[4],
                "target_summ_resource": row[5]
            })
        return trade_agreements

    def load_cities(self):
        """
        Загружает список городов для текущей фракции из таблицы cities.
        Инициализирует self.cities_buildings для каждого города.
        Также подсчитывает количество городов и сохраняет его в self.city_count.
        """
        rows = self.load_data("cities", ["name", "coordinates"], "faction = ?", (self.faction,))
        cities = []
        self.city_count = 0
        self.cities_buildings = {}  # Сброс данных о зданиях
        for row in rows:
            name, coordinates = row
            try:
                # Убираем квадратные скобки и преобразуем координаты
                coordinates = coordinates.strip('[]')
                x, y = map(int, coordinates.split(','))
            except ValueError:
                print(f"Ошибка при разборе координат для города {name}: {coordinates}")
                x, y = 0, 0  # Устанавливаем значения по умолчанию, если координаты некорректны

            cities.append({"name": name, "x": x, "y": y})
            # Инициализируем данные о зданиях для каждого города
            self.cities_buildings[name] = {'Больница': 0, 'Фабрика': 0}
            self.city_count += 1  # Увеличиваем счетчик городов

        return cities

    def build_factory(self, city, quantity=1):
        """Увеличить количество фабрик в указанном городе на заданное количество."""
        if city not in self.cities_buildings:
            self.cities_buildings[city] = {'Больница': 0, 'Фабрика': 0}
        self.cities_buildings[city]['Фабрика'] += quantity  # Обновляем локальные данные
        save_building_change(self.faction, city, "Фабрика", quantity)  # Передаем изменение
        self.load_buildings()  # Пересчитываем общие показатели

    def build_hospital(self, city, quantity=1):
        """Увеличить количество больниц в указанном городе на заданное количество."""
        if city not in self.cities_buildings:
            self.cities_buildings[city] = {'Больница': 0, 'Фабрика': 0}
        self.cities_buildings[city]['Больница'] += quantity
        save_building_change(self.faction, city, "Больница", quantity)
        self.load_buildings()  # Пересчитываем общие показатели


    def cash_build(self, money):
        """Списывает деньги, если их хватает, и возвращает True, иначе False."""
        if self.money >= money:
            self.money -= money
            self.save_resources_to_db()
            return True
        else:
            return False

    def get_income_per_person(self):
        """Получение дохода с одного человека для данной фракции."""
        if self.tax_set and self.custom_tax_rate is not None:
            return self.custom_tax_rate
        params = self.economic_params[self.faction]
        return params["tax_rate"]

    def calculate_tax_income(self):
        """Расчет дохода от налогов с учетом установленной ставки."""
        if not self.tax_set:
            print("Налог не установлен. Прироста от налогов нет.")
            self.taxes = 0
        else:
            # Используем пользовательскую ставку налога или базовую, если пользовательская не задана
            tax_rate = self.custom_tax_rate if self.custom_tax_rate is not None else self.get_base_tax_rate()
            self.taxes = self.population * tax_rate  # Применяем базовую налоговую ставку
        return self.taxes

    def set_taxes(self, new_tax_rate):
        """
        Установка нового уровня налогов и обновление ресурсов.
        """
        self.custom_tax_rate = self.get_base_tax_rate() * new_tax_rate
        self.tax_set = True
        self.calculate_tax_income()

    def tax_effect(self, tax_rate):
        """
        Рассчитывает процентное изменение населения на основе ставки налога.
        :param tax_rate: Текущая ставка налога (в процентах).
        :return: Процент изменения населения (положительное или отрицательное значение).
        """
        if tax_rate >= 90:
            return -69  # Критическая убыль населения (-69%)
        elif 80 <= tax_rate < 90:
            return -51  # Значительная убыль населения (-51%)
        elif 65 <= tax_rate < 80:
            return -37  # Умеренная убыль населения (-37%)
        elif 45 <= tax_rate < 65:
            return -21  # Умеренная убыль населения (-21%)
        elif 35 <= tax_rate < 45:
            return -8  # Небольшая убыль населения (-8%)
        elif 25 <= tax_rate < 35:
            return 0  # Нейтральный эффект (0%)
        elif 16 <= tax_rate < 25:
            return 5  # Небольшой рост (5%)
        elif 10 <= tax_rate < 16:
            return 11  # Небольшой рост населения (+11%)
        elif 1 <= tax_rate < 10:
            return 18  # Небольшой рост населения (+18%)
        else:
            return 34  # Существенный рост населения (+34%)

    def apply_tax_effect(self, tax_rate):
        """
        Применяет эффект налогов на население в виде процентного изменения.
        :param tax_rate: Текущая ставка налога (в процентах).
        :return: Абсолютное изменение населения.
        """
        # Получаем процентное изменение населения
        percentage_change = self.tax_effect(tax_rate)

        # Загружаем текущее население из базы данных
        try:
            self.cursor.execute('''
                SELECT amount
                FROM resources
                WHERE faction = ? AND resource_type = "Население"
            ''', (self.faction,))
            row = self.cursor.fetchone()
            current_population = row[0] if row else 0
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных о населении: {e}")
            current_population = 0

        # Рассчитываем абсолютное изменение населения
        population_change = int(current_population * (percentage_change / 100))

        # Применяем эффект налогов
        self.tax_effects = population_change
        return self.tax_effects

    def calculate_base_tax_rate(self, tax_rate):
        """Формула расчёта базовой налоговой ставки для текущей фракции."""
        params = self.economic_params[self.faction]
        base_tax_rate = params["tax_rate"]  # Базовая ставка налога для текущей фракции

        # Формируем корректировочный коэффициент на основе введённой ставки
        multiplier = tax_rate
        # Возвращаем корректированную налоговую ставку
        return base_tax_rate * multiplier

    def get_base_tax_rate(self):
        """Получение базовой налоговой ставки для текущей фракции."""
        return self.economic_params[self.faction]["tax_rate"]

    def show_popup(self, title, message):
        """Отображает всплывающее окно с сообщением."""
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()

    def load_available_buildings_from_db(self):
        """
        Загружает список доступных зданий для текущей фракции из базы данных.
        """
        try:
            self.cursor.execute('''
                SELECT DISTINCT building_type
                FROM buildings
                WHERE faction = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()
            return [row[0] for row in rows]  # Возвращаем список типов зданий
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке зданий: {e}")
            return []

    def update_cash(self):
        """
        Обновляет ресурсы и сохраняет их в файл.
        """
        self.load_resources()
        self.resources['Кроны'] = self.money
        self.resources['Рабочие'] = self.free_peoples
        self.resources['Сырье'] = self.raw_material
        self.resources['Население'] = self.population
        self.resources['Текущее потребление'] = self.current_consumption
        self.resources['Лимит армии'] = self.max_army_limit
        self.save_resources_to_db()
        return self.resources

    def check_resource_availability(self, resource_type, required_amount):
        """
        Проверяет, достаточно ли у фракции ресурсов для выполнения сделки.

        :param resource_type: Тип ресурса (например, "Сырье", "Кроны", "Рабочие", "Население").
        :param required_amount: Требуемое количество ресурсов.
        :return: True, если ресурсов достаточно, иначе False.
        """
        if resource_type == "Сырье":
            return self.raw_material >= required_amount
        elif resource_type == "Кроны":
            return self.money >= required_amount
        elif resource_type == "Население":
            return self.population >= required_amount
        elif resource_type == "Рабочие":
            return self.free_peoples >= required_amount
        else:
            raise ValueError(f"Неизвестный тип ресурса: {resource_type}")

    def update_resource_deals(self, resource_type='', amount=''):
        """
        Обновляет количество ресурсов фракции на указанное значение.

        :param resource_type: Тип ресурса (например, "Сырье", "Кроны", "Рабочие", "Население").
        :param amount: Изменение количества ресурсов (положительное или отрицательное).
        """
        if resource_type == "Сырье":
            self.resources['Сырье'] += amount
        elif resource_type == "Кроны":
            self.resources['Кроны'] += amount
        elif resource_type == "Население":
            self.resources['Население'] += amount
        elif resource_type == "Рабочие":
            self.resources['Рабочие'] += amount
        else:
            raise ValueError(f"Неизвестный тип ресурса: {resource_type}")


    def update_trade_resources_from_db(self):
        """
        Обновляет ресурсы с учетом торговых соглашений из таблицы trade_agreements.
        Удаляет сделки с agree = 0 и обрабатывает сделки с agree = 1.
        """
        try:
            # Удаляем все сделки с agree = 0
            self.cursor.execute('''
                DELETE FROM trade_agreements 
                WHERE initiator = ? AND agree = 0
            ''', (self.faction,))
            print("Сделки с agree = 0 удалены.")

            # Извлекаем торговые соглашения с agree = 1 для текущей фракции
            self.cursor.execute('''
                SELECT id, initiator, target_faction, initiator_type_resource, 
                       initiator_summ_resource, target_type_resource, target_summ_resource
                FROM trade_agreements 
                WHERE initiator = ? AND agree = 1
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            completed_trades = []  # Список завершенных сделок

            for row in rows:
                trade_id, initiator, target_faction, initiator_type_resource, \
                    initiator_summ_resource, target_type_resource, target_summ_resource = row

                # Если текущая фракция является инициатором сделки
                if initiator == self.faction:
                    # Проверяем наличие ресурсов для выполнения сделки
                    if not self.check_resource_availability(initiator_type_resource, initiator_summ_resource):
                        print(f"Недостаточно ресурсов для выполнения сделки ID={trade_id}.")
                        continue  # Пропускаем сделку, если недостаточно ресурсов

                    # Отнимаем ресурс, который отдает инициатор
                    self.update_resource_deals(initiator_type_resource, -initiator_summ_resource)

                    # Добавляем ресурс, который получает инициатор
                    self.update_resource_deals(target_type_resource, target_summ_resource)

                # Если текущая фракция является целевой фракцией
                elif target_faction == self.faction:
                    # Проверяем наличие ресурсов для выполнения сделки
                    if not self.check_resource_availability(target_type_resource, target_summ_resource):
                        print(f"Недостаточно ресурсов для выполнения сделки ID={trade_id}.")
                        continue  # Пропускаем сделку, если недостаточно ресурсов

                    # Отнимаем ресурс, который отдает целевая фракция
                    self.update_resource_deals(target_type_resource, -target_summ_resource)

                    # Добавляем ресурс, который получает целевая фракция
                    self.update_resource_deals(initiator_type_resource, initiator_summ_resource)

                # Добавляем сделку в список завершенных
                completed_trades.append(trade_id)

            # Удаляем завершенные сделки из таблицы trade_agreements
            for trade_id in completed_trades:
                self.cursor.execute('''
                    DELETE FROM trade_agreements 
                    WHERE id = ?
                ''', (trade_id,))
                print(f"Сделка ID={trade_id} удалена после завершения.")

            self.save_resources_to_db()

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении ресурсов на основе торговых соглашений: {e}")

    def load_resources_from_db(self):
        """
        Загружает текущие ресурсы фракции из таблицы resources.
        """
        try:
            self.cursor.execute('''
                SELECT resource_type, amount
                FROM resources
                WHERE faction = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Инициализация ресурсов по умолчанию
            self.money = 0
            self.free_peoples = 0
            self.raw_material = 0
            self.population = 0

            # Обновление ресурсов на основе данных из базы данных
            for resource_type, amount in rows:
                if resource_type == "Кроны":
                    self.money = amount
                elif resource_type == "Рабочие":
                    self.free_peoples = amount
                elif resource_type == "Сырье":
                    self.raw_material = amount
                elif resource_type == "Население":
                    self.population = amount

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке ресурсов: {e}")

    def save_resources_to_db(self):
        """
        Сохраняет текущие ресурсы фракции в таблицу resources.
        """
        try:
            for resource_type, amount in self.resources.items():
                # Проверяем, существует ли запись
                self.cursor.execute('''
                    SELECT amount
                    FROM resources
                    WHERE faction = ? AND resource_type = ?
                ''', (self.faction, resource_type))
                existing_record = self.cursor.fetchone()

                if existing_record:
                    # Обновляем существующую запись
                    self.cursor.execute('''
                        UPDATE resources
                        SET amount = ?
                        WHERE faction = ? AND resource_type = ?
                    ''', (amount, self.faction, resource_type))
                else:
                    # Создаем новую запись
                    self.cursor.execute('''
                        INSERT INTO resources (faction, resource_type, amount)
                        VALUES (?, ?, ?)
                    ''', (self.faction, resource_type, amount))

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении ресурсов в базу данных: {e}")

    def update_ally_resources_from_db(self):
        """
        Обновляет ресурсы от союзников из таблицы trade_agreements.
        """
        try:
            self.cursor.execute('''
                SELECT initiator, target_faction, initiator_type_resource, 
                       initiator_summ_resource, target_type_resource, target_summ_resource
                FROM trade_agreements 
                WHERE initiator = ? OR target_faction = ?
            ''', (self.faction, self.faction))
            rows = self.cursor.fetchall()
            for row in rows:
                initiator_faction, target_faction, initiator_type_resource, initiator_summ_resource, \
                    target_type_resource, target_summ_resource = row

                if initiator_faction == self.faction:
                    # Игрок — инициатор сделки
                    if initiator_type_resource == "Сырье":
                        self.raw_material -= initiator_summ_resource
                    elif initiator_type_resource == "Кроны":
                        self.money -= initiator_summ_resource
                    elif initiator_type_resource == "Население":
                        self.population -= initiator_summ_resource
                    elif initiator_type_resource == "Рабочие":
                        self.free_peoples -= initiator_summ_resource

                elif target_faction == self.faction:
                    # Игрок — получатель сделки
                    if target_type_resource == "Сырье":
                        self.raw_material -= target_summ_resource
                    elif target_type_resource == "Кроны":
                        self.money -= target_summ_resource
                    elif target_type_resource == "Население":
                        self.population -= target_summ_resource
                    elif target_type_resource == "Рабочие":
                        self.free_peoples -= target_summ_resource

                    # Получаем ресурс от инициатора
                    if initiator_type_resource == "Сырье":
                        self.raw_material += initiator_summ_resource
                    elif initiator_type_resource == "Кроны":
                        self.money += initiator_summ_resource
                    elif initiator_type_resource == "Население":
                        self.population += initiator_summ_resource
                    elif initiator_type_resource == "Рабочие":
                        self.free_peoples += initiator_summ_resource
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении ресурсов от союзников: {e}")

    def load_relations(self):
        """
        Загружает текущие отношения из таблицы relations в базе данных.
        Возвращает словарь, где ключи — названия фракций, а значения — уровни отношений.
        """
        try:
            self.cursor.execute('''
                SELECT faction2, relationship
                FROM relations
                WHERE faction1 = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь, преобразуя значения в числа
            relations = {faction2: int(relationship) for faction2, relationship in rows}
            return relations

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений из таблицы relations: {e}")
            return {}

    def load_political_system(self):
        """
        Загружает текущую политическую систему фракции из базы данных.
        """
        try:
            query = "SELECT system FROM political_systems WHERE faction = ?"
            self.cursor.execute(query, (self.faction,))
            result = self.cursor.fetchone()
            return result[0] if result else "Капитализм"  # По умолчанию "Капитализм"
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политической системы: {e}")
            return "Капитализм"

    def apply_player_bonuses(self):
        """
        Применяет бонусы игроку на основе его политической системы.
        Также изменяет отношения с другими фракциями каждые 4 хода.
        """
        try:
            # Применяем бонусы к ресурсам
            system = self.load_political_system()
            if system == "Капитализм":
                # +15% Крон от общего прироста
                crowns_bonus = int(self.money_up * 0.15)
                self.money += crowns_bonus
            elif system == "Коммунизм":
                # +15% Сырья от общего прироста
                raw_material_bonus = int(self.food_info * 0.15)
                self.raw_material += raw_material_bonus

            # Изменяем отношения с другими фракциями каждые 4 хода
            if self.turn % 4 == 0:
                print("Выполняем обновление отношений...")
                self.update_relations_based_on_political_system()

        except Exception as e:
            print(f"Ошибка при применении бонусов игроку: {e}")

    def load_political_system_for_faction(self, faction):
        """
        Загружает политическую систему указанной фракции.
        """
        try:
            query = "SELECT system FROM political_systems WHERE faction = ?"
            self.cursor.execute(query, (faction,))
            result = self.cursor.fetchone()
            return result[0] if result else "Капитализм"  # По умолчанию "Капитализм"
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политической системы для фракции {faction}: {e}")
            return "Капитализм"

    def update_relations_based_on_political_system(self):
        """
        Изменяет отношения на основе политической системы каждые 4 хода.
        """
        current_system = self.load_political_system()
        all_factions = self.load_relations()

        for faction, relation_level in all_factions.items():
            other_system = self.load_political_system_for_faction(faction)

            if current_system == other_system:
                # Улучшаем отношения на +2%
                new_relation = min(relation_level + 2, 100)
                print(f"Улучшение отношений с {faction}: {relation_level} -> {new_relation}")
            else:
                # Ухудшаем отношения на -2%
                new_relation = max(relation_level - 2, 0)
                print(f"Ухудшение отношений с {faction}: {relation_level} -> {new_relation}")

            # Обновляем уровень отношений в базе данных
            self.update_relation_in_db(faction, new_relation)

    def update_relation_in_db(self, faction, new_relation):
        """
        Обновляет уровень отношений в базе данных.
        """
        try:
            print(f"Обновляем отношения для {faction}: новое значение = {new_relation}")
            query = """
                UPDATE relations
                SET relationship = ?
                WHERE faction1 = ? AND faction2 = ?
            """
            self.cursor.execute(query, (new_relation, self.faction, faction))
            self.conn.commit()
            print(f"Отношения успешно обновлены для {faction}.")
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении отношений для фракции {faction}: {e}")

    def calculate_army_limit(self):
        """
        Рассчитывает максимальный лимит армии на основе базового значения и бонуса от городов.
        """
        base_limit = 1_000_000  # Базовый лимит 1 млн
        city_bonus = 100_000 * len(self.cities)  # Бонус за каждый город
        total_limit = base_limit + city_bonus
        return total_limit

    def calculate_and_deduct_consumption(self):
        """
        Метод для расчета потребления сырья гарнизонами текущей фракции
        и вычета суммарного потребления из self.raw_material.
        Также проверяет лимиты потребления и при необходимости сокращает армию,
        уменьшая количество юнитов на 15% от их числа.
        """
        try:
            self.current_consumption = 0
            # Шаг 1: Выгрузка всех гарнизонов из таблицы garrisons
            self.cursor.execute("""
                SELECT city_id, unit_name, unit_count 
                FROM garrisons
            """)
            garrisons = self.cursor.fetchall()

            # Шаг 2: Для каждого гарнизона находим соответствующий юнит в таблице units
            faction_units = {}
            for garrison in garrisons:
                city_id, unit_name, unit_count = garrison

                # Проверяем, к какой фракции принадлежит юнит
                if unit_name not in faction_units:
                    self.cursor.execute("""
                        SELECT consumption, faction 
                        FROM units 
                        WHERE unit_name = ?
                    """, (unit_name,))
                    unit_data = self.cursor.fetchone()

                    if unit_data:
                        consumption, unit_faction = unit_data
                        faction_units[unit_name] = {
                            'consumption': consumption,
                            'faction': unit_faction
                        }
                    else:
                        continue

                # Учитываем только юниты текущей фракции
                if faction_units[unit_name]['faction'] == self.faction:
                    # Расчет потребления для данного типа юнита
                    self.current_consumption += faction_units[unit_name]['consumption'] * unit_count

            # Шаг 3: Расчет базового лимита
            base_limit = 1_000_000  # Базовый лимит 1 млн
            city_bonus = 100_000 * len(self.cities)  # Бонус за каждый город
            total_limit = base_limit + city_bonus

            # Шаг 4: Проверка превышения лимита
            if self.current_consumption > total_limit:
                excess_consumption = self.current_consumption - total_limit
                starving_units = []  # Список юнитов, которые голодают

                # Логика сокращения армии на 15% от числа юнитов
                for garrison in garrisons:
                    city_id, unit_name, unit_count = garrison

                    if unit_count > 0 and faction_units[unit_name]['faction'] == self.faction:
                        # Сокращаем не более 15% от текущего количества юнитов
                        reduction = max(1, int(unit_count * 0.15))  # Минимум 1 юнит

                        # Обновляем данные в базе
                        self.cursor.execute("""
                            UPDATE garrisons
                            SET unit_count = unit_count - ?
                            WHERE city_id = ? AND unit_name = ?
                        """, (reduction, city_id, unit_name))

                        # Обновляем переменные
                        new_unit_count = unit_count - reduction
                        starving_units.append((unit_name, reduction))  # Добавляем в список голодающих юнитов

                        # Если количество юнитов стало <= 0, удаляем запись
                        if new_unit_count <= 0:
                            self.cursor.execute("""
                                DELETE FROM garrisons
                                WHERE city_id = ? AND unit_name = ?
                            """, (city_id, unit_name))
                        else:
                            # Пересчитываем потребление для оставшихся юнитов
                            self.current_consumption -= faction_units[unit_name]['consumption'] * reduction

                        # Уменьшаем избыточное потребление
                        excess_consumption -= faction_units[unit_name]['consumption'] * reduction

                        # Если избыточное потребление устранено, завершаем цикл
                        if excess_consumption <= 0:
                            break

                # Выводим уведомление о голоде
                if starving_units:
                    message = "Армия голодает и будет сокращаться:\n"
                    for unit_name, reduction in starving_units:
                        message += f"- {unit_name}: умерло {reduction} юнитов\n"
                    show_message("Голод в армии", message)

                print(f"Армия сокращена до допустимого лимита.")

            # Шаг 5: Вычитание общего потребления из сырья фракции
            self.raw_material -= self.current_consumption
            print(f"Общее потребление сырья: {self.current_consumption}")
            print(f"Остаток сырья у фракции: {self.raw_material}")

            # Обновляем текущее потребление в ресурсах
            self.resources['Текущее потребление'] = self.current_consumption
            self.resources['Лимит армии'] = total_limit

            # Сохраняем ресурсы в базу данных
            self.save_resources_to_db()

        except Exception as e:
            print(f"Произошла ошибка: {e}")

            # Обновляем текущее потребление в ресурсах
            self.resources['Текущее потребление'] = self.current_consumption
            self.resources['Лимит армии'] = total_limit



    def update_resources(self):
        """
        Обновление текущих ресурсов с учетом данных из базы данных.
        Все расчеты выполняются на основе таблиц в базе данных.
        """
        print('-----------------ХОДИТ ИГРОК-----------', self.faction.upper)
        # Обновляем данные о зданиях из таблицы buildings
        self.turn += 1
        self.load_buildings()

        # Генерируем новую цену на сырье
        self.generate_raw_material_price()

        # Обновляем ресурсы на основе торговых соглашений
        self.update_trade_resources_from_db()

        # Коэффициенты для каждой фракции
        faction_coefficients = {
            'Аркадия': {'money_loss': 100, 'food_gain': 600, 'food_loss': 1.4},
            'Селестия': {'money_loss': 200, 'food_gain': 540, 'food_loss': 1.1},
            'Хиперион': {'money_loss': 200, 'food_gain': 530, 'food_loss': 0.9},
            'Этерия': {'money_loss': 300, 'food_gain': 500, 'food_loss': 0.5},
            'Халидон': {'money_loss': 300, 'food_gain': 500, 'food_loss': 0.4},
        }

        # Получение коэффициентов для текущей фракции
        faction = self.faction
        if faction not in faction_coefficients:
            raise ValueError(f"Фракция '{faction}' не найдена.")
        coeffs = faction_coefficients[faction]

        # Обновление ресурсов с учетом коэффициентов
        self.born_peoples = int(self.hospitals * 500)
        self.work_peoples = int(self.factories * 200)
        self.clear_up_peoples = (self.born_peoples - self.work_peoples + self.tax_effects) + int(
            self.city_count * (self.population / 100))

        # Загружаем текущие значения ресурсов из базы данных
        self.load_resources_from_db()

        # Выполняем расчеты
        self.free_peoples += self.clear_up_peoples
        self.money += int(self.calculate_tax_income() - (self.hospitals * coeffs['money_loss']))
        self.money_info = int(self.hospitals * coeffs['money_loss'])
        self.money_up = int(self.calculate_tax_income() - (self.hospitals * coeffs['money_loss']))
        self.taxes_info = int(self.calculate_tax_income())

        # Учитываем, что одна фабрика может прокормить 1000 людей
        self.raw_material += int((self.factories * 1000) - (self.population * coeffs['food_loss']))
        self.food_info = (
                int((self.factories * 1000) - (self.population * coeffs['food_loss'])) - self.current_consumption)
        self.food_peoples = int(self.population * coeffs['food_loss'])

        # Проверяем, будет ли население увеличиваться
        if self.raw_material > 0:
            self.population += int(self.clear_up_peoples)  # Увеличиваем население только если есть Сырье
        else:
            # Логика убыли населения при недостатке Сырья
            if self.population > 100:
                loss = int(self.population * 0.45)  # 45% от населения
                self.population -= loss
            else:
                loss = min(self.population, 50)  # Обнуление по 50, но не ниже 0
                self.population -= loss
            self.free_peoples = 0  # Все рабочие обнуляются, так как Сырья нет

        # Проверка, чтобы ресурсы не опускались ниже 0 и не превышали максимальные значения
        self.resources.update({
            "Кроны": max(min(int(self.money), 10_000_000_000), 0),  # Не более 10 млрд
            "Рабочие": max(min(int(self.free_peoples), 10_000_000), 0),  # Не более 10 млн
            "Сырье": max(min(int(self.raw_material), 10_000_000_000), 0),  # Не более 10 млрд
            "Население": max(min(int(self.population), 100_000_000), 0),  # Не более 100 млн
            "Текущее потребление": self.current_consumption,  # Используем рассчитанное значение
            "Лимит армии": self.max_army_limit
        })
        self.money = self.resources['Кроны']
        self.free_peoples = self.resources['Рабочие']
        self.raw_material = self.resources['Сырье']
        self.population = self.resources['Население']
        self.max_army_limit = self.resources['Лимит армии']
        self.current_consumption = self.resources['Текущее потребление']
        # Применяем бонусы игроку
        self.apply_player_bonuses()
        self.max_army_limit = self.calculate_army_limit()
        # Списываем потребление войсками
        self.calculate_and_deduct_consumption()
        # Сохраняем обновленные ресурсы в базу данных
        self.save_resources_to_db()

        print(f"Ресурсы обновлены: {self.resources}, Больницы: {self.hospitals}, Фабрики: {self.factories}")


    def get_resource_now(self, resource_type):
        """
        Возвращает текущее значение указанного ресурса.
        :param resource_type: Тип ресурса (например, "Кроны").
        :return: Значение ресурса.
        """
        return self.resources.get(resource_type, 0)

    def update_resource_now(self, resource_type, new_amount):
        if resource_type == 'Кроны':
            self.money = new_amount
        elif resource_type == 'Рабочие':
            self.free_peoples = new_amount
        elif resource_type == 'Сырье':
            self.raw_material = new_amount
        elif resource_type == 'Население':
            self.population = new_amount

    def get_resources(self):
        """Получение текущих ресурсов с форматированием чисел."""
        formatted_resources = {}

        for resource, value in self.resources.items():
            formatted_resources[resource] = format_number(value)

        return formatted_resources

    def end_game(self):
        if self.population == 0:
            return False

    def buildings_info_fraction(self):
        if self.faction == 'Аркадия':
            return 100
        if self.faction == 'Селестия':
            return 200
        if self.faction == 'Хиперион':
            return 200
        if self.faction == 'Этерия':
            return 300
        if self.faction == 'Халидон':
            return 300

    def initialize_raw_material_prices(self):
        """Инициализация истории цен на сырье"""
        for _ in range(25):  # Генерируем 25 случайных цен
            self.generate_raw_material_price()

    def generate_raw_material_price(self):
        """
        Генерация случайной цены на сырье.
        Цена генерируется только при изменении номера хода.
        """
        # Загрузка номера хода из таблицы turn
        try:
            self.cursor.execute('''
                SELECT turn_count 
                FROM turn
                ORDER BY turn_count DESC
                LIMIT 1
            ''')
            row = self.cursor.fetchone()
            if row:
                current_turn = row[0]  # Текущий номер хода
            else:
                current_turn = 1  # Если записей нет, начинаем с нуля
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке номера хода: {e}")
            current_turn = 1  # В случае ошибки устанавливаем значение по умолчанию

        # Проверка, был ли уже загружен текущий ход
        if current_turn == self.last_turn_loaded:
            return  # Цена уже сгенерирована для этого хода

        # Генерация новой цены
        if current_turn == 1:  # Если это первый ход
            self.current_raw_material_price = random.randint(800, 42000)
            self.raw_material_price_history.append(self.current_raw_material_price)
        else:
            # Генерация новой цены на основе текущей
            self.current_raw_material_price = self.raw_material_price_history[-1] + random.randint(-3700, 3500)
            self.current_raw_material_price = max(
                800, min(42000, self.current_raw_material_price)  # Ограничиваем диапазон
            )
            self.raw_material_price_history.append(self.current_raw_material_price)

        # Ограничение длины истории цен до 25 элементов
        if len(self.raw_material_price_history) > 25:
            self.raw_material_price_history.pop(0)

        # Обновляем значение последнего загруженного хода
        self.last_turn_loaded = current_turn

    def trade_raw_material(self, action, quantity):
        """
        Торговля сырьем через таблицу resources.
        :param action: Действие ('buy' для покупки, 'sell' для продажи).
        :param quantity: Количество лотов (1 лот = 10,000 единиц сырья).
        """
        # Преобразуем количество лотов в единицы сырья
        total_quantity = quantity * 10000
        total_cost = self.current_raw_material_price * quantity

        if action == 'buy':  # Покупка сырья
            # Проверяем, достаточно ли денег для покупки
            if self.money >= total_cost:
                # Обновляем ресурсы
                self.money -= total_cost
                self.raw_material += total_quantity
                # Сохраняем изменения в базе данных
                self.save_resources_to_db()
                return True  # Операция успешна
            else:
                show_message("Недостаточно денег", "У вас недостаточно денег для покупки сырья.")
                return False

        elif action == 'sell':  # Продажа сырья
            # Проверяем, достаточно ли сырья для продажи
            if self.raw_material >= total_quantity:
                # Обновляем ресурсы
                self.money += total_cost
                self.raw_material -= total_quantity
                # Сохраняем изменения в базе данных
                self.save_resources_to_db()
                return True  # Операция успешна
            else:
                show_message("Недостаточно сырья", "У вас недостаточно сырья для продажи.")
                return False

        return False  # Операция не удалась

    def get_raw_material_price_history(self):
        """Получение табличного представления истории цен на сырье"""
        history = []
        for i, price in enumerate(self.raw_material_price_history):
            # Вместо строки создаем кортеж (номер хода, цена)
            history.append((f"Ход {i + 1}", price))
        return history


def show_message(title, message):
    layout = BoxLayout(orientation='vertical', padding=10)
    label = Label(text=message, size_hint=(1, 0.8))
    close_btn = Button(text="Закрыть", size_hint=(1, 0.2))

    layout.add_widget(label)
    layout.add_widget(close_btn)

    popup = Popup(title=title, content=layout, size_hint=(0.6, 0.4))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()


# Логика для отображения сообщения об ошибке средств
def show_error_message(message):
    error_popup = Popup(title="Ошибка", content=Label(text=message), size_hint=(0.5, 0.5))
    error_popup.open()


def build_structure(building, city, faction, quantity, on_complete):
    if building == "Здания" or city == "Города":
        show_error_message("Выберите здание для постройки и город!")
        return

    # Проверяем, что количество зданий больше 0
    if quantity <= 0:
        show_error_message("Количество зданий должно быть больше 0!")
        return

    # Ищем город в списке городов фракции
    city_found = next((c for c in faction.cities if c.get('name') == city), None)
    if city_found is None:
        show_error_message("Выбранный город не найден!")
        return

    # Определяем стоимость постройки одного здания
    building_cost = 200 if building == "Фабрика" else 300 if building == "Больница" else None
    if building_cost is None:
        show_error_message("Неизвестный тип здания!")
        return

    total_cost = building_cost * quantity

    # Проверяем, хватает ли денег на постройку всех зданий
    if not faction.cash_build(total_cost):
        show_error_message(f"Недостаточно денег для постройки {quantity} зданий!\nСтоимость: {total_cost} крон")
        return

    # Загружаем актуальные данные о зданиях в городе из базы данных
    faction.load_buildings()  # Обновляем данные о зданиях
    city_buildings = faction.cities_buildings.get(city, {"Больница": 0, "Фабрика": 0})

    # Текущее количество зданий в городе
    current_factories = city_buildings.get("Фабрика", 0)
    current_hospitals = city_buildings.get("Больница", 0)
    total_buildings = current_factories + current_hospitals

    # Максимальное количество зданий в городе
    max_buildings_per_city = 250

    # Проверяем, не превышает ли новое количество зданий лимит
    if total_buildings + quantity > max_buildings_per_city:
        show_error_message(
            f"Невозможно построить больше зданий!\n"
            f"Максимум зданий в городе: {max_buildings_per_city}\n"
            f"Текущее количество зданий: {total_buildings}"
        )
        return

    # Строим здания за один вызов
    if building == "Фабрика":
        faction.build_factory(city_found['name'], quantity)  # Передаем количество
    elif building == "Больница":
        faction.build_hospital(city_found['name'], quantity)  # Передаем количество

    # Выполняем функцию завершения постройки
    if on_complete:
        Clock.schedule_once(on_complete, 0.5)  # Задержка 0.5 секунды для отображения сообщений


def open_build_popup(faction):
    def rebuild_popup(*args):
        build_popup.dismiss()
        open_build_popup(faction)

    # Проверка наличия городов
    faction.cities = faction.load_cities()
    if not faction.cities:
        show_error_message("Список городов пуст.")
        return

    build_popup = Popup(
        title="Состояние государства",
        size_hint=(0.8, 0.8),
        background_color=(0.1, 0.1, 0.1, 1),  # Темный фон окна
        title_color=(1, 1, 1, 1),  # Белый цвет заголовка
    )

    main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

    # Таблица статистики с прокруткой
    scroll_view = ScrollView(size_hint=(1, 0.6), do_scroll_x=False, do_scroll_y=True)
    stats_table = GridLayout(
        cols=2,
        size_hint_y=None,
        spacing=5,  # Расстояние между ячейками
        padding=[20, 20, 20, 20],
    )
    stats_table.bind(minimum_height=stats_table.setter('height'))  # Автоматический ресайз высоты

    # Заполнение таблицы данными
    stats_data = [
        ("1 больница (за ход):",
         f"+500 рабочих / -{faction.buildings_info_fraction()} крон"),
        ("1 фабрика (за ход):", "+1000 сырья / -200 рабочих"),
        ("Количество больниц:", faction.hospitals),
        ("Количество фабрик:", faction.factories),
        ("Количество рабочих на фабриках:", faction.work_peoples),
        ("Чистый прирост рабочих:", faction.clear_up_peoples),
        ("Потребление денег больницами:", faction.money_info),
        ("Чистое производство сырья:", faction.food_info),
        ("Чистый прирост денег:", faction.money_up),
        ("Доход от налогов:", faction.taxes_info),
        ("Эффект от налогов (Рост населения):",
         faction.apply_tax_effect(int(faction.current_tax_rate[:-1])) if faction.tax_set else "Налог не установлен"),
    ]

    # Функция для расчета размера шрифта
    def calculate_font_size():
        screen_width, _ = Window.size
        base_font_size = max(7, min(16, screen_width / 360 * 10))
        return int(base_font_size)

    font_size = calculate_font_size()

    for label_text, value in stats_data:
        # Добавляем описание параметра
        stats_table.add_widget(Label(
            text=label_text,
            color=(1, 1, 1, 1),  # Белый цвет текста
            font_size=f'{font_size}sp',
            bold=True,
            size_hint_y=None,
            height=40,
        ))

        # Добавляем значение параметра с подсветкой
        if isinstance(value, (int, float)):
            value_color = (1, 0, 0, 1) if value < 0 else (0, 1, 0, 1)
        else:
            value_color = (1, 1, 1, 1)

        stats_table.add_widget(Label(
            text=str(value),
            color=value_color,
            font_size=f'{font_size}sp',
            bold=True,
            size_hint_y=None,
            height=40,
        ))

    # Привязываем фон к размеру таблицы
    with stats_table.canvas.before:
        Color(0.2, 0.2, 0.2, 1)  # Серый фон
        stats_table.background_rect = RoundedRectangle(
            size=stats_table.size,
            pos=stats_table.pos,
            radius=[10]
        )

    def update_background_rect(instance, value):
        Clock.schedule_once(lambda dt: setattr(instance.background_rect, 'size', instance.size), 0)
        Clock.schedule_once(lambda dt: setattr(instance.background_rect, 'pos', instance.pos), 0)

    stats_table.bind(size=update_background_rect, pos=update_background_rect)

    scroll_view.add_widget(stats_table)
    main_layout.add_widget(scroll_view)

    # Нижний блок с кнопками
    bottom_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)

    # Блок выбора зданий
    building_box = BoxLayout(orientation='vertical', spacing=10)
    building_main_button = Button(
        text="Выберите здание",
        size_hint=(1, None),
        height=44,
        background_color=(0.3, 0.4, 0.9, 1),
    )
    building_dropdown = DropDown(auto_dismiss=False)

    # Статические элементы для выбора зданий
    available_buildings = ["Больница", "Фабрика"]

    for building in available_buildings:
        btn = Button(
            text=building,
            size_hint_y=None,
            height=44,
            background_color=(0.4, 0.5, 1, 1),
        )
        btn.bind(on_release=lambda btn: building_dropdown.select(btn.text))
        building_dropdown.add_widget(btn)

    building_main_button.bind(on_release=building_dropdown.open)
    building_dropdown.bind(on_select=lambda instance, x: setattr(building_main_button, 'text', x))

    building_box.add_widget(Label(text="Здания:", size_hint=(1, None), height=30, color=(1, 1, 1, 1)))
    building_box.add_widget(building_main_button)
    bottom_layout.add_widget(building_box)

    # Блок выбора города
    city_box = BoxLayout(orientation='vertical', spacing=10)
    city_main_button = Button(
        text="Выберите город",
        size_hint=(1, None),
        height=44,
        background_color=(0.3, 0.8, 0.4, 1),
    )
    city_dropdown = DropDown(auto_dismiss=False)

    for city in faction.cities:
        city_text = city.get('name', 'Неизвестный город')
        btn = Button(
            text=city_text,
            size_hint_y=None,
            height=44,
            background_color=(0.4, 0.9, 0.5, 1),
        )
        btn.bind(on_release=lambda btn: city_dropdown.select(btn.text))
        city_dropdown.add_widget(btn)

    city_main_button.bind(on_release=city_dropdown.open)
    city_dropdown.bind(on_select=lambda instance, x: setattr(city_main_button, 'text', x))

    city_box.add_widget(Label(text="Города:", size_hint=(1, None), height=30, color=(1, 1, 1, 1)))
    city_box.add_widget(city_main_button)
    bottom_layout.add_widget(city_box)

    # Поле для ввода количества зданий
    quantity_input = TextInput(
        text="1",
        size_hint=(None, None),
        width=50,
        height=44,
        input_filter="int",
        multiline=False,
    )
    bottom_layout.add_widget(quantity_input)

    # Кнопка "Построить"
    build_button = Button(
        text="Построить",
        size_hint=(None, None),
        size=(100, 44),
        background_color=(1, 0.4, 0.4, 1),
    )

    def on_build_button_press(instance):
        try:
            quantity = int(quantity_input.text)
            if quantity <= 0:
                raise ValueError("Количество зданий должно быть больше 0.")
        except ValueError as e:
            show_error_message(str(e))
            return

        build_structure(
            building_main_button.text,
            city_main_button.text,
            faction,
            quantity,
            rebuild_popup
        )

    build_button.bind(on_release=on_build_button_press)
    bottom_layout.add_widget(build_button)

    main_layout.add_widget(bottom_layout)

    build_popup.content = main_layout
    build_popup.open()


#---------------------------------------------------------------


def open_trade_popup(game_instance):
    """Открытие окна торговли с историей цен"""
    # Обновляем данные из базы данных
    game_instance.load_resources_from_db()

    # Генерируем новую цену, если это необходимо
    game_instance.generate_raw_material_price()

    trade_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

    # Блок бегущей строки (история цен)
    price_history_text = ""
    previous_price = None

    for i, price in enumerate(game_instance.raw_material_price_history):
        # Определяем цвет цены
        if previous_price is not None:
            color_tag = "[color=00FF00]" if price > previous_price else "[color=FF0000]"
        else:
            color_tag = "[color=FFFFFF]"

        # Формируем текст с отступами
        price_history_text += f"{color_tag}Ход {i + 1}: {price}[/color]    "
        previous_price = price

    # Создаем Label для бегущей строки
    history_label = Label(
        text=price_history_text,
        markup=True,
        font_size=16,
        color=(1, 1, 1, 1),
        size_hint=(None, None),
        size=(len(price_history_text) * 10, 40)
    )

    # Добавляем Label в ScrollView
    scroll_view = ScrollView(size_hint=(1, None), height=40, do_scroll_x=True, do_scroll_y=False)
    scroll_view.add_widget(history_label)

    # Анимация бегущей строки
    def animate_history():
        animation = Animation(x=-history_label.width, duration=15) + Animation(x=0, duration=0)
        animation.repeat = True
        animation.start(history_label)

    Clock.schedule_once(lambda dt: animate_history(), 0)

    # Размещаем бегущую строку сверху окна
    trade_layout.add_widget(scroll_view)

    # Блок текущей цены (по центру)
    current_price_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.3), padding=10)

    # Логика для определения цвета цены
    if len(game_instance.raw_material_price_history) > 1:
        previous_price = game_instance.raw_material_price_history[-2]
        current_price = game_instance.current_raw_material_price
        arrow_color = (0, 1, 0, 1) if current_price > previous_price else (1, 0, 0, 1)
    else:
        arrow_color = (0.5, 0.5, 0.5, 1)

    # Отображение текущей цены
    current_price_label = Label(
        text=f"Текущая цена: {game_instance.current_raw_material_price}",
        font_size=40,
        bold=True,
        color=arrow_color,
        halign="center",
        valign="middle"
    )
    current_price_label.bind(size=current_price_label.setter('text_size'))  # Для выравнивания текста
    current_price_layout.add_widget(current_price_label)

    trade_layout.add_widget(current_price_layout)

    # Блок кнопок "Купить" и "Продать"
    button_container = BoxLayout(orientation='vertical', size_hint=(1, 0.4), spacing=10)

    # Надпись "Цена за 1 лот = 10,000 единиц сырья"
    lot_info_label = Label(
        text="Цена за 1 лот = 10,000 единиц сырья",
        font_size=18,
        color=(1, 1, 1, 1),
        size_hint=(1, 0.3),
        halign="center",
        valign="middle"
    )
    lot_info_label.bind(size=lot_info_label.setter('text_size'))
    button_container.add_widget(lot_info_label)

    # Кнопки "Купить" и "Продать"
    button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.7), spacing=20)

    buy_btn = Button(
        text="Купить",
        background_color=(0, 1, 0, 1),
        size_hint=(0.5, 1),
        background_normal='',
        background_down=''
    )
    sell_btn = Button(
        text="Продать",
        background_color=(1, 0, 0, 1),
        size_hint=(0.5, 1),
        background_normal='',
        background_down=''
    )

    # Стилизация кнопок
    with buy_btn.canvas.before:
        Color(0, 1, 0, 1)
        buy_btn.rect = RoundedRectangle(size=buy_btn.size, pos=buy_btn.pos, radius=[10])
    with sell_btn.canvas.before:
        Color(1, 0, 0, 1)
        sell_btn.rect = RoundedRectangle(size=sell_btn.size, pos=sell_btn.pos, radius=[10])

    def update_rect(instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    buy_btn.bind(pos=update_rect, size=update_rect)
    sell_btn.bind(pos=update_rect, size=update_rect)

    button_layout.add_widget(buy_btn)
    button_layout.add_widget(sell_btn)
    button_container.add_widget(button_layout)

    trade_layout.add_widget(button_container)

    # Поле ввода количества лотов
    quantity_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2), spacing=10)

    quantity_label = Label(
        text="Введите количество лотов для торговли сырьем:",
        font_size=16,
        color=(1, 1, 1, 1),
        size_hint=(1, 0.4),
        halign="center",
        valign="middle"
    )
    quantity_label.bind(size=quantity_label.setter('text_size'))

    quantity_input = TextInput(
        hint_text="1 лот = 10,000 единиц",
        multiline=False,
        font_size=16,
        input_filter='int',
        size_hint=(1, 0.6)
    )

    quantity_layout.add_widget(quantity_label)
    quantity_layout.add_widget(quantity_input)
    trade_layout.add_widget(quantity_layout)

    # Создаем попап
    trade_popup = Popup(title="Торговля сырьем", content=trade_layout, size_hint=(0.8, 0.8))

    # Обработка покупки сырья
    buy_btn.bind(on_press=lambda x: handle_trade(game_instance, 'buy', quantity_input.text, trade_popup))
    # Обработка продажи сырья
    sell_btn.bind(on_press=lambda x: handle_trade(game_instance, 'sell', quantity_input.text, trade_popup))

    trade_popup.open()


def handle_trade(game_instance, action, quantity, trade_popup):
    """Обработка торговли (покупка/продажа сырья)"""
    try:
        # Проверяем, что количество введено
        if not quantity or int(quantity) <= 0:
            raise ValueError("Не было введено количество лотов. Пожалуйста, введите количество лотов.")

        quantity = int(quantity)

        # Проверяем, что количество сырья для продажи не превышает доступное
        if action == 'sell' and quantity * 10000 > game_instance.resources["Сырье"]:
            raise ValueError("Недостаточно сырья для продажи.")

        result = game_instance.trade_raw_material(action, quantity)

        if result:  # Если торговля прошла успешно
            show_message("Успех", f"{'Куплено' if action == 'buy' else 'Продано'} {quantity} лотов сырья.")
        else:  # Если операция не удалась
            show_message("Ошибка", "Не удалось завершить операцию.")
    except ValueError as e:
        show_message("Ошибка", str(e))
    trade_popup.dismiss()  # Закрываем попап после операции


#-----------------------------------
def open_tax_popup(faction):
    # Создаем попап с анимированной тенью и градиентным фоном
    tax_popup = Popup(
        title="Управление налогами",
        size_hint=(0.8, 0.6),
        background_color=(0.05, 0.05, 0.05, 0.95),
        title_color=(0.8, 0.8, 0.8, 1),
        separator_color=(0.3, 0.3, 0.3, 1),
        title_size=24,
        title_align='center'
    )

    main_layout = FloatLayout()

    # Получаем начальное значение налога из объекта faction
    current_tax_rate = (
        int(faction.current_tax_rate.strip('%'))  # Если это строка с '%'
        if isinstance(faction.current_tax_rate, str) else
        int(faction.current_tax_rate)  # Если это число
    ) if hasattr(faction, 'current_tax_rate') else 0

    # Анимированная метка с динамической цветовой индикацией
    tax_label = Label(
        text=f"Налог: {current_tax_rate}%",
        color=(0.7, 0.9, 0.7, 1),
        font_size=28,
        bold=True,
        pos_hint={'center_x': 0.5, 'top': 0.9},
        size_hint=(0.8, None),
        halign="center"
    )

    # Кастомный ползунок с градиентной дорожкой
    tax_slider = Slider(
        min=0,
        max=100,
        value=current_tax_rate,  # Устанавливаем значение из faction
        step=1,
        orientation='horizontal',
        pos_hint={'center_x': 0.5, 'center_y': 0.6},
        size_hint=(0.9, 0.15),
        background_width=8,  # Ширина фона ползунка
        cursor_size=(30, 30),  # Размер курсора
        value_track=False,  # Отключаем дорожку под ползунком
    )

    # Кнопка с эффектом "матового стекла" и анимацией
    set_tax_button = Button(
        text="Применить",
        pos_hint={'center_x': 0.5, 'y': 0.1},
        size_hint=(0.6, 0.15),
        background_color=(0, 0, 0, 0),  # Прозрачный фон
        color=(0.8, 0.8, 0.8, 1),
        font_size=20
    )

    with set_tax_button.canvas.before:
        Color(0.3, 0.3, 0.3, 0.5)  # Цвет фона
        set_tax_button.rect = RoundedRectangle(
            size=set_tax_button.size,
            pos=set_tax_button.pos,
            radius=[15]  # Скругленные углы
        )

    def update_rect(instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    set_tax_button.bind(pos=update_rect, size=update_rect)

    # Обновляем метку с анимацией цвета
    def update_tax_label(instance, value):
        tax_label.text = f"Налог: {int(value)}%"
        r = value / 100
        g = 1 - r
        tax_label.color = (r, g, 0, 1)
        Animation(font_size=32, duration=0.1).start(tax_label)
        Animation(font_size=28, duration=0.2).start(tax_label)

    tax_slider.bind(value=update_tax_label)

    # Функция для установки налога
    def set_tax(instance):
        """Установить новый уровень налогов и закрыть попап"""
        tax_rate = int(tax_slider.value)  # Получаем текущее значение ползунка
        faction.current_tax_rate = f"{tax_rate}%"  # Сохраняем значение в faction
        faction.set_taxes(tax_rate)  # Обновляем налоги в объекте faction
        faction.apply_tax_effect(tax_rate)  # Применяем эффекты от налогов
        tax_popup.dismiss()  # Закрываем попап

    set_tax_button.bind(on_press=set_tax)

    # Добавляем элементы в layout
    main_layout.add_widget(tax_label)
    main_layout.add_widget(tax_slider)
    main_layout.add_widget(set_tax_button)

    # Устанавливаем содержимое попапа
    tax_popup.content = main_layout
    tax_popup.open()


def start_economy_mode(faction, game_area):
    """Инициализация экономического режима для выбранной фракции"""

    # Создаем layout для кнопок
    economy_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, 0.1),
        pos_hint={'x': 0, 'y': 0},
        spacing=10,  # Расстояние между кнопками
        padding=10  # Отступы внутри layout
    )

    # Функция для создания стильных кнопок
    def create_styled_button(text, on_press_callback):
        button = Button(
            text=text,
            size_hint_x=0.33,
            size_hint_y=None,
            height=50,
            background_color=(0, 0, 0, 0),  # Прозрачный фон
            color=(1, 1, 1, 1),  # Цвет текста (белый)
            font_size=16,  # Размер шрифта
            bold=True  # Жирный текст
        )

        # Добавляем кастомный фон с помощью Canvas
        with button.canvas.before:
            Color(0.2, 0.8, 0.2, 1)  # Цвет фона кнопки (зеленый)
            button.rect = Rectangle(pos=button.pos, size=button.size)

        # Обновляем позицию и размер прямоугольника при изменении размера кнопки
        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        button.bind(pos=update_rect, size=update_rect)

        # Привязываем функцию к событию нажатия
        button.bind(on_press=on_press_callback)
        return button

    # Создаем кнопки с новым стилем
    build_btn = create_styled_button("Состояние государства", lambda x: open_build_popup(faction))
    trade_btn = create_styled_button("Торговля", lambda x: open_trade_popup(faction))
    tax_btn = create_styled_button("Управление налогами", lambda x: open_tax_popup(faction))

    # Добавляем кнопки в layout
    economy_layout.add_widget(build_btn)
    economy_layout.add_widget(trade_btn)
    economy_layout.add_widget(tax_btn)

    # Добавляем layout с кнопками в нижнюю часть экрана
    game_area.add_widget(economy_layout)