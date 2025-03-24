import json
import os
import shutil

from kivy.core.window import Window
from kivy.graphics import Rectangle, Color
from kivy.properties import partial
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from army import open_weapon_db_management
from kivy.uix.image import Image as KivyImage
from kivy.uix.textinput import TextInput

import fight
import sqlite3

arkadia_file_path = "files/config/manage_ii/arkadia_in_city.json"
celestia_file_path = "files/config/manage_ii/celestia_in_city.json"
eteria_file_path = "files/config/manage_ii/eteria_in_city.json"
giperion_file_path = "files/config/manage_ii/giperion_in_city.json"
halidon_file_path = "files/config/manage_ii/halidon_in_city.json"
all_arms_file_path = "files/config/arms/all_arms.json"

translation_dict = {
    "Аркадия": "arkadia",
    "Селестия": "celestia",
    "Этерия": "eteria",
    "Хиперион": "giperion",
    "Халидон": "halidon",
}

# Установка мягких цветов для фона
Window.clearcolor = (0.95, 0.95, 0.95, 1)  # Светло-серый фон


def get_faction_of_city(city_name):
    try:
        with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
            diplomacies = json.load(file)
        for faction, data in diplomacies.items():
            if city_name in data.get("города", []):
                return faction
        print(f"Город '{city_name}' не принадлежит ни одной фракции.")
        return None
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при загрузке diplomacies.json: {e}")
        return None


def backup_files():
    # Определяем путь к исходным и резервным файлам
    backup_dir = 'files/config/backup/save'
    city_file_path = 'files/config/city.json'
    diplomaties_file_path = 'files/config/status/diplomaties.json'

    # Проверяем, существует ли директория для резервных копий, если нет - создаем её
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Определяем пути для резервных копий
    city_backup_path = os.path.join(backup_dir, 'city_backup.json')
    diplomaties_backup_path = os.path.join(backup_dir, 'diplomaties_backup.json')

    # Копируем файлы в каталог backup
    shutil.copy(city_file_path, city_backup_path)
    shutil.copy(diplomaties_file_path, diplomaties_backup_path)

    print("Резервные копии файлов сохранены в:", backup_dir)


def merge_army_and_ii_files():
    # Список всех файлов, которые нужно объединить
    file_paths = [
        arkadia_file_path,
        celestia_file_path,
        eteria_file_path,
        giperion_file_path,
        halidon_file_path
    ]

    # Инициализация словаря для хранения объединенных данных
    merged_data = {}

    # Проходим по каждому файлу и загружаем данные
    for file_path in file_paths:
        faction_name = os.path.splitext(os.path.basename(file_path))[0]

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                    # Добавляем данные фракции в словарь
                    merged_data[faction_name] = data
                except json.JSONDecodeError:
                    print(f"Файл {file_path} пустой или поврежден, инициализируем пустым словарем.")
                    # Инициализируем фракцию пустым словарем
                    merged_data[faction_name] = {}
        else:
            print(f"Файл {file_path} не найден, инициализируем пустым словарем.")
            # Инициализируем фракцию пустым словарем
            merged_data[faction_name] = {}

    # Сохраняем объединенные данные в all_arms.json
    with open(all_arms_file_path, "w", encoding="utf-8") as all_arms_file:
        json.dump(merged_data, all_arms_file, ensure_ascii=False, indent=4)
        print(f"Данные успешно объединены и сохранены в {all_arms_file_path}.")


def transform_filename(file_path):
    # Разбиваем путь на части
    path_parts = file_path.split('/')

    # Преобразуем название города в английский
    for i, part in enumerate(path_parts):
        # Проверяем, если часть пути содержит русское название, заменяем его на английское
        for ru_name, en_name in translation_dict.items():  # Исправлено: используем items()
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)

    # Собираем путь обратно
    return '/'.join(path_parts)


def load_json_file(filepath):
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не существует.")
        return {}

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            if os.stat(filepath).st_size == 0:  # Проверяем, пуст ли файл
                print(f"Файл {filepath} пустой.")
                return {}
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"Ошибка чтения JSON из файла {filepath}: {e}")
        return {}
    except Exception as e:
        print(f"Ошибка при открытии файла {filepath}: {e}")
        return {}


