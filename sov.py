from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.core.window import Window
import os

import sqlite3
import random

import json

# Словарь для перевода названий
translation_dict = {
    "Аркадия": "arkadia",
    "Селестия": "celestia",
    "Этерия": "eteria",
    "Хиперион": "giperion",
    "Халидон": "halidon",
}

# Имена глав МИД
foreign_ministers = {
    "Аркадия": "Мирослав",
    "Селестия": "Меркуцио",
    "Хиперион": "Джон",
    "Этерия": "Цзинь Лун",
    "Халидон": "Сулейман",
}


def transform_filename(file_path):
    path_parts = file_path.split('/')
    for i, part in enumerate(path_parts):
        for ru_name, en_name in translation_dict.items():
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)
    transformed_path = '/'.join(path_parts)
    return transformed_path


reverse_translation_dict = {v: k for k, v in translation_dict.items()}


def calculate_font_size():
    """Рассчитывает базовый размер шрифта на основе высоты окна."""
    base_height = 720  # Базовая высота окна для нормального размера шрифта
    default_font_size = 16  # Базовый размер шрифта
    scale_factor = Window.height / base_height  # Коэффициент масштабирования
    return max(8, int(default_font_size * scale_factor))  # Минимальный размер шрифта — 8


class AdvisorView(FloatLayout):
    def __init__(self, faction, **kwargs):
        super(AdvisorView, self).__init__(**(kwargs))
        self.faction = faction
        self.db_connection = sqlite3.connect('game_data.db')  # Подключение к базе данных
        self.cursor = self.db_connection.cursor()

        self.relations_path = r'files\config\status\dipforce'
        self.relations_file = r'files\config\status\dipforce\relations.json'

        # Инициализация таблицы political_systems
        self.initialize_political_systems()
        # Настройки темы
        self.colors = {
            'background': (0.95, 0.95, 0.95, 1),
            'primary': (0.118, 0.255, 0.455, 1),  # Темно-синий
            'accent': (0.227, 0.525, 0.835, 1),  # Голубой
            'text': (1, 1, 1, 1),
            'card': (1, 1, 1, 1)
        }

        # Создаем главное окно
        self.interface_window = FloatLayout(size_hint=(1, 1))

        # Основной контейнер
        main_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(20),
            padding=dp(20),
            size_hint=(1, 1)
        )

        # Левая панель с изображением
        left_panel = FloatLayout(size_hint=(0.45, 1))

        # Правая панель
        right_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.55, 1),
            spacing=0,
            padding=0
        )

        # Панель вкладок
        tabs_panel = ScrollView(
            size_hint=(1, None),
            height=Window.height * 0.3,  # Адаптивная высота
            bar_width=dp(8),
            bar_color=(0.5, 0.5, 0.5, 0.5)
        )
        self.tabs_content = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=dp(10),
            padding=dp(5)
        )
        self.tabs_content.bind(minimum_height=self.tabs_content.setter('height'))
        tabs_panel.add_widget(self.tabs_content)
        right_panel.add_widget(tabs_panel)

        # Сборка интерфейса
        main_layout.add_widget(left_panel)
        main_layout.add_widget(right_panel)

        # Нижняя панель с кнопками
        bottom_panel = BoxLayout(
            size_hint=(1, None),
            height=Window.height * 0.1,  # Адаптивная высота
            padding=dp(10),
            pos_hint={'x': 0, 'y': 0},
            spacing=dp(10)
        )

        # Кнопки в нижней панели
        close_button = Button(
            text="Закрыть",
            size_hint=(None, None),
            size=(Window.width * 0.2, Window.height * 0.08),  # Адаптивный размер
            background_normal='',
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=Window.height * 0.02,  # Размер шрифта зависит от высоты окна
            bold=True,
            border=(0, 0, 0, 0)
        )
        close_button.bind(on_press=self.close_window)

        political_system_button = Button(
            text="Полит. строй",
            size_hint=(None, None),
            size=(Window.width * 0.2, Window.height * 0.08),  # Адаптивный размер
            background_normal='',
            background_color=(0.227, 0.525, 0.835, 1),
            color=(1, 1, 1, 1),
            font_size=Window.height * 0.02,  # Размер шрифта зависит от высоты окна
            bold=True,
            border=(0, 0, 0, 0)
        )
        political_system_button.bind(on_press=lambda x: self.show_political_systems())

        relations_button = Button(
            text="Отношения",
            size_hint=(None, None),
            size=(Window.width * 0.2, Window.height * 0.08),  # Адаптивный размер
            background_normal='',
            background_color=(0.118, 0.255, 0.455, 1),
            color=(1, 1, 1, 1),
            font_size=Window.height * 0.02,  # Размер шрифта зависит от высоты окна
            bold=True,
            border=(0, 0, 0, 0)
        )
        relations_button.bind(on_press=lambda x: self.show_relations("Состояние отношений"))

        bottom_panel.add_widget(close_button)
        bottom_panel.add_widget(political_system_button)
        bottom_panel.add_widget(relations_button)

        self.interface_window.add_widget(main_layout)
        self.interface_window.add_widget(bottom_panel)

        # Создаем Popup
        self.popup = Popup(
            title=f"",  # Жирный шрифт с помощью [b][/b]
            title_size=Window.height * 0.03,  # Размер заголовка зависит от высоты окна
            title_align="center",  # Центрирование текста (по умолчанию уже centered, но явно указываем)
            content=self.interface_window,
            size_hint=(0.7, 0.7),
            separator_height=dp(0),
            background=f'files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg' if os.path.exists(
                f'files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg') else ''
        )
        self.popup.open()

    def show_political_systems(self):
        """
        Отображает окно с таблицей политических систем и их влияния на отношения.
        """
        # Загружаем данные о политических системах
        political_systems = self.load_political_systems()
        if not political_systems:
            print(f"Нет данных о политических системах для фракции {self.faction}.")
            return

        # Создаем основной контейнер
        main_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(10),
            size_hint=(1, 1)
        )

        # Заголовок
        header = Label(
            text=f"Политические системы ({self.faction})",
            font_size=Window.height * 0.03,
            bold=True,
            size_hint_y=None,
            height=Window.height * 0.06,
            color=(0.15, 0.15, 0.15, 1)
        )
        main_layout.add_widget(header)

        # Таблица с данными (3 столбца)
        table = GridLayout(
            cols=3,
            size_hint_y=None,
            spacing=dp(5),
            row_default_height=Window.height * 0.06
        )
        table.bind(minimum_height=table.setter('height'))

        # Заголовки таблицы
        table.add_widget(self.create_header("Фракция"))
        table.add_widget(self.create_header("Полит. строй"))
        table.add_widget(self.create_header("Влияние на отношения"))

        # Добавление данных
        for faction, data in political_systems.items():
            system = data["system"]  # Политическая система фракции

            # Определяем, какая стрелочка будет отображена
            if system == self.load_political_system():
                influence_widget = self.create_arrow_icon("up", color=(0, 0.75, 0, 1))  # Зеленая стрелка вверх
            else:
                influence_widget = self.create_arrow_icon("down", color=(0.8, 0, 0, 1))  # Красная стрелка вниз

            # Добавляем данные в таблицу
            table.add_widget(self.create_cell(faction))
            table.add_widget(self.create_cell(system))
            table.add_widget(influence_widget)

        # Прокрутка
        scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(8),
            bar_color=(0.4, 0.4, 0.4, 0.6)
        )
        scroll.add_widget(table)
        main_layout.add_widget(scroll)

        # Выбор политической системы
        system_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=Window.height * 0.1,
            spacing=dp(10)
        )

        capitalism_button = Button(
            text="Капитализм",
            background_color=(0.2, 0.7, 0.3, 1),
            size_hint=(0.5, 1)
        )
        communism_button = Button(
            text="Коммунизм",
            background_color=(0.8, 0.2, 0.2, 1),
            size_hint=(0.5, 1)
        )

        capitalism_button.bind(on_press=lambda x: self.update_political_system("Капитализм"))
        communism_button.bind(on_press=lambda x: self.update_political_system("Коммунизм"))

        system_layout.add_widget(capitalism_button)
        system_layout.add_widget(communism_button)
        main_layout.add_widget(system_layout)

        # Настройка попапа
        popup = Popup(
            title='',
            content=main_layout,
            size_hint=(0.8, 0.8),
            background_color=(0.96, 0.96, 0.96, 1),
            overlay_color=(0, 0, 0, 0.2)
        )
        popup.open()

        # Сохраняем ссылку на текущий попап
        self.popup = popup

    def create_arrow_icon(self, direction, color):
        """
        Создает виджет с изображением стрелки.
        :param direction: "up" или "down" (направление стрелки)
        :param color: кортеж (r, g, b, a) для цвета стрелки
        :return: виджет с изображением стрелки
        """
        arrow_text = "^" if direction == "up" else "v"  # Символы стрелок
        return Label(
            text=arrow_text,
            font_size=Window.height * 0.025,
            bold=True,
            color=color,
            size_hint_y=None,
            height=Window.height * 0.06,
            halign="center",
            valign="middle"
        )

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

    def load_political_systems(self):
        """
        Загружает данные о политических системах всех фракций из базы данных.
        Возвращает словарь, где ключи — названия фракций, а значения — информация о системе и её влиянии.
        """
        try:
            query = "SELECT faction, system FROM political_systems"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь
            systems = {}
            for faction, system in rows:
                systems[faction] = {
                    "system": system,
                    "influence": self.get_influence_description(system)
                }
            return systems
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политических систем: {e}")
            return {}

    def get_influence_description(self, system):
        """
        Возвращает текстовое описание влияния политической системы.
        """
        if system == "Капитализм":
            return 15
        elif system == "Коммунизм":
            return 15
        else:
            return "Неизвестное влияние"

    def initialize_political_systems(self):
        """
        Инициализирует таблицу political_systems значениями по умолчанию,
        если она пуста. Политическая система для каждой фракции выбирается случайным образом.
        Условие: не может быть меньше 2 и больше 3 стран с одним политическим строем.
        """
        try:
            # Проверяем, есть ли записи в таблице
            self.cursor.execute("SELECT COUNT(*) FROM political_systems")
            count = self.cursor.fetchone()[0]
            if count == 0:
                # Список всех фракций
                factions = ["Аркадия", "Селестия", "Хиперион", "Этерия", "Халидон"]

                # Список возможных политических систем
                systems = ["Капитализм", "Коммунизм"]

                # Функция для проверки распределения
                def is_valid_distribution(distribution):
                    counts = {system: distribution.count(system) for system in systems}
                    return all(2 <= count <= 3 for count in counts.values())

                # Генерация случайного распределения
                while True:
                    default_systems = [(faction, random.choice(systems)) for faction in factions]
                    distribution = [system for _, system in default_systems]

                    if is_valid_distribution(distribution):
                        break

                # Вставляем данные в таблицу
                self.cursor.executemany(
                    "INSERT INTO political_systems (faction, system) VALUES (?, ?)",
                    default_systems
                )
                self.db_connection.commit()
                print("Таблица political_systems инициализирована случайными значениями.")
        except sqlite3.Error as e:
            print(f"Ошибка при инициализации таблицы political_systems: {e}")

    def update_political_system(self, new_system):
        """
        Обновляет политическую систему фракции в базе данных и пересоздает окно.
        """
        try:
            # Обновляем политическую систему в базе данных
            query = """
                INSERT INTO political_systems (faction, system)
                VALUES (?, ?)
                ON CONFLICT(faction) DO UPDATE SET system = excluded.system
            """
            self.cursor.execute(query, (self.faction, new_system))
            self.db_connection.commit()
            print(f"Политическая система обновлена: {new_system}")

            # Пересоздаем окно с обновленными данными
            if hasattr(self, 'popup') and self.popup:
                self.popup.dismiss()  # Закрываем текущее окно
            self.show_political_systems()  # Показываем обновленное окно

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении политической системы: {e}")

    def close_window(self, instance):
        """Закрытие окна"""
        print("Метод close_window вызван.")  # Отладочный вывод
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()
        else:
            print("Ошибка: Попап не найден.")

    def trade_news(self, faction):
        """Функция для загрузки данных по торговым отношениям и построения таблицы"""
        # Загрузка данных о текущих отношениях
        relations_data = self.load_relations()

        # Проверка наличия данных
        if not relations_data or "relations" not in relations_data:
            print("Нет данных об отношениях.")
            return

        # Получаем данные о текущей фракции
        faction_relations = relations_data["relations"].get(self.faction, {})
        if not faction_relations:
            print(f"Нет данных об отношениях для фракции {self.faction}.")
            return

        # Создаем основной контейнер
        main_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(10),
            size_hint=(1, 1)
        )

        # Заголовок
        header = Label(
            text=f"Торговые условия для {self.faction}",
            font_size=Window.height * 0.03,  # Адаптивный размер шрифта
            bold=True,
            size_hint_y=None,
            height=Window.height * 0.06,  # Адаптивная высота
            color=(0.15, 0.15, 0.15, 1)
        )
        main_layout.add_widget(header)

        # Таблица с данными
        table = GridLayout(
            cols=3,
            size_hint_y=None,
            spacing=dp(5),
            row_default_height=Window.height * 0.06  # Адаптивная высота строки
        )
        table.bind(minimum_height=table.setter('height'))

        # Заголовки таблицы
        table.add_widget(self.create_header("Фракция"))
        table.add_widget(self.create_header("Торговые условия"))
        table.add_widget(self.create_header("Коэффициент"))

        # Добавление данных
        for target_faction, relation_level in faction_relations.items():
            # Определяем коэффициент на основе уровня отношений
            coefficient = self.calculate_coefficient(relation_level)

            # Формируем текстовое описание условий
            if coefficient == 0:
                condition_text = "Отказ от сделок."
            elif coefficient < 1:
                condition_text = f"Должны уступать {int((1 - coefficient) * 100)}% в сделках."
            elif coefficient == 1:
                condition_text = "Можем требовать столько же, сколько предлагаем."
            else:
                condition_text = f"Можем требовать больше на {int((coefficient - 1) * 100)}%."

            # Добавляем данные в таблицу
            table.add_widget(self.create_cell(target_faction))
            table.add_widget(self.create_cell(condition_text))
            table.add_widget(self.create_value_trade_cell(coefficient))

        # Прокрутка
        scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(8),
            bar_color=(0.4, 0.4, 0.4, 0.6)
        )
        scroll.add_widget(table)
        main_layout.add_widget(scroll)

        # Настройка попапа
        popup = Popup(
            title='',
            content=main_layout,
            size_hint=(0.8, 0.8),
            background_color=(0.96, 0.96, 0.96, 1),
            overlay_color=(0, 0, 0, 0.2)
        )
        popup.open()

    def load_trade_agreements(self, faction):
        """Загружает данные о торговых соглашениях для указанной фракции"""
        trade_file_path = transform_filename(f'files/config/status/trade_dogovor/{faction}.json')
        try:
            with open(trade_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Файл торговых соглашений для фракции {faction} не найден.")
            return {}
        except json.JSONDecodeError:
            print(f"Ошибка чтения файла торговых соглашений для фракции {faction}.")
            return {}

    def load_relations(self):
        """
        Загружает текущие отношения из таблицы relations в базе данных.
        Возвращает словарь, где ключи — названия фракций, а значения — уровни отношений.
        """
        try:
            # Выполняем запрос к таблице relations
            self.cursor.execute('''
                SELECT faction2, relationship
                FROM relations
                WHERE faction1 = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь
            relations = {faction2: relationship for faction2, relationship in rows}
            return relations

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений из таблицы relations: {e}")
            return {}

    def calculate_coefficient(self, relation_level):
        """Рассчитывает коэффициент на основе уровня отношений"""
        relation_level = int(relation_level)
        if relation_level < 15:
            return 0
        elif 15 <= relation_level < 25:
            return 0.08
        elif 25 <= relation_level < 35:
            return 0.3
        elif 35 <= relation_level < 50:
            return 0.8
        elif 50 <= relation_level < 60:
            return 1.0
        elif 60 <= relation_level < 75:
            return 1.4
        elif 75 <= relation_level < 90:
            return 2.0
        elif 90 <= relation_level <= 100:
            return 2.9
        else:
            return 0

    def load_combined_relations(self):
        """
        Загружает и комбинирует отношения из таблицы relations и файла diplomaties.json.
        Возвращает словарь, где ключи — названия фракций, а значения — словари с уровнем отношений и статусом.
        """
        # Загрузка данных из таблицы relations
        relations_data = self.load_relations()

        # Загрузка данных из таблицы diplomaties
        diplomacies_data = self.load_diplomacies()

        # Создаем комбинированный словарь отношений
        combined_relations = {}

        # Обрабатываем данные из таблицы relations
        for target_faction, relation_level in relations_data.items():
            if target_faction not in combined_relations:
                combined_relations[target_faction] = {}

            combined_relations[target_faction] = {
                "relation_level": relation_level,
                "status": "неизвестно"  # значение по умолчанию
            }

        # Добавляем/обновляем статусы из таблицы diplomaties
        for faction, data in diplomacies_data.items():
            if faction == self.faction:  # Рассматриваем только текущую фракцию
                for target_faction, status in data.get("отношения", {}).items():
                    if target_faction in combined_relations:
                        combined_relations[target_faction]["status"] = status
                    else:
                        combined_relations[target_faction] = {
                            "relation_level": 0,  # значение по умолчанию
                            "status": status
                        }

        return combined_relations

    def show_relations(self, instance):
        """Отображает окно с таблицей отношений."""
        self.manage_relations()

        # Загружаем комбинированные отношения
        combined_relations = self.load_combined_relations()

        if not combined_relations:
            print(f"Нет данных об отношениях для фракции {self.faction}.")
            return

        # Создаем основной контейнер
        main_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(10),
            size_hint=(1, 1)
        )

        # Заголовок
        header = Label(
            text=f"Отношения {self.faction}",
            font_size=Window.height * 0.03,
            bold=True,
            size_hint_y=None,
            height=Window.height * 0.06,
            color=(0.15, 0.15, 0.15, 1)
        )
        main_layout.add_widget(header)

        # Таблица с данными (4 столбца)
        table = GridLayout(
            cols=4,
            size_hint_y=None,
            spacing=dp(5),
            row_default_height=Window.height * 0.06
        )
        table.bind(minimum_height=table.setter('height'))

        # Заголовки таблицы
        table.add_widget(self.create_header("Фракция"))
        table.add_widget(self.create_header("Отношения"))
        table.add_widget(self.create_header("Кф. торговли"))
        table.add_widget(self.create_header("Статус"))

        # Добавление данных
        for country, data in combined_relations.items():
            relation_level = data["relation_level"]
            status = data["status"]

            table.add_widget(self.create_cell(country))
            table.add_widget(self.create_value_cell(relation_level))

            # Рассчитываем коэффициент
            coefficient = self.calculate_coefficient(relation_level)
            table.add_widget(self.create_value_trade_cell(coefficient))

            # Статус отношений
            table.add_widget(self.create_status_cell(status))

        # Прокрутка
        scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(8),
            bar_color=(0.4, 0.4, 0.4, 0.6)
        )
        scroll.add_widget(table)
        main_layout.add_widget(scroll)

        # Настройка попапа
        popup = Popup(
            title='',
            content=main_layout,
            size_hint=(0.8, 0.8),
            background_color=(0.96, 0.96, 0.96, 1),
            overlay_color=(0, 0, 0, 0.2)
        )
        popup.open()

    def save_relations(self, relations_data):
        """Сохраняем обновленные отношения в файл relations.json"""
        try:
            with open(self.relations_file, "w", encoding="utf-8") as f:
                json.dump(relations_data, f, ensure_ascii=False, indent=4)
        except PermissionError:
            print("Ошибка доступа к файлу relations.json. Проверьте права доступа.")

    def manage_relations(self):
        """
        Управление отношениями только для фракций, заключивших дипломатическое соглашение.
        Использует данные из таблиц БД `relations` и `diplomacies`.
        """
        # Загружаем текущие отношения из базы данных
        relations_data = self.load_relations()

        if not relations_data:
            print(f"Отношения для фракции {self.faction} не найдены.")
            return

        # Загружаем дипломатические соглашения из базы данных
        diplomacies_data = self.load_diplomacies()

        # Проверяем, есть ли дипломатические соглашения для текущей фракции
        if self.faction not in diplomacies_data:
            print(f"Дипломатические соглашения для фракции {self.faction} не найдены.")
            return

        # Получаем список фракций, с которыми заключены соглашения
        agreements = diplomacies_data[self.faction].get("отношения", {})

        for target_faction, status in agreements.items():
            if status == "союз":  # Рассматриваем только фракции с дипломатическим союзом
                # Проверяем, есть ли отношения с этой фракцией
                if target_faction in relations_data:
                    current_value_self = relations_data[target_faction]
                    current_value_other = self.load_relations_for_target(target_faction).get(self.faction, 0)

                    # Увеличиваем уровень отношений (не более 100)
                    relations_data[target_faction] = min(current_value_self + 7, 100)
                    self.update_relations_in_db(target_faction, min(current_value_other + 7, 100))

        # Сохраняем обновленные данные в базу данных
        self.save_relations_to_db(relations_data)

    def load_relations_for_target(self, target_faction):
        """
        Загружает отношения для указанной целевой фракции.
        Возвращает словарь, где ключи — названия фракций, а значения — уровни отношений.
        """
        try:
            self.cursor.execute('''
                SELECT faction2, relationship
                FROM relations
                WHERE faction1 = ?
            ''', (target_faction,))
            rows = self.cursor.fetchall()
            return {faction2: relationship for faction2, relationship in rows}
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений для фракции {target_faction}: {e}")
            return {}

    def update_relations_in_db(self, target_faction, new_value):
        """
        Обновляет уровень отношений в базе данных для указанной целевой фракции.
        """
        try:
            self.cursor.execute('''
                UPDATE relations
                SET relationship = ?
                WHERE faction1 = ? AND faction2 = ?
            ''', (new_value, target_faction, self.faction))
            self.db_connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении отношений для фракции {target_faction}: {e}")

    def save_relations_to_db(self, relations_data):
        """
        Сохраняет обновленные отношения в базу данных.
        """
        try:
            for target_faction, relationship in relations_data.items():
                self.cursor.execute('''
                    UPDATE relations
                    SET relationship = ?
                    WHERE faction1 = ? AND faction2 = ?
                ''', (relationship, self.faction, target_faction))
            self.db_connection.commit()
            print("Отношения успешно сохранены в базе данных.")
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении отношений в базе данных: {e}")

    def load_diplomacies(self):
        """Загружает данные о дипломатических отношениях из файла."""
        try:
            file_path = "files/config/status/diplomaties.json"
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Файл diplomaties.json не найден.")
            return {}

    def create_status_cell(self, status):
        """Создает ячейку со статусом отношений и цветовой маркировкой."""
        color = self.get_status_color(status)
        lbl = Label(
            text=status.capitalize(),
            font_size=Window.height * 0.022,
            bold=True,
            color=color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=Window.height * 0.06
        )
        return lbl

    def get_status_color(self, status):
        """Определяет цвет на основе статуса отношений."""
        if status == "война":
            return (1, 0, 0, 1)  # Красный
        elif status == "нейтралитет":
            return (1, 1, 1, 1)  # Белый
        elif status == "союз":
            return (0, 0.75, 0.8, 1)  # Синий
        else:
            return (0.5, 0.5, 0.5, 1)  # Серый (для неизвестного статуса)

    def create_header(self, text):
        """Создает ячейку заголовка таблицы"""
        lbl = Label(
            text=text,
            bold=True,
            font_size=Window.height * 0.025,  # Адаптивный размер шрифта
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=Window.height * 0.06  # Адаптивная высота
        )
        with lbl.canvas.before:
            Color(0.15, 0.24, 0.35, 1)  # Темно-синий фон
            rect = Rectangle(size=lbl.size, pos=lbl.pos)
        lbl.bind(pos=lambda instance, value: setattr(rect, 'pos', instance.pos))
        lbl.bind(size=lambda instance, value: setattr(rect, 'size', instance.size))
        return lbl

    def create_cell(self, text):
        """Создает ячейку с названием фракции (белый цвет и жирный шрифт)"""
        lbl = Label(
            text=text,
            font_size=Window.height * 0.022,  # Адаптивный размер шрифта
            bold=True,
            color=(1, 1, 1, 1),  # Белый цвет текста
            halign='left',
            valign='middle',
            padding_x=dp(15),
            size_hint_y=None,
            height=Window.height * 0.06  # Адаптивная высота
        )
        lbl.bind(size=lbl.setter('text_size'))  # Автоматический перенос текста
        return lbl

    def create_text_cell(self, text):
        """
        Создает ячейку с текстовым описанием (например, бонусов политической системы).
        """
        lbl = Label(
            text=text,
            font_size=Window.height * 0.022,  # Адаптивный размер шрифта
            bold=True,
            color=(0, 0, 0, 1),  # Черный цвет текста
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=Window.height * 0.06  # Адаптивная высота
        )
        return lbl

    def create_value_cell(self, value):
        """Создает ячейку со значением отношений"""
        color = self.get_relation_color(value)
        lbl = Label(
            text=f"{value}%",
            font_size=Window.height * 0.022,  # Адаптивный размер шрифта
            bold=True,
            color=color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=Window.height * 0.06  # Адаптивная высота
        )
        return lbl

    def create_value_trade_cell(self, value):
        """Создает ячейку с коэффициентом"""
        color = self.get_relation_trade_color(value)
        lbl = Label(
            text=f"{value:.2f}",
            font_size=Window.height * 0.022,  # Адаптивный размер шрифта
            bold=True,
            color=color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=Window.height * 0.06  # Адаптивная высота
        )
        return lbl

    def get_relation_trade_color(self, value):
        """Возвращает цвет в зависимости от значения коэффициента"""
        if value <= 0.08:
            return (0.8, 0.1, 0.1, 1)  # Красный
        elif 0.08 < value <= 0.3:
            return (1.0, 0.5, 0.0, 1)  # Оранжевый
        elif 0.3 < value <= 0.8:
            return (1.0, 0.8, 0.0, 1)  # Желтый
        elif 0.8 < value <= 1.0:
            return (0.2, 0.7, 0.3, 1)  # Зеленый
        elif 1.0 < value <= 1.4:
            return (0.0, 0.8, 0.8, 1)  # Голубой
        elif 1.4 < value <= 2.0:
            return (0.0, 0.6, 1.0, 1)  # Синий
        elif 2.0 < value <= 2.9:
            return (0.1, 0.3, 0.9, 1)  # Темно-синий
        else:
            return (1, 1, 1, 1)  # Белый

    def update_rect(self, instance, value):
        """Обновляет позицию и размер прямоугольника фона"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def get_relation_color(self, value):
        """Возвращает цвет в зависимости от значения"""
        value = int(value)
        if value <= 15:
            return (0.8, 0.1, 0.1, 1)
        elif 15 < value <= 25:
            return (1.0, 0.5, 0.0, 1)
        elif 25 < value <= 35:
            return (1.0, 0.8, 0.0, 1)
        elif 35 < value <= 50:
            return (0.2, 0.7, 0.3, 1)
        elif 50 < value <= 60:
            return (0.0, 0.8, 0.8, 1)
        elif 60 < value <= 75:
            return (0.0, 0.6, 1.0, 1)
        elif 75 < value <= 90:
            return (0.1, 0.3, 0.9, 1)
        else:
            return (1, 1, 1, 1)
