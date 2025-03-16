import json
import os
import re
import shutil
import sqlite3

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
from collections import defaultdict
from kivy.uix.image import Image as KivyImage  # Для отображения изображений в Kivy
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import fight

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
        self.fraction = kingdom
        self.city_name = ''
        self.city_coords = list(city_coords)
        self.size_hint = (0.8, 0.8)
        self.player_fraction = player_fraction
        self.file_path2 = None
        self.file_path1 = None
        self.garrison = transform_filename(f'files/config/manage_ii/{self.player_fraction}_in_city.json')

        # Загрузка данных о городах
        with open('files/config/cities.json', 'r', encoding='utf-8') as file:
            cities_data = json.load(file)["cities"]
            for city in cities_data:
                if city["coordinates"] == self.city_coords:
                    self.city_name = city["name"]
                    break

        self.title = f"Информация о поселении {self.city_name}"
        self.create_ui()

    def create_ui(self):
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Верхняя часть: Гарнизон и здания
        columns_layout = GridLayout(cols=2, spacing=20, size_hint_y=0.7)

        # Левая колонка: Гарнизон
        troops_column = BoxLayout(orientation='vertical', spacing=10)
        troops_column.add_widget(Label(text="Гарнизон", font_size='20sp', bold=True, size_hint_y=None, height=30))
        self.attacking_units_list = ScrollView(size_hint=(1, 1))
        self.attacking_units_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.attacking_units_box.bind(minimum_height=self.attacking_units_box.setter('height'))
        self.attacking_units_list.add_widget(self.attacking_units_box)
        troops_column.add_widget(self.attacking_units_list)
        columns_layout.add_widget(troops_column)

        # Правая колонка: Здания
        buildings_column = BoxLayout(orientation='vertical', spacing=10)
        buildings_column.add_widget(Label(text="Здания", font_size='20sp', bold=True, size_hint_y=None, height=30))
        self.buildings_list = ScrollView(size_hint=(1, 1))
        self.buildings_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.buildings_box.bind(minimum_height=self.buildings_box.setter('height'))
        self.buildings_list.add_widget(self.buildings_box)
        buildings_column.add_widget(self.buildings_list)
        columns_layout.add_widget(buildings_column)

        main_layout.add_widget(columns_layout)

        # Нижняя часть: Кнопки действий
        button_layout = GridLayout(cols=3, size_hint_y=None, height=50, spacing=10)

        # Кнопка "Ввести войска"
        send_troops_button = Button(text="Ввести войска", background_color=(0.6, 0.8, 0.6, 1))
        send_troops_button.bind(on_press=self.introduce_troops)
        button_layout.add_widget(send_troops_button)

        # Кнопка "Нанести удар ДБ оружием"
        strike_weapon_button = Button(text="Нанести удар ДБ оружием", background_color=(0.8, 0.6, 0.6, 1))
        strike_weapon_button.bind(on_press=self.strike_with_dbs)
        button_layout.add_widget(strike_weapon_button)

        # Кнопка "Разместить армию"
        place_army_button = Button(text="Разместить армию", background_color=(0.6, 0.6, 0.8, 1))
        place_army_button.bind(on_press=self.place_army)
        button_layout.add_widget(place_army_button)

        main_layout.add_widget(button_layout)

        # Кнопка "Закрыть"
        close_button = Button(text="Закрыть", size_hint_y=None, height=50, background_color=(0.8, 0.8, 0.8, 1))
        close_button.bind(on_press=self.dismiss)
        main_layout.add_widget(close_button)

        self.content = main_layout
        self.load_troops(self.fraction, self.city_coords)
        self.load_buildings()

    def load_troops(self, kingdom, city_coords):
        merge_army_and_ii_files()
        log_file = 'files/config/arms/all_arms.json'
        attacking_units = self.get_units(log_file, self.city_name)
        for unit in attacking_units:
            unit_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=70, spacing=5)
            unit_image = Image(source=unit['unit_image'], size_hint=(1, 0.7))
            unit_name_label = Label(
                text=f"{unit['unit_name']} (кол-во: {unit['unit_count']})",
                size_hint_y=None,
                height=30,
                color=(0.2, 0.2, 0.2, 1)
            )
            unit_layout.add_widget(unit_image)
            unit_layout.add_widget(unit_name_label)
            self.attacking_units_box.add_widget(unit_layout)

    def load_buildings(self):
        buildings = self.get_buildings()
        for building in buildings:
            label = Label(
                text=building,
                size_hint_y=None,
                height=30,
                color=(0.2, 0.2, 0.2, 1)
            )
            self.buildings_box.add_widget(label)

    def get_units(self, log_file, city_name):
        units = []
        try:
            with open(log_file, 'r', encoding='utf-8') as file:
                army_data = json.load(file)
                for army_type in ['arkadia_in_city', 'celestia_in_city', 'halidon_in_city', 'giperion_in_city',
                                  'eteria_in_city']:  # Проверка всех разделов
                    if city_name in army_data.get(army_type, {}):
                        for entry in army_data[army_type][city_name]:
                            for unit in entry.get('units', []):
                                units.append({
                                    'unit_image': unit['unit_image'],
                                    'unit_name': unit['unit_name'],
                                    'unit_count': unit['unit_count']
                                })
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Файл {log_file} не найден или пуст.")
        except Exception as e:
            print(f"Произошла ошибка при загрузке юнитов: {e}")
        return units

    def get_buildings(self):
        """Получает количество зданий в указанном городе из JSON-файла."""
        # Формируем путь к файлу зданий фракции
        path_to_buildings = transform_filename(f'files/config/buildings_in_city/{self.fraction}_buildings_city.json')

        # Инициализируем словарь для подсчета зданий
        buildings_count = defaultdict(int)

        # Проверяем, существует ли файл
        if os.path.exists(path_to_buildings):
            try:
                with open(path_to_buildings, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                # Проверяем, есть ли информация о здании для текущего города
                if self.city_name in data:
                    buildings_info = data[self.city_name].get('Здания', {})
                    for building_type, count in buildings_info.items():
                        buildings_count[building_type] = count

            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Ошибка при чтении файла {path_to_buildings}: {e}")

        # Формируем список с информацией о зданиях
        buildings = [f"{building}: {count}" for building, count in buildings_count.items()]

        # Если зданий нет, добавляем пустую строку
        if not buildings:
            buildings.append("")

        return buildings

    def introduce_troops(self, instance):
        # Открытие окна для выбора гарнизона
        garrison_selection_popup = Popup(title="Выберите гарнизон для ввода войск",
                                         size_hint=(0.8, 0.8))

        # Создание макета для выбора гарнизона
        garrison_selection_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Загружаем данные гарнизонов из файла
        with open(self.garrison, 'r', encoding='utf-8') as file:
            try:
                army_data = json.load(file)
            except json.JSONDecodeError:
                print("Файл army_in_city.json пустой или поврежден, загружаем пустые данные.")
                army_data = {}

        # Отображение гарнизонов с информацией о войсках
        for city_name, entries in army_data.items():
            for entry in entries:
                coordinates = entry.get("coordinates", "")
                units_info = "\n".join(
                    [f"{unit['unit_name']} (Кол-во: {unit['unit_count']})" for unit in entry.get("units", [])]
                )  # Информация о каждом типе войск

                # Создаем кнопку с именем гарнизона, координатами и составом войск
                garrison_button = Button(
                    text=f"{city_name} - Войска:\n{units_info}",
                    size_hint_y=None,
                    height=100
                )

                # Привязываем действие к кнопке, чтобы при нажатии вызвать метод передачи войск
                garrison_button.bind(
                    on_press=lambda btn, name=city_name: self.choose_garrison(name, garrison_selection_popup)
                )

                # Добавляем кнопку в макет
                garrison_selection_layout.add_widget(garrison_button)

        # Кнопка для закрытия окна
        close_button = Button(text="Закрыть", size_hint_y=None, height=50)
        close_button.bind(on_press=garrison_selection_popup.dismiss)
        garrison_selection_layout.add_widget(close_button)

        # Устанавливаем содержимое окна и открываем его
        garrison_selection_popup.content = garrison_selection_layout
        garrison_selection_popup.open()

    def place_army(self, instance):
        arms_file_path = 'files/config/arms/arms.json'
        try:
            with open(arms_file_path, 'r', encoding='utf-8') as file:
                arms_data = json.load(file)

            popup = Popup(title="Разместить армию", size_hint=(0.9, 0.9))
            main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

            table_layout = GridLayout(cols=5, spacing=10, size_hint_y=None)
            table_layout.bind(minimum_height=table_layout.setter('height'))

            base_font_size = 7
            screen_width, _ = Window.size
            scale_factor = screen_width / 360
            font_size = int(base_font_size * scale_factor)

            headers = ["Изображение", "Название", "Количество", "Статистика", "Действие"]
            for header in headers:
                label = Label(
                    text=header,
                    font_size=f'{font_size}sp',
                    bold=True,
                    size_hint_y=None,
                    height=40,
                    color=(1, 1, 1, 1)
                )
                table_layout.add_widget(label)

            base_image_width, base_image_height = 50, 50
            image_width = int(base_image_width * scale_factor)
            image_height = int(base_image_height * scale_factor)

            bg_color = (0.2, 0.2, 0.2, 1)  # Цвет окна интерфейса

            def update_rect(instance, value):
                if hasattr(instance, 'bg_rect'):
                    instance.bg_rect.pos = instance.pos
                    instance.bg_rect.size = instance.size

            for unit_key, unit_data in arms_data.items():
                image_container = BoxLayout(size_hint_y=None, height=image_height)
                unit_image = KivyImage(
                    source=unit_data["image"],
                    size_hint=(None, None),
                    size=(image_width, image_height)
                )
                image_container.add_widget(unit_image)
                table_layout.add_widget(image_container)

                name_label = Label(
                    text=unit_data["name"],
                    font_size=f'{font_size}sp',
                    size_hint_y=None,
                    height=60,
                    color=(1, 1, 1, 1)
                )
                with name_label.canvas.before:
                    Color(*bg_color)
                    name_label.bg_rect = Rectangle(pos=name_label.pos, size=name_label.size)
                name_label.bind(pos=update_rect, size=update_rect)
                table_layout.add_widget(name_label)

                count_label = Label(
                    text=str(unit_data["count"]),
                    font_size=f'{font_size}sp',
                    size_hint_y=None,
                    height=60,
                    color=(1, 1, 1, 1)
                )
                with count_label.canvas.before:
                    Color(*bg_color)
                    count_label.bg_rect = Rectangle(pos=count_label.pos, size=count_label.size)
                count_label.bind(pos=update_rect, size=update_rect)
                table_layout.add_widget(count_label)

                stats_text = "\n".join([f"{stat}: {value}" for stat, value in unit_data["stats"].items()])
                stats_label = Label(
                    text=stats_text,
                    font_size=f'{font_size}sp',
                    size_hint_y=None,
                    height=100,
                    color=(1, 1, 1, 1)
                )
                with stats_label.canvas.before:
                    Color(*bg_color)
                    stats_label.bg_rect = Rectangle(pos=stats_label.pos, size=stats_label.size)
                stats_label.bind(pos=update_rect, size=update_rect)
                table_layout.add_widget(stats_label)

                action_button = Button(
                    text="Добавить",
                    font_size=f'{font_size}sp',
                    size_hint_y=None,
                    height=40,
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
                height=40,
                background_color=(0.8, 0.8, 0.8, 1)
            )
            close_button.bind(on_press=popup.dismiss)
            main_layout.add_widget(close_button)

            popup.content = main_layout
            popup.open()

        except FileNotFoundError:
            print(f"Файл {arms_file_path} не найден.")
        except json.JSONDecodeError:
            print(f"Ошибка при декодировании JSON из файла {arms_file_path}.")
            self.show_warning_popup()
        except Exception as e:
            print(f"Произошла ошибка при загрузке данных о войсках: {e}")


    def add_to_garrison(self, unit, *args):
        """
        Проверяет наличие юнитов и добавляет выбранный тип войск в гарнизон.
        """
        # Создание всплывающего окна для выбора количества
        popup = Popup(title="Выберите количество", size_hint=(0.6, 0.4))
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Поле ввода количества
        input_label = Label(text=f"Введите количество {unit['name']} (доступно: {unit['count']})")
        count_input = TextInput(multiline=False, input_filter='int')  # Разрешаем только целые числа
        layout.add_widget(input_label)
        layout.add_widget(count_input)

        # Кнопки подтверждения и отмены
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        confirm_button = Button(text="Подтвердить", background_color=(0.6, 0.8, 0.6, 1))
        cancel_button = Button(text="Отмена", background_color=(0.8, 0.6, 0.6, 1))

        # Привязка действий к кнопкам
        confirm_button.bind(on_press=lambda btn: self.confirm_addition(unit, count_input.text, popup))
        cancel_button.bind(on_press=popup.dismiss)

        button_layout.add_widget(confirm_button)
        button_layout.add_widget(cancel_button)
        layout.add_widget(button_layout)

        popup.content = layout
        popup.open()

        # Перенос армии в файл зданий
        self.transfer_army_to_buildings_file(unit)

    def show_warning_popup(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text="Для размещения юнитов сначала надо нанять!")
        btn = Button(text="OK", size_hint=(1, 0.3))

        popup = Popup(title="Внимание!", content=layout, size_hint=(0.5, 0.3))
        btn.bind(on_release=popup.dismiss)

        layout.add_widget(label)
        layout.add_widget(btn)

        popup.open()

    def confirm_addition(self, unit, count_text, popup):
        """
        Подтверждает добавление войск в гарнизон после проверки введенного количества.
        """
        try:
            count = int(count_text)  # Преобразуем введенное значение в число
            if count <= 0:
                raise ValueError("Количество должно быть больше нуля.")
            if count > unit['count']:
                raise ValueError(f"Недостаточно войск. Доступно только {unit['count']}.")

            # Обновляем файл гарнизона
            self.update_garrison(unit, count)

            # Закрываем всплывающее окно
            popup.dismiss()
            print(f"Добавлено в гарнизон: {unit['name']} (количество: {count})")

        except ValueError as e:
            # Выводим сообщение об ошибке
            error_popup = Popup(title="Ошибка", size_hint=(0.6, 0.4), auto_dismiss=True)
            error_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            error_label = Label(text=str(e))
            close_button = Button(text="Закрыть", size_hint_y=None, height=50)
            close_button.bind(on_press=error_popup.dismiss)
            error_layout.add_widget(error_label)
            error_layout.add_widget(close_button)
            error_popup.content = error_layout
            error_popup.open()

    def update_garrison(self, unit, count):
        """
        Обновляет файл гарнизона, добавляя или изменяя данные о войсках.
        """

        try:
            # Проверяем, существует ли файл
            if not os.path.exists(self.garrison) or os.path.getsize(self.garrison) == 0:
                print(f"Файл {self.garrison} не найден или пустой. Создаем новый файл.")
                with open(self.garrison, 'w', encoding='utf-8') as file:
                    json.dump({}, file, ensure_ascii=False, indent=4)

            # Загружаем текущие данные гарнизона
            with open(self.garrison, 'r', encoding='utf-8') as file:
                try:
                    garrison_data = json.load(file)
                except json.JSONDecodeError:
                    print(f"Файл {self.garrison} пустой или содержит некорректные данные. Используем пустой словарь.")
                    garrison_data = {}

            # Проверяем, есть ли уже войска в городе
            if self.city_name not in garrison_data:
                garrison_data[self.city_name] = [
                    {
                        "coordinates": self.city_coords,
                        "units": []
                    }
                ]

            units = garrison_data[self.city_name][0]["units"]

            # Ищем совпадающий тип войск
            matching_unit = next((u for u in units if u["unit_name"] == unit['name']), None)
            if matching_unit:
                # Если войска уже есть, увеличиваем их количество
                matching_unit["unit_count"] += count
            else:
                # Если войск нет, добавляем новый тип
                units.append({
                    "unit_image": unit['image'],
                    "unit_name": unit['name'],
                    "unit_count": count,
                    "units_stats": unit['stats']
                })

            # Сохраняем обновленные данные в файл
            with open(self.garrison, 'w', encoding='utf-8') as file:
                json.dump(garrison_data, file, ensure_ascii=False, indent=4)

            print(f"Добавлено в гарнизон: {unit['name']} (количество: {count})")

        except Exception as e:
            print(f"Произошла ошибка при обновлении гарнизона: {e}")

    def transfer_army_to_buildings_file(self, selected_units):
        """
        Переносит данные о войсках из arms.json в файл buildings_in_city/{fraction}_buildings_city.json
        и модифицирует оставшиеся данные в arms.json.
        :param selected_units: Словарь {unit_key: count} с выбранными юнитами.
        """
        arms_file_path = 'files/config/arms/arms.json'
        buildings_file_path = transform_filename(f'files/config/buildings_in_city/{self.fraction}_buildings_city.json')

        try:
            # Загружаем текущие войска
            with open(arms_file_path, 'r', encoding='utf-8') as file:
                arms_data = json.load(file)

            # Загружаем или создаем файл с войсками в городе
            if not os.path.exists(buildings_file_path) or os.path.getsize(buildings_file_path) == 0:
                initial_data = {}
            else:
                with open(buildings_file_path, 'r', encoding='utf-8') as file:
                    initial_data = json.load(file)

            # Структура для войск города
            if self.city_name not in initial_data:
                initial_data[self.city_name] = {"coordinates": self.city_coords, "units": []}

            city_units = initial_data[self.city_name]["units"]

            # Обрабатываем выбранные войска
            for unit_key, taken_count in selected_units.items():
                if unit_key in arms_data:
                    unit_info = arms_data[unit_key]
                    old_count = unit_info["count"]

                    if taken_count > old_count:
                        print(f"Ошибка: нельзя взять больше, чем есть. {unit_key}: {taken_count} > {old_count}")
                        continue  # Пропускаем обработку этого юнита

                    # Пересчет характеристик для нового отряда
                    new_unit = {
                        "unit_image": unit_info["image"],
                        "unit_name": unit_info["name"],
                        "unit_count": taken_count,
                        "units_stats": {stat: round(value * (taken_count / old_count), 2) for stat, value in
                                        unit_info["stats"].items()}
                    }

                    # Добавляем войска в гарнизон
                    existing_city_unit = next((u for u in city_units if u["unit_name"] == unit_info["name"]), None)
                    if existing_city_unit:
                        existing_city_unit["unit_count"] += taken_count
                    else:
                        city_units.append(new_unit)

                    # Обновляем оставшиеся войска в arms.json
                    remaining_count = old_count - taken_count
                    if remaining_count > 0:
                        arms_data[unit_key]["count"] = remaining_count
                        arms_data[unit_key]["stats"] = {stat: round(value * (remaining_count / old_count), 2) for
                                                        stat, value in unit_info["stats"].items()}
                    else:
                        del arms_data[unit_key]  # Полностью убираем юнита, если его больше нет

            # Сохраняем обновленные данные в файлы
            with open(buildings_file_path, 'w', encoding='utf-8') as file:
                json.dump(initial_data, file, ensure_ascii=False, indent=4)

            with open(arms_file_path, 'w', encoding='utf-8') as file:
                json.dump(arms_data, file, ensure_ascii=False, indent=4)

            print(f"Данные успешно перенесены в {buildings_file_path}, оставшиеся войска обновлены в {arms_file_path}")

        except FileNotFoundError:
            print(f"Файл {arms_file_path} не найден.")
        except json.JSONDecodeError:
            print(f"Ошибка при чтении JSON из {arms_file_path}.")
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
        path_to_army_strike = transform_filename(f'files/config/manage_ii/{self.fraction}_in_city.json')
        data = {
            "city_name": self.city_name,
            "coordinates": self.city_coords,
            "path_to_army": path_to_army_strike
        }
        with open('files/config/arms/coordinates_weapons.json', 'w', encoding='utf-8') as file:
            json.dump(data, file)
        print(f"Данные о городе '{self.city_name}' и его координатах {self.city_coords} сохранены в файл.")

        # Закрытие окна после выполнения действия
        self.dismiss()