class FortressInfoPopup(Popup):
    def __init__(self, kingdom, city_coords, player_fraction, **kwargs):
        super(FortressInfoPopup, self).__init__(**kwargs)

        # Создаем подключение к БД
        self.conn = sqlite3.connect('game_data.db')
        self.cursor = self.conn.cursor()

        self.fraction = kingdom
        self.city_name = ''
        self.city_coords = list(city_coords)
        self.size_hint = (0.8, 0.8)
        self.player_fraction = player_fraction
        self.file_path2 = None
        self.file_path1 = None
        self.city_coords = city_coords  # Это кортеж (x, y)
        self.current_popup = None  # Ссылка на текущее всплывающее окно

        # Преобразуем координаты в строку для сравнения с БД
        coords_str = f"[{self.city_coords[0]}, {self.city_coords[1]}]"

        # Получаем информацию о городе из таблицы cities
        self.cursor.execute("""
            SELECT name FROM cities 
            WHERE coordinates = ?
        """, (coords_str,))

        city_data = self.cursor.fetchone()
        if city_data:
            self.city_name = city_data[0]
        else:
            print(f"Город с координатами {self.city_coords} не найден в базе данных")
            return

        self.title = f"Информация о поселении {self.city_name}"
        self.create_ui()

    def create_ui(self):
        """
        Создает масштабируемый пользовательский интерфейс.
        """
        # Базовые параметры для масштабирования
        screen_width, screen_height = Window.size
        scale_factor = screen_width / 360  # Масштабный коэффициент (360 — базовая ширина экрана)

        base_font_size = 8  # Базовый размер шрифта
        base_padding = 7  # Базовый отступ
        base_spacing = 7  # Базовое расстояние между виджетами
        base_button_height = 20  # Базовая высота кнопок

        font_size = int(base_font_size * scale_factor)
        padding = int(base_padding * scale_factor)
        spacing = int(base_spacing * scale_factor)
        button_height = int(base_button_height * scale_factor)

        # Главный макет
        main_layout = BoxLayout(orientation='vertical', padding=padding, spacing=spacing)

        # Верхняя часть: Гарнизон и здания
        columns_layout = GridLayout(cols=2, spacing=spacing, size_hint_y=0.7)

        # Левая колонка: Гарнизон
        troops_column = BoxLayout(orientation='vertical', spacing=spacing)
        troops_label = Label(
            text="Гарнизон",
            font_size=f'{font_size*1.2}sp',
            bold=True,
            size_hint_y=None,
            height=int(30 * scale_factor),
            color=(1, 1, 1, 1)  # Черный текст
        )
        troops_column.add_widget(troops_label)

        self.attacking_units_list = ScrollView(size_hint=(1, 1))
        self.attacking_units_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=spacing)
        self.attacking_units_box.bind(minimum_height=self.attacking_units_box.setter('height'))
        self.attacking_units_list.add_widget(self.attacking_units_box)
        troops_column.add_widget(self.attacking_units_list)
        columns_layout.add_widget(troops_column)

        # Правая колонка: Здания
        buildings_column = BoxLayout(orientation='vertical', spacing=spacing)
        buildings_label = Label(
            text="Здания",
            font_size=f'{font_size*1.2}sp',
            bold=True,
            size_hint_y=None,
            height=int(30 * scale_factor),
            color=(1, 1, 1, 1)  # Черный текст
        )
        buildings_column.add_widget(buildings_label)

        self.buildings_list = ScrollView(size_hint=(1, 1))
        self.buildings_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=spacing)
        self.buildings_box.bind(minimum_height=self.buildings_box.setter('height'))
        self.buildings_list.add_widget(self.buildings_box)
        buildings_column.add_widget(self.buildings_list)
        columns_layout.add_widget(buildings_column)

        main_layout.add_widget(columns_layout)

        # Нижняя часть: Кнопки действий
        button_layout = GridLayout(cols=3, size_hint_y=None, height=button_height, spacing=spacing)

        # Кнопка "Ввести войска"
        send_troops_button = Button(
            text="Ввести войска",
            font_size=f'{font_size}sp',
            size_hint_y=None,
            height=button_height,
            background_color=(0.6, 0.8, 0.6, 1)
        )
        send_troops_button.bind(on_press=self.select_troop_type)
        button_layout.add_widget(send_troops_button)

        # Кнопка "Нанести удар ДБ оружием"
        strike_weapon_button = Button(
            text="Нанести удар \nДБ оружием",
            font_size=f'{font_size}sp',
            size_hint_y=None,
            height=button_height,
            background_color=(0.8, 0.6, 0.6, 1)
        )
        strike_weapon_button.bind(on_press=self.strike_with_dbs)
        button_layout.add_widget(strike_weapon_button)

        # Кнопка "Разместить армию"
        place_army_button = Button(
            text="Разместить армию",
            font_size=f'{font_size}sp',
            size_hint_y=None,
            height=button_height,
            background_color=(0.6, 0.6, 0.8, 1)
        )
        place_army_button.bind(on_press=self.place_army)
        button_layout.add_widget(place_army_button)

        main_layout.add_widget(button_layout)

        # Кнопка "Закрыть"
        close_button = Button(
            text="Закрыть",
            font_size=f'{font_size}sp',
            size_hint_y=None,
            height=button_height,
            background_color=(0.8, 0.8, 0.8, 1)
        )
        close_button.bind(on_press=self.dismiss)
        main_layout.add_widget(close_button)

        self.content = main_layout

        # Инициализация данных
        self.get_garrison()
        self.load_buildings()

        # Ссылки на виджеты гарнизона
        self.garrison_widgets = {}  # Словарь для хранения ссылок на виджеты гарнизона

    def load_buildings(self):
        """Загружает здания в интерфейс."""
        buildings = self.get_buildings()  # Получаем список зданий

        # Очищаем контейнер перед добавлением новых данных
        self.buildings_box.clear_widgets()

        # Если зданий нет, добавляем сообщение об этом
        if not buildings:
            label = Label(
                text="Зданий нет",
                size_hint_y=None,
                height=40,
                font_size='18sp',  # Увеличиваем размер шрифта
                color=(1, 0, 0, 1),  # Ярко-красный цвет текста
                halign='center',
                valign='middle'
            )
            label.bind(size=label.setter('text_size'))  # Для корректного выравнивания текста
            self.buildings_box.add_widget(label)
            return

        # Добавляем каждое здание в интерфейс
        for building in buildings:
            # Создаем макет для одного здания
            building_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)

            # Информация о здании (текст с названием и количеством)
            text_container = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=5)
            with text_container.canvas.before:
                Color(0.1, 0.1, 0.1, 1)  # Темно-серый фон для контраста
                text_container.bg_rect = Rectangle(pos=text_container.pos, size=text_container.size)

            def update_rect(instance, value):
                """Обновляет позицию и размер фона при изменении размеров виджета."""
                if hasattr(instance, 'bg_rect'):
                    instance.bg_rect.pos = instance.pos
                    instance.bg_rect.size = instance.size

            text_container.bind(pos=update_rect, size=update_rect)

            # Текст с названием и количеством
            text_label = Label(
                text=building,
                font_size='18sp',  # Увеличиваем размер шрифта
                color=(1, 1, 1, 1),  # Белый цвет текста
                halign='left',
                valign='middle'
            )
            text_label.bind(size=text_label.setter('text_size'))  # Для корректного выравнивания текста
            text_container.add_widget(text_label)

            building_layout.add_widget(text_container)

            # Добавляем макет здания в контейнер
            self.buildings_box.add_widget(building_layout)

    def get_garrison(self):
        """Получает гарнизон города из таблицы garrisons"""
        try:
            # Запрос к базе данных для получения гарнизона
            self.cursor.execute("""
                SELECT unit_name, unit_count, unit_image 
                FROM garrisons 
                WHERE city_id = ?
            """, (self.city_name,))
            garrison_data = self.cursor.fetchall()

            # Очищаем контейнер с предыдущими данными
            self.attacking_units_box.clear_widgets()

            if not garrison_data:
                print(f"Гарнизон для города {self.city_name} пуст.")
                return

            print('Выполняется запрос к базе данных гарнизона', garrison_data)

            # Добавляем данные о каждом юните в интерфейс
            for unit_name, unit_count, unit_image in garrison_data:
                # Создаем макет для одного юнита
                unit_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, spacing=10)

                # Изображение юнита
                unit_image_widget = Image(
                    source=unit_image,
                    size_hint=(None, None),
                    size=(110, 110)  # Увеличиваем размер изображения
                )
                unit_layout.add_widget(unit_image_widget)

                # Информация о юните (текст с названием и количеством)
                text_container = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=5)
                with text_container.canvas.before:
                    Color(0.3, 0.3, 0.3, 1)
                    text_container.bg_rect = Rectangle(pos=text_container.pos, size=text_container.size)

                def update_rect(instance, value):
                    """Обновляет позицию и размер фона при изменении размеров виджета."""
                    if hasattr(instance, 'bg_rect'):
                        instance.bg_rect.pos = instance.pos
                        instance.bg_rect.size = instance.size

                text_container.bind(pos=update_rect, size=update_rect)

                # Текст с названием и количеством
                unit_text = f"{unit_name}\nКоличество: {unit_count}"
                text_label = Label(
                    text=unit_text,
                    font_size='16sp',  # Увеличиваем размер шрифта
                    color=(1, 1, 1, 1),  # Белый текст
                    halign='left',
                    valign='middle'
                )
                text_label.bind(size=text_label.setter('text_size'))  # Для корректного выравнивания текста
                text_container.add_widget(text_label)

                unit_layout.add_widget(text_container)

                # Добавляем макет юнита в контейнер
                self.attacking_units_box.add_widget(unit_layout)

        except Exception as e:
            print(f"Ошибка при получении гарнизона: {e}")

    def get_buildings(self):
        """Получает количество зданий в указанном городе из таблицы buildings."""
        try:
            # Выполняем запрос к базе данных
            self.cursor.execute("""
                SELECT building_type, count 
                FROM buildings 
                WHERE city_name = ? AND faction = ?
            """, (self.city_name, self.fraction))

            buildings_data = self.cursor.fetchall()

            # Формируем список с информацией о зданиях
            buildings = [f"{building_type}: {count}" for building_type, count in buildings_data]

            # Если зданий нет, возвращаем пустой список
            return buildings if buildings else []

        except Exception as e:
            print(f"Ошибка при получении данных о зданиях: {e}")
            return []

    def select_troop_type(self, instance=None):
        """
        Открывает окно для выбора типа войск: Защитные, Атакующие, Любые.
        :param instance: Экземпляр виджета, который вызвал метод (не используется).
        """
        popup = Popup(title="Выберите тип войск", size_hint=(0.6, 0.4))
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Кнопки для выбора типа войск
        defensive_button = Button(text="Защитные", background_color=(0.6, 0.8, 0.6, 1))
        offensive_button = Button(text="Атакующие", background_color=(0.8, 0.6, 0.6, 1))
        any_button = Button(text="Любые", background_color=(0.6, 0.6, 0.8, 1))

        # Привязка действий к кнопкам
        defensive_button.bind(on_press=lambda btn: self.load_troops_by_type("Защитные", popup))
        offensive_button.bind(on_press=lambda btn: self.load_troops_by_type("Атакующие", popup))
        any_button.bind(on_press=lambda btn: self.load_troops_by_type("Любые", popup))

        # Добавляем кнопки в макет
        layout.add_widget(defensive_button)
        layout.add_widget(offensive_button)
        layout.add_widget(any_button)

        # Устанавливаем содержимое окна и открываем его
        popup.content = layout
        popup.open()

    def select_troops(self, selected_data):
        """
        Обрабатывает выбор войск для перемещения и выполняет обновление данных в базе данных.
        :param selected_data: Кортеж с данными о выбранном юните (город, название юнита, количество).
        """
        try:
            # Распаковываем данные о выбранном юните
            source_city_id, unit_name, unit_count = selected_data

            # Запрос у пользователя количества юнитов для переноса
            popup = Popup(title="Выберите количество", size_hint=(0.6, 0.4))
            layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

            input_label = Label(text=f"Введите количество {unit_name} (доступно: {unit_count}):")
            count_input = TextInput(multiline=False, input_filter='int')  # Разрешаем только целые числа
            layout.add_widget(input_label)
            layout.add_widget(count_input)

            # Кнопки подтверждения и отмены
            button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
            confirm_button = Button(text="Подтвердить", background_color=(0.6, 0.8, 0.6, 1))
            cancel_button = Button(text="Отмена", background_color=(0.8, 0.6, 0.6, 1))

            def confirm_action(btn):
                try:
                    # Получаем введенное количество
                    taken_count = int(count_input.text)

                    if 0 < taken_count <= unit_count:
                        # Выполняем перенос войск
                        self.transfer_troops_between_cities(source_city_id, self.city_name, unit_name, taken_count)

                        # Закрываем окно ввода
                        popup.dismiss()

                        # Обновляем интерфейс гарнизона
                        self.update_garrison()

                        # Закрываем текущее окно выбора войск
                        self.current_popup.dismiss()

                        # Показываем обновленное окно выбора войск
                        self.show_troops_selection(self.load_troops_data())
                    else:
                        # Показываем ошибку, если количество некорректно
                        error_popup = Popup(
                            title="Ошибка",
                            content=Label(text="Некорректное количество"),
                            size_hint=(0.6, 0.4)
                        )
                        error_popup.open()
                except ValueError:
                    # Обработка случая, если ввод не является числом
                    error_popup = Popup(
                        title="Ошибка",
                        content=Label(text="Введите число"),
                        size_hint=(0.6, 0.4)
                    )
                    error_popup.open()

            confirm_button.bind(on_press=confirm_action)
            cancel_button.bind(on_press=popup.dismiss)

            button_layout.add_widget(confirm_button)
            button_layout.add_widget(cancel_button)
            layout.add_widget(button_layout)

            popup.content = layout
            popup.open()

        except Exception as e:
            print(f"Ошибка при выборе войск: {e}")

    def load_troops_data(self):
        """
        Загружает данные о войсках из базы данных.
        :return: Список войск.
        """
        try:
            cursor = self.cursor
            cursor.execute("""
                SELECT city_id, unit_name, unit_count, unit_image 
                FROM garrisons
            """)
            troops_data = cursor.fetchall()
            return troops_data
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных о войсках: {e}")
            return []

    def transfer_troops_between_cities(self, source_city_id, destination_city_id, unit_name, taken_count):
        """
        Переносит войска из одного города в другой.
        :param source_city_id: Идентификатор исходного города.
        :param destination_city_id: Идентификатор целевого города.
        :param unit_name: Название юнита.
        :param taken_count: Количество юнитов для переноса.
        """
        try:
            cursor = self.cursor

            # Шаг 1: Проверяем наличие юнитов в исходном городе
            cursor.execute("""
                SELECT unit_count, unit_image FROM garrisons 
                WHERE city_id = ? AND unit_name = ?
            """, (source_city_id, unit_name))
            source_unit = cursor.fetchone()

            if not source_unit or source_unit[0] < taken_count:
                print(f"Ошибка: недостаточно юнитов '{unit_name}' в городе '{source_city_id}'.")
                return

            # Получаем изображение юнита
            unit_image = source_unit[1]

            # Шаг 2: Обновляем количество юнитов в исходном городе
            remaining_count = source_unit[0] - taken_count
            if remaining_count > 0:
                cursor.execute("""
                    UPDATE garrisons 
                    SET unit_count = ? 
                    WHERE city_id = ? AND unit_name = ?
                """, (remaining_count, source_city_id, unit_name))
            else:
                cursor.execute("""
                    DELETE FROM garrisons 
                    WHERE city_id = ? AND unit_name = ?
                """, (source_city_id, unit_name))

            # Шаг 3: Проверяем наличие юнитов в целевом городе
            cursor.execute("""
                SELECT unit_count FROM garrisons 
                WHERE city_id = ? AND unit_name = ?
            """, (destination_city_id, unit_name))
            destination_unit = cursor.fetchone()

            if destination_unit:
                # Если юнит уже есть, увеличиваем его количество
                new_count = destination_unit[0] + taken_count
                cursor.execute("""
                    UPDATE garrisons 
                    SET unit_count = ? 
                    WHERE city_id = ? AND unit_name = ?
                """, (new_count, destination_city_id, unit_name))
            else:
                # Если юнита нет, добавляем новую запись с изображением
                cursor.execute("""
                    INSERT INTO garrisons (city_id, unit_name, unit_count, unit_image)
                    VALUES (?, ?, ?, ?)
                """, (destination_city_id, unit_name, taken_count, unit_image))

            # Сохраняем изменения в базе данных
            self.conn.commit()
            print("Войска успешно перенесены.")

        except sqlite3.Error as e:
            print(f"Произошла ошибка при работе с базой данных: {e}")
        except Exception as e:
            print(f"Произошла ошибка при переносе войск: {e}")

    def load_troops_by_type(self, troop_type, previous_popup):
        """
        Загружает войска из гарнизонов в зависимости от выбранного типа.
        :param troop_type: Тип войск ("Defensive", "Offensive", "Any").
        :param previous_popup: Предыдущее всплывающее окно для закрытия.
        """
        try:
            # Закрываем предыдущее окно
            previous_popup.dismiss()

            # Шаг 1: Получаем все юниты из таблицы garrisons
            self.cursor.execute("""
                SELECT city_id, unit_name, unit_count, unit_image 
                FROM garrisons
            """)
            all_troops = self.cursor.fetchall()

            if not all_troops:
                # Если войск нет, показываем сообщение
                error_popup = Popup(
                    title="Ошибка",
                    content=Label(text=f"Нет доступных войск."),
                    size_hint=(0.6, 0.4)
                )
                error_popup.open()
                return

            # Шаг 2: Фильтруем юниты по типу (атакующие, защитные, любые)
            filtered_troops = []
            for city_id, unit_name, unit_count, unit_image in all_troops:
                # Получаем характеристики юнита из таблицы units
                self.cursor.execute("""
                    SELECT attack, defense, durability 
                    FROM units 
                    WHERE unit_name = ?
                """, (unit_name,))
                unit_stats = self.cursor.fetchone()

                if not unit_stats:
                    print(f"Характеристики для юнита '{unit_name}' не найдены.")
                    continue

                attack, defense, durability = unit_stats

                # Определяем тип юнита
                if troop_type == "Защитные":
                    if defense > attack and defense > durability:
                        filtered_troops.append((city_id, unit_name, unit_count, unit_image))
                elif troop_type == "Атакующие":
                    if attack > defense and attack > durability:
                        filtered_troops.append((city_id, unit_name, unit_count, unit_image))
                else:  # "Any"
                    filtered_troops.append((city_id, unit_name, unit_count, unit_image))

            if not filtered_troops:
                # Если подходящих войск нет, показываем сообщение
                error_popup = Popup(
                    title="Ошибка",
                    content=Label(text=f"Нет доступных {troop_type.lower()} войск."),
                    size_hint=(0.6, 0.4)
                )
                error_popup.open()
                return

            # Открываем окно с выбором войск
            self.show_troops_selection(filtered_troops)

        except Exception as e:
            print(f"Ошибка при загрузке войск: {e}")

    def show_troops_selection(self, troops_data):
        """
        Отображает окно с выбором войск.
        :param troops_data: Список войск, полученный из базы данных.
        """
        popup = Popup(title="Выберите войска для перемещения", size_hint=(0.9, 0.9))
        self.current_popup = popup  # Сохраняем ссылку на текущее окно

        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Создаем таблицу для отображения войск
        table_layout = GridLayout(cols=5, spacing=10, size_hint_y=None)
        table_layout.bind(minimum_height=table_layout.setter('height'))

        headers = ["Город", "Юнит", "Количество", "Изображение", "Действие"]
        for header in headers:
            label = Label(
                text=header,
                font_size='14sp',
                bold=True,
                size_hint_y=None,
                height=40,
                color=(1, 1, 1, 1)
            )
            table_layout.add_widget(label)

        for city_id, unit_name, unit_count, unit_image in troops_data:
            # Город
            city_label = Label(
                text=city_id,
                font_size='14sp',
                size_hint_y=None,
                height=60,
                color=(1, 1, 1, 1)
            )
            table_layout.add_widget(city_label)

            # Юнит
            unit_label = Label(
                text=unit_name,
                font_size='14sp',
                size_hint_y=None,
                height=60,
                color=(1, 1, 1, 1)
            )
            table_layout.add_widget(unit_label)

            # Количество
            count_label = Label(
                text=str(unit_count),
                font_size='14sp',
                size_hint_y=None,
                height=60,
                color=(1, 1, 1, 1)
            )
            table_layout.add_widget(count_label)

            # Изображение
            image_container = BoxLayout(size_hint_y=None, height=60)
            unit_image_widget = Image(
                source=unit_image,
                size_hint=(None, None),
                size=(50, 50)
            )
            image_container.add_widget(unit_image_widget)
            table_layout.add_widget(image_container)

            # Кнопка действия
            action_button = Button(
                text="Выбрать",
                font_size='14sp',
                size_hint_y=None,
                height=40,
                background_color=(0.6, 0.8, 0.6, 1)
            )
            action_button.bind(on_press=lambda btn, data=(city_id, unit_name, unit_count): self.select_troops(data))
            table_layout.add_widget(action_button)

        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(table_layout)
        main_layout.add_widget(scroll_view)

        # Кнопка для закрытия окна
        close_button = Button(text="Закрыть", size_hint_y=None, height=50, background_color=(0.8, 0.8, 0.8, 1))
        close_button.bind(on_press=popup.dismiss)
        main_layout.add_widget(close_button)

        popup.content = main_layout
        popup.open()

    def update_garrison(self):
        """
        Обновляет данные о гарнизоне на интерфейсе с сохранением стиля.
        """
        try:
            # Очищаем текущие виджеты гарнизона
            self.attacking_units_box.clear_widgets()

            # Получаем актуальные данные о гарнизоне из базы данных
            cursor = self.cursor
            cursor.execute("""
                SELECT unit_name, unit_count, unit_image 
                FROM garrisons 
                WHERE city_id = ?
            """, (self.city_name,))
            garrison_data = cursor.fetchall()

            if not garrison_data:
                # Если гарнизон пуст, добавляем сообщение
                label = Label(
                    text="Гарнизон пуст",
                    size_hint_y=None,
                    height=60,
                    font_size='18sp',
                    color=(1, 0, 0, 1),  # Ярко-красный текст
                    halign='center',
                    valign='middle'
                )
                label.bind(size=label.setter('text_size'))  # Для корректного выравнивания текста
                self.attacking_units_box.add_widget(label)
                return

            # Добавляем новые виджеты для каждого юнита в гарнизоне
            for unit_name, unit_count, unit_image in garrison_data:
                # Создаем макет для одного юнита
                unit_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, spacing=10)

                # Изображение юнита
                unit_image_widget = Image(
                    source=unit_image,
                    size_hint=(None, None),
                    size=(110, 110)  # Увеличиваем размер изображения
                )
                unit_layout.add_widget(unit_image_widget)

                # Информация о юните (текст с названием и количеством)
                text_container = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=5)
                with text_container.canvas.before:
                    Color(0.3, 0.3, 0.3, 1)  # Темно-серый фон
                    text_container.bg_rect = Rectangle(pos=text_container.pos, size=text_container.size)

                def update_rect(instance, value):
                    """Обновляет позицию и размер фона при изменении размеров виджета."""
                    if hasattr(instance, 'bg_rect'):
                        instance.bg_rect.pos = instance.pos
                        instance.bg_rect.size = instance.size

                text_container.bind(pos=update_rect, size=update_rect)

                # Текст с названием и количеством
                unit_text = f"{unit_name}\nКоличество: {unit_count}"
                text_label = Label(
                    text=unit_text,
                    font_size='16sp',  # Увеличиваем размер шрифта
                    color=(1, 1, 1, 1),  # Белый текст
                    halign='left',
                    valign='middle'
                )
                text_label.bind(size=text_label.setter('text_size'))  # Для корректного выравнивания текста
                text_container.add_widget(text_label)

                unit_layout.add_widget(text_container)

                # Добавляем макет юнита в контейнер
                self.attacking_units_box.add_widget(unit_layout)

        except Exception as e:
            print(f"Ошибка при обновлении гарнизона: {e}")

    def add_to_garrison(self, unit, *args):
        """
        Проверяет наличие юнитов и добавляет выбранный тип войск в гарнизон.
        """
        # Создание всплывающего окна для выбора количества
        popup = Popup(title="Выберите количество", size_hint=(0.6, 0.4))
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Поле ввода количества
        input_label = Label(text=f"Введите количество {unit['unit_type']} (доступно: {unit['quantity']}):")
        count_input = TextInput(multiline=False, input_filter='int')  # Разрешаем только целые числа
        layout.add_widget(input_label)
        layout.add_widget(count_input)

        # Кнопки подтверждения и отмены
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        confirm_button = Button(text="Подтвердить", background_color=(0.6, 0.8, 0.6, 1))
        cancel_button = Button(text="Отмена", background_color=(0.8, 0.6, 0.6, 1))

        # Привязка действий к кнопкам
        def confirm_action(btn):
            try:
                count = int(count_input.text)
                if 0 < count <= unit['quantity']:
                    # Передаем unit и количество в метод
                    self.transfer_army_to_garrison(unit, count)

                    # Закрываем текущее всплывающее окно
                    popup.dismiss()

                    # Обновляем интерфейс гарнизона
                    self.update_garrison()

                    # Обновляем интерфейс, вызывая place_army заново
                    self.place_army(None)
                else:
                    # Показываем ошибку, если количество некорректно
                    error_popup = Popup(title="Ошибка", content=Label(text="Некорректное количество"),
                                        size_hint=(0.6, 0.4))
                    error_popup.open()
            except ValueError:
                # Обработка случая, если ввод не является числом
                error_popup = Popup(title="Ошибка", content=Label(text="Введите число"), size_hint=(0.6, 0.4))
                error_popup.open()

        confirm_button.bind(on_press=confirm_action)
        cancel_button.bind(on_press=popup.dismiss)

        button_layout.add_widget(confirm_button)
        button_layout.add_widget(cancel_button)
        layout.add_widget(button_layout)

        popup.content = layout
        popup.open()

    def show_warning_popup(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text="Для размещения юнитов сначала надо нанять!")
        btn = Button(text="OK", size_hint=(1, 0.3))

        popup = Popup(title="Внимание!", content=layout, size_hint=(0.5, 0.3))
        btn.bind(on_release=popup.dismiss)

        layout.add_widget(label)
        layout.add_widget(btn)

        popup.open()

    def place_army(self, instance):
        try:
            # Закрываем предыдущее всплывающее окно, если оно существует
            if self.current_popup:
                self.current_popup.dismiss()
                self.current_popup = None  # Очищаем ссылку

            cursor = self.cursor
            # Запрос для получения данных из таблицы armies
            cursor.execute("""
                SELECT unit_type, quantity, total_attack, total_defense, total_durability, unit_class, unit_image 
                FROM armies
            """)
            army_data = cursor.fetchall()

            if not army_data:
                print("Нет доступных юнитов для размещения.")
                self.show_warning_popup()
                return

            # Создаем новое всплывающее окно
            popup = Popup(title="Разместить армию", size_hint=(0.9, 0.9))
            self.current_popup = popup  # Сохраняем ссылку на текущее окно

            main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            table_layout = GridLayout(cols=5, spacing=5, size_hint_y=None)  # Уменьшаем отступы между элементами
            table_layout.bind(minimum_height=table_layout.setter('height'))

            # Базовые параметры для масштабирования (еще меньше)
            base_font_size = 8  # Очень маленький базовый размер шрифта
            base_image_width, base_image_height = 50, 50  # Меньшие размеры изображений
            screen_width, _ = Window.size
            scale_factor = screen_width / 360  # Масштабный коэффициент

            font_size = int(base_font_size * scale_factor)
            image_width = int(base_image_width * scale_factor)
            image_height = int(base_image_height * scale_factor)

            headers = ["Изображение", "Название", "Количество", "Статистика", "Действие"]
            for header in headers:
                label = Label(
                    text=header,
                    font_size=f'{font_size}sp',
                    bold=True,
                    size_hint_y=None,
                    height=80,  # Уменьшаем высоту заголовков
                    color=(1, 1, 1, 1)
                )
                table_layout.add_widget(label)

            bg_color = (0.2, 0.2, 0.2, 1)  # Цвет окна интерфейса

            def update_rect(instance, value):
                if hasattr(instance, 'bg_rect'):
                    instance.bg_rect.pos = instance.pos
                    instance.bg_rect.size = instance.size

            for unit in army_data:
                unit_type, quantity, attack, defense, durability, unit_class, unit_image = unit
                # Формируем данные о юните
                unit_data = {
                    "unit_type": unit_type,
                    "quantity": quantity,
                    "stats": {
                        "Атака": attack,
                        "Защита": defense,
                        "Живучесть": durability,
                        "Класс": unit_class
                    },
                    "unit_image": unit_image
                }

                # Изображение юнита
                image_container = BoxLayout(size_hint_y=None, height=image_height)
                unit_image_widget = KivyImage(
                    source=unit_image,
                    size_hint=(None, None),
                    size=(image_width, image_height)
                )
                image_container.add_widget(unit_image_widget)
                table_layout.add_widget(image_container)

                # Название юнита
                name_label = Label(
                    text=unit_type,
                    font_size=f'{font_size}sp',
                    size_hint_y=None,
                    height=70,  # Уменьшаем высоту
                    color=(1, 1, 1, 1)
                )
                with name_label.canvas.before:
                    Color(*bg_color)
                    name_label.bg_rect = Rectangle(pos=name_label.pos, size=name_label.size)
                name_label.bind(pos=update_rect, size=update_rect)
                table_layout.add_widget(name_label)

                # Количество юнитов
                count_label = Label(
                    text=str(quantity),
                    font_size=f'{font_size}sp',
                    size_hint_y=None,
                    height=60,  # Уменьшаем высоту
                    color=(1, 1, 1, 1)
                )
                with count_label.canvas.before:
                    Color(*bg_color)
                    count_label.bg_rect = Rectangle(pos=count_label.pos, size=count_label.size)
                count_label.bind(pos=update_rect, size=update_rect)
                table_layout.add_widget(count_label)

                # Статистика юнита
                stats_text = "\n".join([
                    f"Атака: {attack}",
                    f"Защита: {defense}",
                    f"Живучесть: {durability}",
                    f"Класс: {unit_class}"
                ])
                stats_label = Label(
                    text=stats_text,
                    font_size=f'{font_size}sp',
                    size_hint_y=None,
                    height=150,  # Уменьшаем высоту
                    color=(1, 1, 1, 1)
                )
                with stats_label.canvas.before:
                    Color(*bg_color)
                    stats_label.bg_rect = Rectangle(pos=stats_label.pos, size=stats_label.size)
                stats_label.bind(pos=update_rect, size=update_rect)
                table_layout.add_widget(stats_label)

                # Кнопка действия
                action_button = Button(
                    text="Добавить",
                    font_size=f'{font_size}sp',
                    size_hint_y=None,
                    height=70,  # Уменьшаем высоту кнопки
                    background_color=(0.6, 0.8, 0.6, 1)
                )
                action_button.bind(on_press=partial(self.add_to_garrison, unit_data))
                table_layout.add_widget(action_button)

            scroll_view = ScrollView(size_hint=(1, 1))
            scroll_view.add_widget(table_layout)
            main_layout.add_widget(scroll_view)

            close_button = Button(
                text="Закрыть",
                font_size=f'{font_size}sp',
                size_hint_y=None,
                height=30,  # Уменьшаем высоту кнопки "Закрыть"
                background_color=(0.8, 0.8, 0.8, 1)
            )
            close_button.bind(on_press=popup.dismiss)
            main_layout.add_widget(close_button)

            popup.content = main_layout
            popup.open()

        except sqlite3.Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    def transfer_army_to_garrison(self, selected_unit, taken_count):
        """
        Переносит данные о войсках из таблицы armies в таблицу garrisons.
        :param selected_unit: Словарь с данными о юните (тип, статистика, изображение и т.д.).
        :param taken_count: Количество юнитов для переноса.
        """
        print('selected_unit прилетает в transfer_army_to_garrison в таком виде:', selected_unit)
        print(f'Количество юнитов для переноса: {taken_count}')
        try:
            cursor = self.cursor

            # Извлекаем данные из selected_unit
            unit_type = selected_unit.get("unit_type")
            stats = selected_unit.get("stats", {})
            unit_image = selected_unit.get("unit_image")

            # Проверяем, что все необходимые данные присутствуют
            if not all([unit_type, taken_count, stats, unit_image]):
                raise ValueError("Некорректные данные для переноса юнита.")

            # Преобразуем stats обратно в отдельные характеристики
            total_attack = stats.get("Attack", 0)
            total_defense = stats.get("Defense", 0)
            total_durability = stats.get("Durability", 0)

            # Получаем текущее количество юнитов из таблицы armies
            cursor.execute("""
                SELECT quantity, total_attack, total_defense, total_durability 
                FROM armies
                WHERE faction = ? AND unit_type = ?
            """, (self.player_fraction, unit_type))

            result = cursor.fetchone()

            if not result:
                print(f"Юнит '{unit_type}' не найден в таблице armies.")
                return

            old_count, current_attack, current_defense, current_durability = result

            # Проверяем, что можно взять указанное количество юнитов
            if taken_count > old_count:
                print(f"Ошибка: нельзя взять больше, чем есть. {unit_type}: {taken_count} > {old_count}")
                return

            # Проверяем, есть ли уже такой юнит в гарнизоне
            cursor.execute("""
                SELECT unit_count FROM garrisons 
                WHERE city_id = ? AND unit_name = ?
            """, (self.city_name, unit_type))

            existing_unit = cursor.fetchone()

            if existing_unit:
                # Если юнит уже есть, обновляем количество
                new_count = existing_unit[0] + taken_count
                cursor.execute("""
                    UPDATE garrisons 
                    SET unit_count = ? 
                    WHERE city_id = ? AND unit_name = ?
                """, (new_count, self.city_name, unit_type))
            else:
                # Если юнита нет, добавляем новую запись
                cursor.execute("""
                    INSERT INTO garrisons (city_id, unit_name, unit_count, unit_image)
                    VALUES (?, ?, ?, ?)
                """, (self.city_name, unit_type, taken_count, unit_image))

            # Обновляем оставшиеся войска в таблице armies
            remaining_count = old_count - taken_count
            if remaining_count > 0:
                cursor.execute("""
                    UPDATE armies 
                    SET quantity = ?, total_attack = ?, total_defense = ?, total_durability = ?
                    WHERE faction = ? AND unit_type = ?
                """, (
                    remaining_count,
                    round(current_attack * (remaining_count / old_count), 2),
                    round(current_defense * (remaining_count / old_count), 2),
                    round(current_durability * (remaining_count / old_count), 2),
                    self.player_fraction,
                    unit_type
                ))
            else:
                # Удаляем запись, если юнитов больше не осталось
                cursor.execute("""
                    DELETE FROM armies 
                    WHERE faction = ? AND unit_type = ?
                """, (self.player_fraction, unit_type))

            # Сохраняем изменения в базе данных
            self.conn.commit()
            print("Данные успешно перенесены из таблицы armies в таблицу garrisons.")

        except sqlite3.Error as e:
            print(f"Произошла ошибка при работе с базой данных: {e}")
        except Exception as e:
            print(f"Произошла ошибка при переносе данных: {e}")

    def check_city_attack(self):
        fractions = get_faction_of_city(self.city_name)
        flag_path = f'files/config/attack_in_city/{transform_filename(fractions)}_check.txt'
        print('flag_path', flag_path)
        with open(flag_path, 'r',
                  encoding='utf-8') as file:
            status = file.read()
            print('status', status)
            if status == 'True':
                return True
            elif status == 'False':
                return False

    def choose_garrison(self, source_city_name, garrison_selection_popup):
        # Получаем фракции источника и назначения
        source_faction = get_faction_of_city(source_city_name)
        destination_faction = get_faction_of_city(self.city_name)
        if source_faction != destination_faction:
            if self.check_city_attack():
                backup_files()  # Делаем бэкап данных
                # Получаем фракции источника и назначения
                source_faction = get_faction_of_city(source_city_name)
                destination_faction = get_faction_of_city(self.city_name)

                # Обработка путей в зависимости от фракций
                if source_faction == self.player_fraction:
                    self.file_path1 = self.garrison
                    self.file_path2 = transform_filename(f'files/config/manage_ii/{destination_faction}_in_city.json')
                elif destination_faction == self.player_fraction:
                    self.file_path1 = transform_filename(f'files/config/manage_ii/{source_faction}_in_city.json')
                    self.file_path2 = self.garrison
                else:
                    self.file_path1 = transform_filename(f'files/config/manage_ii/{source_faction}_in_city.json')
                    self.file_path2 = transform_filename(f'files/config/manage_ii/{destination_faction}_in_city.json')

                if not source_faction:
                    print(f"Фракция для города '{source_city_name}' не найдена.")
                    return
                if not destination_faction:
                    print(f"Фракция для города '{self.city_name}' не найдена.")
                    return

                relationship = self.get_relationship(source_faction, destination_faction)
                if relationship == "война":
                    print(f"Фракции '{source_faction}' и '{destination_faction}' находятся в состоянии войны.")
                    # Загружаем армии
                    attacking_army = self.get_army_from_city(source_city_name)
                    defending_army = self.get_army_from_city(self.city_name)

                    # Печать предупреждений, если одна из армий не найдена
                    if not attacking_army:
                        print(f"Атакующая армия для города '{source_city_name}' не найдена.")
                    if not defending_army:
                        print(f"Армия для города '{self.city_name}' не найдена.")

                    # Передаем данные в модуль боя независимо от наличия армий
                    fight.fight(
                        user_file_path=self.file_path1,
                        ii_file_path=self.file_path2,
                        attacking_city=source_city_name,
                        attacking_fraction=source_faction,
                        defending_fraction=destination_faction,
                        defending_city_coords=self.city_coords,  # Координаты города-защитника
                        defending_city=self.city_name,
                        defending_army=defending_army,
                        attacking_army=attacking_army
                    )
                else:
                    print(
                        f"Фракции '{source_faction}' и '{destination_faction}' находятся в состоянии '{relationship}'. Войска не могут быть введены.")

                # Закрыть всплывающее окно после выполнения выбора
                garrison_selection_popup.dismiss()
                self.dismiss()
            else:
                # Создание и отображение всплывающего окна
                layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
                message = Label(text='На этом ходу уже была атака на это государство')
                close_button = Button(text='ОК', size_hint=(1, 0.3))

                layout.add_widget(message)
                layout.add_widget(close_button)

                popup = Popup(title='Предупреждение',
                              content=layout,
                              size_hint=(0.6, 0.4),
                              auto_dismiss=False)

                close_button.bind(on_release=popup.dismiss)

                popup.open()
                return
        else:
            self.update_city_data(source_city_name)
            garrison_selection_popup.dismiss()
            self.dismiss()

    def get_relationship(self, faction1, faction2):
        try:
            with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
                diplomacies = json.load(file)
            # Получаем отношения от faction1 к faction2
            relationship = diplomacies.get(faction1, {}).get("отношения", {}).get(faction2, "нейтралитет")
            return relationship
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Ошибка при загрузке diplomacies.json: {e}")
            return "нейтралитет"

    def get_army_from_city(self, city_name):
        log_file = 'files/config/arms/all_arms.json'
        try:
            with open(log_file, 'r', encoding='utf-8') as file:
                army_data = json.load(file)
                for army_type in ['arkadia_in_city', 'celestia_in_city', 'halidon_in_city', 'giperion_in_city',
                                  'eteria_in_city']:  # Проверка всех разделов
                    if city_name in army_data.get(army_type, {}):
                        for entry in army_data[army_type][city_name]:
                            return entry.get('units', [])  # Возвращаем список юнитов
            print(f"Армия для города '{city_name}' не найдена.")
            return None
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Файл {log_file} не найден или пуст.")
            return None
        except Exception as e:
            print(f"Произошла ошибка при загрузке армии из города '{city_name}': {e}")
            return None

    def update_city_data(self, source_city_name):
        try:
            army_data = load_json_file(self.garrison)
            if not army_data:
                print("Не удалось загрузить данные гарнизонов.")
                return

            # Проверяем, есть ли исходный город в данных
            if source_city_name not in army_data or not army_data[source_city_name]:
                print(f"Гарнизон '{source_city_name}' не содержит данных или отсутствует.")
                return

            source_city_data = army_data[source_city_name]
            source_units = source_city_data[0].get("units", []) if len(source_city_data) > 0 else []

            # Проверяем, есть ли гарнизон в целевом городе
            if self.city_name in army_data and len(army_data[self.city_name]) > 0:
                destination_units = army_data[self.city_name][0].setdefault("units", [])

                # Объединяем юниты из двух городов
                for source_unit in source_units:
                    matching_unit = next(
                        (unit for unit in destination_units if unit["unit_name"] == source_unit["unit_name"]),
                        None
                    )
                    if matching_unit:
                        # Обновляем количество юнитов
                        matching_unit["unit_count"] += source_unit["unit_count"]
                    else:
                        # Добавляем новый тип юнита
                        destination_units.append(source_unit)
            else:
                # Если гарнизона нет, создаем его
                army_data[self.city_name] = [{"coordinates": str(self.city_coords), "units": source_units}]

            # Удаляем исходный город
            del army_data[source_city_name]

            # Сохраняем обновленные данные
            with open(self.garrison, 'w', encoding='utf-8') as file:
                json.dump(army_data, file, ensure_ascii=False, indent=4)

        except KeyError as e:
            print(f"Ошибка при обновлении данных о городе: '{e}' не найден.")
        except Exception as e:
            print(f"Ошибка при обновлении данных о городе: {e}")

    def strike_with_dbs(self, instance):
        # Получаем данные о городе из таблицы cities
        coords_str = f"[{self.city_coords[0]}, {self.city_coords[1]}]"
        self.cursor.execute("""
            SELECT name FROM cities 
            WHERE coordinates = ?
        """, (coords_str,))
        city_data = self.cursor.fetchone()

        if not city_data:
            print(f"Город с координатами {self.city_coords} не найден в базе данных")
            return

        city_name = city_data[0]

        # Вызываем функцию open_weapon_db_management из модуля army
        open_weapon_db_management(
            faction=self.player_fraction,  # Фракция
            army_cash=None,  # Боевой режим
            city_name_text=city_name,  # Название города
            coordinates_text=self.city_coords  # Координаты города
        )

        # Закрываем текущее окно
        self.dismiss()

    def close_popup(self):
        """
        Закрывает текущее всплывающее окно и освобождает ресурсы.
        """
        self.dismiss()  # Закрываем окно
        self.clear_widgets()  # Очищаем все виджеты