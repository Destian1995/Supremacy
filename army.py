# army.py
from kivy.animation import Animation
from kivy.graphics import Rectangle
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle
from strike import strike_to_city

import threading
import strike
import json
import time
import sqlite3


class ArmyCash:
    def __init__(self, faction, class_faction):
        """
        Инициализация класса ArmyCash.
        :param faction: Название фракции.
        :param class_faction: Экземпляр класса Faction (экономический модуль).
        """
        self.faction = faction
        self.class_faction = class_faction  # Экономический модуль
        self.db_path = "game_data.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.resources = self.load_resources()  # Загрузка начальных ресурсов

    def load_resources(self):
        """
        Загружает текущие ресурсы фракции из базы данных.
        """
        try:
            rows = self.load_data("resources", ["resource_type", "amount"], "faction = ?", (self.faction,))
            resources = {"Кроны": 0, "Рабочие": 0}
            for resource_type, amount in rows:
                if resource_type in resources:
                    resources[resource_type] = amount

            # Отладочный вывод: загруженные ресурсы
            print(f"[DEBUG] Загружены ресурсы для фракции '{self.faction}': {resources}")
            return resources
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке ресурсов: {e}")
            return {"Кроны": 0, "Рабочие": 0}

    def load_data(self, table, columns, condition=None, params=None):
        """
        Универсальный метод для загрузки данных из таблицы базы данных.
        """
        try:
            query = f"SELECT {', '.join(columns)} FROM {table}"
            if condition:
                query += f" WHERE {condition}"
            self.cursor.execute(query, params or ())
            result = self.cursor.fetchall()

            # Отладочный вывод: SQL-запрос и результат
            print(f"[DEBUG] SQL-запрос: {query}, параметры: {params}")
            print(f"[DEBUG] Результат запроса: {result}")

            return result
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных из таблицы {table}: {e}")
            return []

    def deduct_resources(self, crowns, workers):
        """
        Списывает ресурсы через экономический модуль.

        :param crowns: Количество крон для списания.
        :param workers: Количество рабочих для списания.
        :return: True, если ресурсы успешно списаны; False, если недостаточно ресурсов.
        """
        try:
            # Проверяем доступность ресурсов через экономический модуль
            current_crowns = self.class_faction.get_resource_now("Кроны")
            current_workers = self.class_faction.get_resource_now("Рабочие")

            print(f"[DEBUG] Текущие ресурсы: Кроны={current_crowns}, Рабочие={current_workers}")

            if current_crowns < crowns or current_workers < workers:
                print("[DEBUG] Недостаточно ресурсов для списания.")
                return False

            # Списываем ресурсы через экономический модуль
            self.class_faction.update_resource_now("Кроны", current_crowns - crowns)
            self.class_faction.update_resource_now("Рабочие", current_workers - workers)

            return True

        except Exception as e:
            print(f"Ошибка при списании ресурсов: {e}")
            return False

    def hire_unit(self, unit_name, unit_cost, quantity, unit_stats, unit_image):
        """
        Нанимает юнит (оружие), если ресурсов достаточно.
        :param unit_name: Название юнита.
        :param unit_cost: Стоимость юнита в виде кортежа (кроны, рабочие).
        :param quantity: Количество нанимаемых юнитов.
        :param unit_stats: Характеристики юнита (должен быть словарем).
        :return: True, если найм успешен; False, если недостаточно ресурсов.
        """
        crowns, workers = unit_cost
        required_crowns = int(crowns) * int(quantity)
        required_workers = int(workers) * int(quantity)

        # Отладочный вывод: стоимость найма
        print(f"[DEBUG] Попытка нанять {quantity} юнитов '{unit_name}'. "
              f"Требуемые ресурсы: Кроны={required_crowns}, Рабочие={required_workers}")

        # Проверка наличия ресурсов
        if not self.deduct_resources(required_crowns, required_workers):
            self.show_message(
                title="Ошибка найма",
                message=f"Нанять юнитов невозможно: недостаточно ресурсов.\n"
                        f"Необходимые: {required_crowns} крон и {required_workers} рабочих."
            )
            return False

        # Проверка типа unit_stats
        if not isinstance(unit_stats, dict):
            print("[ERROR] unit_stats должен быть словарем!")
            return False

        # Добавление юнитов в базу данных
        self.add_or_update_army_unit(unit_name, quantity, unit_stats, unit_image)

        # Отображение сообщения об успехе
        self.show_message(
            title="Успех",
            message=f"Юнит {unit_name} нанят! "
                    f"Потрачено: {required_crowns} крон и {required_workers} рабочих."
        )
        return True

    def add_or_update_army_unit(self, unit_name, quantity, unit_stats, unit_image):
        """
        Добавляет или обновляет данные о юните в базе данных.
        """
        self.cursor.execute("""
            SELECT quantity, total_attack, total_defense, total_durability, unit_image
            FROM armies
            WHERE faction = ? AND unit_type = ?
        """, (self.faction, unit_name))
        result = self.cursor.fetchone()

        if result:
            # Если юнит уже существует, обновляем его данные
            current_quantity, total_attack, total_defense, total_durability, _ = result
            new_quantity = current_quantity + quantity
            self.cursor.execute("""
                UPDATE armies
                SET quantity = ?, total_attack = ?, total_defense = ?, total_durability = ?, unit_image = ?
                WHERE faction = ? AND unit_type = ?
            """, (
                new_quantity,
                total_attack + unit_stats["Урон"] * quantity,
                total_defense + unit_stats["Защита"] * quantity,
                total_durability + unit_stats["Живучесть"] * quantity,
                unit_image,  # Обновляем изображение
                self.faction,
                unit_name
            ))
        else:
            # Если юнит новый, добавляем его в базу
            self.cursor.execute("""
                INSERT INTO armies (faction, unit_type, quantity, total_attack, total_defense, total_durability, unit_class, unit_image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.faction,
                unit_name,
                quantity,
                unit_stats["Урон"] * quantity,
                unit_stats["Защита"] * quantity,
                unit_stats["Живучесть"] * quantity,
                unit_stats["Класс юнита"],
                unit_image  # Добавляем изображение
            ))

        self.conn.commit()

    def hire_weapons(self, weapon_name, unit_cost, quantity):
        """
        Обновляет или создает запись в таблице weapons.
        :param unit_cost: кортеж, содержащий стоимость оружия в кронах и рабочих.
        """
        crowns, workers = unit_cost
        required_crowns = int(crowns) * int(quantity)
        required_workers = int(workers) * int(quantity)

        # Отладочный вывод: стоимость найма
        print(f"[DEBUG] Попытка нанять {quantity} юнитов '{weapon_name}'. "
              f"Требуемые ресурсы: Кроны={required_crowns}, Рабочие={required_workers}")

        # Проверка наличия ресурсов
        if not self.deduct_resources(required_crowns, required_workers):
            self.show_message(
                title="Ошибка найма",
                message=f"Нанять юнитов невозможно: недостаточно ресурсов.\n"
                        f"Необходимые: {required_crowns} крон и {required_workers} рабочих."
            )
            return False
        return True

    def update_weapon_in_db(self, faction, weapon_name, quantity, damage, koef):
        """
        Обновляет или создает запись в таблице weapons.
        :param faction: Название фракции.
        :param weapon_name: Название оружия.
        :param quantity: Количество единиц оружия.
        :param damage: Урон оружия.
        :param koef: Коэффициент преодоления ПВО.
        """
        try:
            # Проверяем, существует ли запись для данного оружия
            self.cursor.execute('''
                SELECT quantity
                FROM weapons
                WHERE faction = ? AND weapon_name = ?
            ''', (faction, weapon_name))
            result = self.cursor.fetchone()

            if result:
                # Если запись существует, обновляем количество
                current_quantity = result[0]
                new_quantity = current_quantity + quantity
                self.cursor.execute('''
                    UPDATE weapons
                    SET quantity = ?, damage = ?, koef = ?
                    WHERE faction = ? AND weapon_name = ?
                ''', (new_quantity, damage, koef, faction, weapon_name))
            else:
                # Если запись отсутствует, создаем новую
                self.cursor.execute('''
                    INSERT INTO weapons (faction, weapon_name, quantity, damage, koef)
                    VALUES (?, ?, ?, ?, ?)
                ''', (faction, weapon_name, quantity, damage, koef))

            self.conn.commit()
            print(f"[DEBUG] Данные оружия '{weapon_name}' успешно обновлены в таблице weapons.")

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении таблицы weapons: {e}")

    def show_message(self, title, message):
        """
        Отображает всплывающее сообщение поверх всех окон.
        :param title: Заголовок сообщения.
        :param message: Текст сообщения.
        """
        # Создаем контент для всплывающего окна
        content_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        message_label = Label(
            text=message,
            color=(1, 1, 1, 1),  # Белый текст
            font_size=16,
            size_hint_y=None,
            height=100
        )
        close_button = Button(
            text="Закрыть",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)  # Синий фон кнопки
        )

        # Добавляем виджеты в контент
        content_layout.add_widget(message_label)
        content_layout.add_widget(close_button)

        # Создаем Popup
        popup = Popup(
            title=title,
            content=content_layout,
            size_hint=(0.6, 0.4),  # Размер окна (60% ширины, 40% высоты)
            auto_dismiss=False  # Окно не закрывается автоматически при клике вне его
        )

        # Привязываем кнопку "Закрыть" к закрытию Popup
        close_button.bind(on_release=popup.dismiss)

        # Открываем Popup
        popup.open()


def load_unit_data(faction):
    """Загружает данные о юнитах для выбранной фракции из базы данных."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT unit_name, cost_money, cost_time, image_path, attack, defense, durability, unit_class
        FROM units WHERE faction = ?
    """, (faction,))
    rows = cursor.fetchall()
    conn.close()

    unit_data = {}
    for row in rows:
        unit_name, cost_money, cost_time, image_path, attack, defense, durability, unit_class = row
        unit_data[unit_name] = {
            "cost": [cost_money, cost_time],
            "image": image_path,
            "stats": {
                "Урон": attack,
                "Защита": defense,
                "Живучесть": durability,
                "Класс юнита": unit_class
            }
        }
    return unit_data


def show_unit_selection(faction, army_hire, class_faction):
    """Показать окно выбора юнитов для найма."""
    unit_data = load_unit_data(faction)

    unit_popup = Popup(title="Выбор юнитов", size_hint=(0.9, 0.9), background_color=(0.1, 0.1, 0.1, 1))

    scroll_view = ScrollView(size_hint=(0.6, 1))

    unit_layout = GridLayout(cols=2, padding=15, spacing=15, size_hint_y=None)
    unit_layout.bind(minimum_height=unit_layout.setter('height'))

    stats_box = TextInput(readonly=True, size_hint=(0.3, 1), padding=(20, 10, 20, 10),
                          background_color=(0.2, 0.2, 0.2, 1), foreground_color=(1, 1, 1, 1), font_size=16)

    for unit_name, unit_info in unit_data.items():
        unit_box = BoxLayout(orientation='vertical', size_hint=(None, None), size=(200, 200))

        # Изображение юнита
        unit_image = Image(source=unit_info["image"], size_hint=(1, 0.6), allow_stretch=True, keep_ratio=True)
        unit_box.add_widget(unit_image)

        # Стоимость юнита
        cost_label = Label(text=f"Кроны: {unit_info['cost'][0]} \nРабочие: {unit_info['cost'][1]}",
                           size_hint=(1, 0.2), color=(1, 1, 1, 1), font_size=14)
        unit_box.add_widget(cost_label)

        # Кнопки управления
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)

        # Поле для ввода количества юнитов
        quantity_input = TextInput(hint_text="Количество", size_hint_x=0.5, font_size=16,
                                   multiline=False, background_color=(0.3, 0.3, 0.3, 1), foreground_color=(1, 1, 1, 1))

        # Кнопка для найма юнита
        hire_btn = Button(text="Нанять", size_hint_x=0.5, background_color=(0.4, 0.8, 0.4, 1),
                          font_size=16, color=(1, 1, 1, 1))
        hire_btn.bind(on_release=lambda instance, name=unit_name, cost=unit_info['cost'],
                                        input_box=quantity_input, stats=unit_info['stats'], image=unit_info["image"]:
        broadcast_units(name, cost, input_box, army_hire, image, stats))

        button_layout.add_widget(hire_btn)
        button_layout.add_widget(quantity_input)

        # Кнопка для отображения информации о юните
        info_btn = Button(text="Инфо", size_hint_x=0.5, background_color=(0.4, 0.6, 0.8, 1),
                          font_size=16, color=(1, 1, 1, 1))
        info_btn.bind(on_release=lambda x, name=unit_name, info=unit_info['stats']:
        display_unit_stats_info(name, info, stats_box))
        button_layout.add_widget(info_btn)

        unit_box.add_widget(button_layout)
        unit_layout.add_widget(unit_box)

    scroll_view.add_widget(unit_layout)

    # Организуем содержимое попапа
    popup_content = BoxLayout(orientation='horizontal', padding=(10, 10, 10, 10), spacing=15)
    popup_content.add_widget(scroll_view)
    popup_content.add_widget(stats_box)

    unit_popup.content = popup_content
    unit_popup.open()


def broadcast_units(unit_name, unit_cost, quantity_input, army_hire, image, unit_stats):
    """Обрабатывает найм юнитов и проверяет количество."""
    quantity_text = quantity_input.text  # Получаем текст из поля ввода
    print(f"Полученный unit_stats: {unit_stats}")
    try:
        # Проверяем, не пустое ли поле
        if not quantity_text:
            print("Введите количество юнитов.")
            return

        quantity = int(quantity_text)

        if quantity <= 0:
            print("Количество должно быть больше нуля.")
            return

        # Корректный порядок аргументов: unit_stats перед image
        if army_hire.hire_unit(unit_name, unit_cost, quantity, unit_stats, image):
            print(f"{quantity} юнитов {unit_name} наняты! Ссылка на изображение: {image}")
        else:
            print(f"Не удалось нанять {quantity} юнитов {unit_name} из-за недостатка ресурсов.")

    except ValueError:
        print("Введите корректное количество.")


def display_unit_stats_info(unit_name, stats, stats_box):
    """Отображает характеристики юнита в текстовом боксе при нажатии кнопки 'Инфо'"""
    stats_text = f"{unit_name}:\n\n"
    for key, value in stats.items():
        stats_text += f"{key}: {value}\n"
    stats_box.text = stats_text  # Устанавливаем текст характеристик юнита




#--------------------------------

# Функция для загрузки данных юнитов (оружия) из БД
def load_weapon_data(faction):
    """Загружает данные об оружии для указанной фракции из таблицы weapons_stats."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT weapon_name, cost_money, cost_time, image_path, damage, koef
        FROM weapons_stats
        WHERE faction = ?
    """, (faction,))
    rows = cursor.fetchall()
    conn.close()

    weapon_data = {}
    for row in rows:
        weapon_name, cost_money, cost_time, image_path, damage, koef = row
        weapon_data[weapon_name] = {
            "cost": [cost_money, cost_time],
            "image": image_path,
            "stats": {
                "Вероятный Урон": damage,
                "Коэфициент преодоления ПВО": koef
            }
        }
    return weapon_data


# Функция для загрузки и очистки данных из файла
def load_and_clear_coordinates_data(faction):
    """Загружает и очищает данные о координатах из таблицы coordinates_weapons."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    # Загружаем данные
    cursor.execute('''
        SELECT city_name, coordinates, path_to_army
        FROM coordinates_weapons
        WHERE faction = ?
    ''', (faction,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {}

    city_name, coordinates, path_to_army = row

    # Очищаем данные
    cursor.execute('''
        DELETE FROM coordinates_weapons
        WHERE faction = ?
    ''', (faction,))
    conn.commit()
    conn.close()

    return {
        "city_name": city_name,
        "coordinates": coordinates,
        "path_to_army": path_to_army
    }


def check_and_open_weapon_management(faction, army_cash):
    def thread_function():
        while True:  # Бесконечный цикл
            coordinates_data = load_and_clear_coordinates_data(faction)
            if coordinates_data:
                city_name_text = coordinates_data.get('city_name', '')
                coordinates_text = coordinates_data.get('coordinates', '')
                path_to_army = coordinates_data.get('path_to_army', '')

                # Запланировать выполнение функции в основном потоке
                Clock.schedule_once(
                    lambda dt: open_weapon_db_management(faction, army_cash, city_name_text, coordinates_text,
                                                         path_to_army))

            else:
                print("")
            time.sleep(2)  # Проверка каждые 2 секунды

    # Запуск потока
    threading.Thread(target=thread_function, daemon=True).start()


current_weapon_management_popup = None
weapon_labels = {}  # Для хранения меток с количеством юнитов
current_weapon_selection_popup = None  # Окно выбора оружия


# Функция для открытия окна управления оружием
def animate_button(button):
    animation = Animation(background_color=(0.2, 0.9, 0.2, 1), duration=0.3)
    animation += Animation(background_color=(0.2, 0.6, 0.2, 1), duration=0.3)
    animation.start(button)


def open_weapon_db_management(faction, army_cash, city_name_text='', coordinates_text='', path_to_army=''):
    if isinstance(coordinates_text, list):
        coordinates_text = ', '.join(map(str, coordinates_text))
    global current_weapon_management_popup

    # Основной макет
    layout = FloatLayout()

    # Загрузка фонового изображения фракции
    faction_image_path = load_faction_image(faction)
    if not faction_image_path:
        print(f"Изображение для фракции {faction} не найдено. Используется запасное изображение.")
        faction_image_path = "files/default_image.jpg"

    with layout.canvas.before:
        Color(1, 1, 1, 1)  # Цвет фона
        Rectangle(source=faction_image_path, pos=layout.pos, size=layout.size)
    layout.bind(pos=lambda *args: setattr(layout.canvas.before.children[-1], 'pos', layout.pos))
    layout.bind(size=lambda *args: setattr(layout.canvas.before.children[-1], 'size', layout.size))

    # Загрузка данных об оружии из базы данных
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT weapon_name, quantity
        FROM weapons
        WHERE faction = ?
    ''', (faction,))
    rows = cursor.fetchall()
    conn.close()

    # Создаем словарь с данными об оружии
    weapon_data = {}
    for row in rows:
        weapon_name, quantity = row
        weapon_data[weapon_name] = {"count": quantity}

    # Левая панель - выбор оружия
    weapon_selection_layout = BoxLayout(orientation='vertical', size_hint=(0.4, 0.6), padding=10, spacing=5)

    # Создаем кнопки для каждого типа оружия
    weapons = load_weapon_data(faction)
    for weapon_name, weapon_info in weapons.items():
        available_quantity = weapon_data.get(weapon_name, {}).get("count", 0)
        button_text = f"{weapon_name} ({available_quantity} шт.)"

        weapon_button = Button(
            text=button_text,
            size_hint=(1, None),
            height=50,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_size=16
        )
        with weapon_button.canvas.before:
            Color(0.3, 0.6, 0.3, 1)
            RoundedRectangle(pos=weapon_button.pos, size=weapon_button.size, radius=[10])

        def update_rect(instance, value, btn_rect=weapon_button.canvas.before.children[-1]):
            btn_rect.pos = instance.pos
            btn_rect.size = instance.size

        weapon_button.bind(pos=update_rect, size=update_rect)

        # Обновляем количество выбранного оружия при нажатии на кнопку
        def on_weapon_select(instance, name=weapon_name):
            select_weapon(name, weapons, faction, army_cash)
            global weapon_name_start_mission
            weapon_name_start_mission = name
            weapon_quantity_input.text = str(available_quantity)  # Передаем количество в поле ввода
            print(f"Выбранное оружие: {name}, Количество: {available_quantity}")  # Отладочное сообщение

            # Обновляем атрибуты кнопки "Запуск"
            mission_button.selected_weapon = name
            mission_button.selected_quantity = available_quantity

        weapon_button.bind(on_release=on_weapon_select)
        weapon_button.bind(on_press=lambda x: animate_button(x))

        # Отключаем кнопку, если это боевой режим (army_cash is None)
        if army_cash is None:
            weapon_button.disabled = True
            weapon_button.background_color = (0.5, 0.5, 0.5, 1)  # Серый цвет для отключенных кнопок
            weapon_button.color = (0.8, 0.8, 0.8, 1)  # Светло-серый текст

        weapon_selection_layout.add_widget(weapon_button)

    # Правая панель - данные миссии и управление
    mission_data_layout = BoxLayout(orientation='vertical', size_hint=(0.6, 0.6), padding=10, spacing=10)

    # Поле для названия города
    city_name_input = TextInput(
        text=str(city_name_text),
        multiline=False,
        readonly=True,
        size_hint_y=None,
        height=40,
        background_normal='',  # Прозрачный фон
        background_color=(0.9, 0.9, 0.9, 1),  # Серый фон
        foreground_color=(0, 0, 0, 1),  # Черный текст
        font_size=16
    )

    # Поле для режима работы
    mode_input = TextInput(
        text="Боевой режим" if army_cash is None else "Обычный режим",
        multiline=False,
        readonly=True,
        size_hint_y=None,
        height=40,
        background_normal='',  # Прозрачный фон
        background_color=(0.9, 0.9, 0.9, 1),  # Серый фон
        foreground_color=(1, 0, 0, 1) if army_cash is None else (0, 0.5, 0, 1),  # Красный или темно-зеленый текст
        font_size=16
    )

    # Поле для количества оружия
    weapon_quantity_input = TextInput(
        hint_text="Количество",
        text="0",
        multiline=False,
        readonly=True,
        size_hint_y=None,
        height=40,
        background_normal='',  # Прозрачный фон
        background_color=(0.9, 0.9, 0.9, 1),  # Серый фон
        foreground_color=(0, 0, 0, 1),  # Черный текст
        font_size=16
    )

    # Кнопка выбора оружия
    select_weapon_button = Button(
        text="Выбрать оружие",
        size_hint_y=None,
        height=60,
        background_normal='',
        background_color=(0, 0, 0, 0),
        color=(1, 1, 1, 1),
        font_size=16
    )
    with select_weapon_button.canvas.before:
        Color(0.3, 0.4, 0.9, 1)
        RoundedRectangle(pos=select_weapon_button.pos, size=select_weapon_button.size, radius=[10])
    select_weapon_button.bind(pos=lambda *args: setattr(select_weapon_button.canvas.before.children[-1], 'pos', select_weapon_button.pos))
    select_weapon_button.bind(size=lambda *args: setattr(select_weapon_button.canvas.before.children[-1], 'size', select_weapon_button.size))

    # Функция для проверки выбора города
    def check_city_selection(instance):
        if not city_name_input.text.strip():  # Проверяем, пустое ли поле
            # Всплывающее сообщение
            popup_content = Label(text="Сначала выберите город в качестве цели!")
            popup = Popup(
                title="Ошибка",
                content=popup_content,
                size_hint=(0.6, 0.3)
            )
            popup.open()
        else:
            # Если город выбран, открываем окно выбора оружия
            open_weapon_selection_popup(
                select_weapon_button,
                faction,
                weapon_quantity_input  # Передаем поле для количества
            )

    # Привязываем функцию к кнопке
    select_weapon_button.bind(on_release=check_city_selection)
    select_weapon_button.bind(on_press=lambda x: animate_button(x))

    # Кнопка запуска миссии
    mission_button = Button(
        text="Запуск",
        size_hint_y=None,
        height=50,
        background_normal='',
        background_color=(0, 0, 0, 0),
        color=(1, 1, 1, 1),
        font_size=16
    )
    with mission_button.canvas.before:
        Color(0.8, 0.2, 0.2, 1)
        RoundedRectangle(pos=mission_button.pos, size=mission_button.size, radius=[10])
    mission_button.bind(pos=lambda *args: setattr(mission_button.canvas.before.children[-1], 'pos', mission_button.pos))
    mission_button.bind(size=lambda *args: setattr(mission_button.canvas.before.children[-1], 'size', mission_button.size))


    # Вызов start_mission с передачей имени оружия и количества
    mission_button.bind(on_release=lambda x: start_mission(
        faction,
        city_name_input.text,
        weapon_name_start_mission,  # Передаем имя оружия
        weapon_quantity_input.text, # Передаем количество
    ))
    mission_button.bind(on_press=lambda x: animate_button(x))

    # Добавляем виджеты в правую панель
    mission_data_layout.add_widget(city_name_input)
    mission_data_layout.add_widget(mode_input)
    mission_data_layout.add_widget(weapon_quantity_input)
    mission_data_layout.add_widget(select_weapon_button)
    mission_data_layout.add_widget(mission_button)

    # Размещаем панели на основном макете
    weapon_selection_layout.pos_hint = {'x': 0, 'y': 0.1}
    mission_data_layout.pos_hint = {'x': 0.4, 'y': 0.1}
    layout.add_widget(weapon_selection_layout)
    layout.add_widget(mission_data_layout)

    # Всплывающее окно
    if current_weapon_management_popup:
        current_weapon_management_popup.dismiss()

    current_weapon_management_popup = Popup(
        title="Управление дальнобойным оружием",
        content=layout,
        size_hint=(0.8, 0.8),
        background_color=(0.2, 0.2, 0.2, 1)
    )
    current_weapon_management_popup.open()


def open_weapon_selection_popup(selected_weapon_label, faction, weapon_quantity_input):
    """Открывает всплывающее окно для выбора оружия."""
    global current_weapon_selection_popup

    # Основной макет окна
    popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

    # Загрузка данных об оружии из базы данных
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT weapon_name, quantity, damage
        FROM weapons
        WHERE faction = ?
    ''', (faction,))
    rows = cursor.fetchall()
    conn.close()

    # Создаем таблицу для отображения данных
    table_layout = GridLayout(cols=3, size_hint_y=None, spacing=5, padding=5)
    table_layout.bind(minimum_height=table_layout.setter('height'))

    # Заголовки таблицы
    headers = ["Тип оружия", "Количество", "Общая мощность"]
    for header in headers:
        header_label = Label(
            text=header,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=40,
            font_size=16,
            bold=True
        )
        table_layout.add_widget(header_label)

    # Добавляем данные в таблицу
    selected_weapon = {}  # Словарь для хранения выбранного оружия
    for row in rows:
        weapon_name, quantity, damage = row
        total_power = quantity * damage

        # Ячейка с типом оружия (кликабельная метка)
        weapon_label = Button(
            text=weapon_name,
            color=(0.8, 0.8, 0.8, 1),
            background_color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            height=40,
            background_normal='',
            on_release=lambda btn, name=weapon_name: select_weapon_from_table(
                name,
                selected_weapon,
                quantity_input,
                table_layout  # Передаем таблицу для поиска кнопки
            )
        )

        # Ячейка с количеством
        quantity_label = Label(
            text=str(quantity),
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None,
            height=40
        )

        # Ячейка с общей мощностью
        power_label = Label(
            text=str(total_power),
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None,
            height=40
        )

        # Добавляем виджеты в таблицу
        table_layout.add_widget(weapon_label)
        table_layout.add_widget(quantity_label)
        table_layout.add_widget(power_label)

        # Сохраняем данные оружия для последующего выбора
        selected_weapon[weapon_name] = {"quantity": quantity, "total_power": total_power}

    # Прокручиваемый контейнер для таблицы
    scroll_view = ScrollView(size_hint=(1, 0.8), do_scroll_x=False)
    scroll_view.add_widget(table_layout)

    # Контейнер для кнопок
    button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)

    # Поле для выбора количества оружия (TextInput)
    quantity_input = TextInput(
        hint_text="Количество",
        multiline=False,
        size_hint_x=0.4,
        height=40,
        background_color=(0.9, 0.9, 0.9, 1),
        foreground_color=(0, 0, 0, 1),
        disabled=False,
        background_normal='',
        background_active='',
        border=(10, 10, 10, 10)  # Закругление по всем углам
    )
    quantity_input.bind(on_touch_down=lambda instance, touch:
    setattr(quantity_input, 'focus', True) if quantity_input.collide_point(*touch.pos) else None)

    # Кнопка подтверждения выбора
    confirm_button = Button(
        text="Подтвердить",
        size_hint_x=0.3,
        height=40,
        background_color=(0.2, 0.8, 0.2, 1),
        color=(1, 1, 1, 1)
    )
    confirm_button.bind(on_release=lambda x: (
        confirm_weapon_selection(selected_weapon, quantity_input.text, weapon_quantity_input),
        current_weapon_selection_popup.dismiss()  # Закрываем окно после подтверждения
    ))

    # Кнопка закрытия окна
    done_button = Button(
        text="Готово",
        size_hint_x=0.3,
        height=40,
        background_color=(0.8, 0.2, 0.2, 1),
        color=(1, 1, 1, 1)
    )
    done_button.bind(on_release=lambda x: current_weapon_selection_popup.dismiss())

    # Добавляем виджеты в контейнер кнопок
    button_layout.add_widget(quantity_input)
    button_layout.add_widget(confirm_button)
    button_layout.add_widget(done_button)

    # Добавляем таблицу и кнопки в основной макет
    popup_layout.add_widget(scroll_view)
    popup_layout.add_widget(button_layout)

    # Создаем объект Popup
    current_weapon_selection_popup = Popup(
        title="Выбор оружия",
        content=popup_layout,
        size_hint=(0.8, 0.8),
        background_color=(0.2, 0.2, 0.2, 1)
    )
    current_weapon_selection_popup.open()

def select_weapon_from_table(weapon_name, selected_weapon, quantity_input, table_layout):
    # Сброс предыдущего выделения
    for widget in table_layout.children:
        if isinstance(widget, Button) and widget.text != "Тип оружия":
            widget.background_color = (0.2, 0.2, 0.2, 1)

    # Установка нового выделения
    for widget in table_layout.children:
        if isinstance(widget, Button) and widget.text == weapon_name:
            widget.background_color = (0.2, 0.6, 0.2, 1)
            break

    # Обновление состояния
    for w in selected_weapon.values():
        w['selected'] = False
    selected_weapon[weapon_name]['selected'] = True

    # Обновление поля ввода
    quantity_input.hint_text = f"Доступно: {selected_weapon[weapon_name]['quantity']}"
    quantity_input.text = ""
    quantity_input.disabled = False


def confirm_weapon_selection(selected_weapon, quantity_text, weapon_quantity_input):
    try:
        # Проверка выбора оружия
        selected = [k for k, v in selected_weapon.items() if v.get('selected')]
        if not selected:
            raise ValueError("Сначала выберите оружие")

        # Проверка ввода количества
        if not quantity_text.strip():
            raise ValueError("Введите количество")
        quantity = int(quantity_text)
        if quantity <= 0:
            raise ValueError("Количество должно быть > 0")

        # Проверка доступности
        weapon_name = selected[0]
        available = selected_weapon[weapon_name]['quantity']
        if quantity > available:
            raise ValueError(f"Доступно только {available}")

        # Обновление интерфейса
        weapon_quantity_input.text = str(quantity)

    except ValueError as e:
        print(f"Ошибка: {e}")


def select_weapon_quantity(selected_weapon, quantity_text, weapon_quantity_input):
    """Обновляет поле количества оружия."""
    try:
        quantity = int(quantity_text)
        if quantity <= 0:
            raise ValueError("Количество должно быть больше 0.")

        # Проверяем, достаточно ли оружия в наличии
        weapon_name = list(selected_weapon.keys())[0]  # Предполагается выбор первого оружия
        available_quantity = selected_weapon[weapon_name]["quantity"]
        if quantity > available_quantity:
            raise ValueError(f"Недостаточно оружия. Доступно: {available_quantity}.")

        # Обновляем поле количества
        weapon_quantity_input.text = str(quantity)
    except ValueError as e:
        print(f"Ошибка: {e}")


def select_weapon_from_list(selected_weapon_label, weapon_name, type_field, count_field, available_count):
    """Обновляет поля с информацией об оружии."""
    selected_weapon_label.text = f"Выбрано: {weapon_name}"
    type_field.text = weapon_name
    count_field.text = str(available_count)

    if current_weapon_selection_popup:
        current_weapon_selection_popup.dismiss()



def load_faction_image(faction):
    """Загружает путь к изображению станции для указанной фракции из базы данных."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT image_path
        FROM station_images
        WHERE faction = ?
    ''', (faction,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        print(f"Изображение для фракции {faction} не найдено.")
        return None

    return result[0]

def select_weapon(weapon_name, weapons, faction, army_cash):
    weapon_info = weapons[weapon_name]
    stats_info = '\n'.join([f"{key}: {value}" for key, value in weapon_info.get('stats', {}).items()])

    weapon_details_layout = BoxLayout(orientation='horizontal', padding=20, spacing=15)

    # Изображение оружия
    weapon_image = Image(
        source=weapon_info.get('image', ''),
        size_hint=(0.6, 1),  # Увеличен размер изображения
        allow_stretch=True  # Позволяет растягивать изображение
    )
    weapon_details_layout.add_widget(weapon_image)

    # Информация об оружии
    info_layout = BoxLayout(orientation='vertical', size_hint=(0.4, 1), spacing=10)
    info_layout.add_widget(Label(
        text=f"[b]Характеристики:[/b]\n{stats_info}",
        markup=True,
        halign='left',
        color=(0.9, 0.9, 0.9, 1)
    ))
    info_layout.add_widget(Label(
        text=f"[b]Стоимость:[/b] \n {weapon_info.get('cost', [0, 0])[0]} Крон,  \n {weapon_info.get('cost', [0, 0])[1]} Рабочих",
        markup=True,
        color=(0.9, 0.9, 0.9, 1)
    ))

    # Поле ввода и кнопка
    quantity_label = Label(text="Количество юнитов:", halign='left', color=(0.8, 0.8, 0.8, 1))
    quantity_input = TextInput(
        multiline=False,
        size_hint=(1, None),
        height=40,
        background_color=(0.2, 0.2, 0.3, 1),  # Цвет фона поля ввода
        foreground_color=(1, 0, 0, 1)  # Красный цвет текста
    )
    build_button = StyledButton(text="Построить", size_hint=(1, None), height=50)

    # Получаем коэффициент преодоления ПВО
    koef = weapon_info.get('stats', {}).get('Коэфициент преодоления ПВО', 0)

    # Создаем всплывающее окно для деталей оружия
    weapon_details_popup = Popup(
        title=f"{weapon_name}",
        content=weapon_details_layout,
        size_hint=(0.8, 0.8),
        title_size=24
    )

    build_button.bind(
        on_release=lambda x: build_weapon(faction, weapon_name, quantity_input.text, weapon_info.get('cost', [0, 0]),
                                          weapon_details_popup, army_cash, koef))

    # Добавляем виджеты
    info_layout.add_widget(quantity_label)
    info_layout.add_widget(quantity_input)
    info_layout.add_widget(build_button)

    weapon_details_layout.add_widget(info_layout)
    weapon_details_popup.open()


# Обновление количества юнитов на основе данных JSON
def update_unit_quantity(weapon_name, new_quantity):
    if weapon_name in weapon_labels:
        weapon_labels[weapon_name].text = f"{weapon_name}: {new_quantity} шт."


def build_weapon(faction, weapon_name, quantity_str, cost, weapon_details_popup, army_cash, koef):
    try:
        quantity = int(quantity_str)
        total_cost = [cost[0] * quantity, cost[1] * quantity]

        # Получаем характеристики оружия из weapon_info
        weapon_info = load_weapon_data(faction).get(weapon_name, {})
        print(f"[DEBUG] Данные оружия '{weapon_name}': {weapon_info}")

        # Проверка наличия характеристик
        if not weapon_info or "stats" not in weapon_info:
            print(f"[ERROR] Некорректные данные для оружия '{weapon_name}'.")
            return

        # Формируем характеристики оружия
        damage = weapon_info.get("stats", {}).get("Вероятный Урон", 0)
        koef_value = weapon_info.get("stats", {}).get("Коэффициент преодоления ПВО", 0)

        # Передаем параметры в hire_weapons
        if army_cash.hire_weapons(weapon_name, cost, quantity):
            print(f"Построено {quantity} юнитов {weapon_name}. "
                  f"Общая стоимость: {total_cost[0]} Крон, {total_cost[1]} Рабочих.")

            # Обновляем таблицу weapons
            army_cash.update_weapon_in_db(faction, weapon_name, quantity, damage, koef_value)

            # Закрываем окно деталей оружия
            if weapon_details_popup:
                weapon_details_popup.dismiss()

            # Обновляем окно управления оружием
            open_weapon_db_management(faction, army_cash)
        else:
            print(f"Недостаточно ресурсов для найма {quantity} юнитов {weapon_name}.")
    except ValueError:
        print("Пожалуйста, введите корректное количество юнитов.")
        error_popup = Popup(
            title="Ошибка",
            content=Label(text="Пожалуйста, введите корректное количество юнитов."),
            size_hint=(0.5, 0.5)
        )
        error_popup.open()

def get_weapons(faction):
    """Получает данные об оружии для указанной фракции."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    cursor.execute('''
        SELECT weapon_name, cost_money, cost_time, image_path, damage, koef
        FROM weapons_stats
        WHERE faction = ?
    ''', (faction,))
    rows = cursor.fetchall()
    conn.close()

    weapon_data = {}
    for row in rows:
        weapon_name, cost_money, cost_time, image_path, damage, koef = row
        weapon_data[weapon_name] = {
            "cost": [cost_money, cost_time],
            "image": image_path,
            "stats": {
                "Вероятный Урон": damage,
                "Коэфициент преодоления ПВО": koef
            }
        }
    return weapon_data


def start_mission(faction, city_name, selected_weapon_name, quantity):
    selected_quantity = int(quantity)
    try:
        with sqlite3.connect("game_data.db") as db_connection:
            cursor = db_connection.cursor()
            print('[DEBUG] ', f'Фракция: {faction}, Город: {city_name}, Оружие: {selected_weapon_name}, Количество: {selected_quantity}')
            # Проверяем наличие оружия
            cursor.execute('''
                SELECT quantity, damage, koef
                FROM weapons
                WHERE faction = ? AND weapon_name = ?
            ''', (faction, selected_weapon_name))
            result = cursor.fetchone()

            if not result:
                print(f"Оружие {selected_weapon_name} не найдено.")
                return

            current_quantity, damage, koef = result
            # Обновляем количество оружия
            new_quantity = current_quantity - selected_quantity
            cursor.execute('''
                UPDATE weapons
                SET quantity = ?
                WHERE faction = ? AND weapon_name = ?
            ''', (new_quantity, faction, selected_weapon_name))
            db_connection.commit()

            # Передаем данные в модуль strike
            weapon_characteristics = {
                "name": selected_weapon_name,
                "count": selected_quantity,
                "damage": damage,
                "koef": koef
            }
            strike_to_city(city_name, weapon_characteristics, db_connection)

    except Exception as e:
        print(f"Ошибка при выполнении миссии start_mission: {e}")



#------Базовая функция------------

def start_army_mode(faction, game_area, class_faction):
    """
    Инициализация армейского режима для выбранной фракции.

    :param class_faction:
    :param faction: Объект фракции (экземпляр класса Faction).
    :param game_area: Центральная область игры, куда будут добавлены виджеты.
    """
    # Создаем объект ArmyCash для найма юнитов
    army_hire = ArmyCash(faction, class_faction)

    # Создаем layout для кнопок
    army_layout = BoxLayout(
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
            Color(1, 0.2, 0.2, 1)  # Цвет фона кнопки (красный)
            button.rect = Rectangle(pos=button.pos, size=button.size)

        # Обновляем позицию и размер прямоугольника при изменении размера кнопки
        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        button.bind(pos=update_rect, size=update_rect)

        # Привязываем функцию к событию нажатия
        button.bind(on_release=on_press_callback)
        return button

    # Создаем кнопки с новым стилем
    train_btn = create_styled_button("Тренировка войск", lambda x: show_unit_selection(faction, army_hire, class_faction))
    defend_btn = create_styled_button("Управление дб. оружием", lambda x: open_weapon_db_management(faction, army_hire))

    # Добавляем кнопки в layout
    army_layout.add_widget(train_btn)
    army_layout.add_widget(defend_btn)

    # Добавляем layout с кнопками в нижнюю часть экрана
    game_area.add_widget(army_layout)


#---------------------------------------------------------------
class StyledButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.2, 0.6, 0.8, 1)  # Основной цвет кнопки
            self.rect = RoundedRectangle(radius=[20], size=self.size, pos=self.pos)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        # Фиксируем радиус закругления
        self.rect.radius = [20]

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Сохраняем радиус при анимации
            self.rect.size = (self.size[0] - 5, self.size[1] - 5)
            self.rect.radius = [20]  # Форсируем обновление радиуса
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.rect.size = self.size
            self.rect.radius = [20]  # Форсируем обновление радиуса
        return super().on_touch_up(touch)