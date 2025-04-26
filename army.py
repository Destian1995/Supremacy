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


from economic import format_number
import threading
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

        # Проверка наличия ресурсов
        if not self.deduct_resources(required_crowns, required_workers):
            self.show_message(
                title="Ошибка найма",
                message=f"Нанять юнитов невозможно: недостаточно ресурсов.\n"
                        f"Необходимые: {format_number(required_crowns)} крон и {format_number(required_workers)} рабочих."
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
            message=f"{unit_name} нанят! \n"
                    f"Потрачено: {format_number(required_crowns)} крон и {format_number(required_workers)} рабочих."
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


        # Проверка наличия ресурсов
        if not self.deduct_resources(required_crowns, required_workers):
            self.show_message(
                title="Ошибка найма",
                message=f"Нанять юнитов невозможно: недостаточно ресурсов.\n"
                        f"Необходимые: {format_number(required_crowns)} крон и {format_number(required_workers)} рабочих."
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
        SELECT unit_name, consumption, cost_money, cost_time, image_path, attack, defense, durability, unit_class
        FROM units WHERE faction = ?
    """, (faction,))
    rows = cursor.fetchall()
    conn.close()

    unit_data = {}
    for row in rows:
        unit_name, consumption, cost_money, cost_time, image_path, attack, defense, durability, unit_class = row
        unit_data[unit_name] = {
            "cost": [cost_money, cost_time],
            "image": image_path,
            "stats": {
                "Урон": attack,
                "Защита": defense,
                "Живучесть": durability,
                "Класс юнита": unit_class,
                "Потребление сырья": consumption
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

    # Добавляем кнопки в layout
    army_layout.add_widget(train_btn)

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