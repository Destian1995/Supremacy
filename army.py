# army.py
from kivy.animation import Animation
from kivy.graphics import Line, Rectangle
from kivy.clock import Clock
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
import threading
import strike
import json
import os
import time

translation_dict = {
    "Аркадия": "arkadia",
    "Селестия": "celestia",
    "Этерия": "eteria",
    "Хиперион": "giperion",
    "Халидон": "halidon",
}


def transform_filename(file_path):
    path_parts = file_path.split('/')
    for i, part in enumerate(path_parts):
        for ru_name, en_name in translation_dict.items():
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)
    return '/'.join(path_parts)

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


class ArmyCash:
    def __init__(self, faction):
        self.faction = faction
        self.cash_resources = 'files/config/resources/cash.json'
        self.units_file = 'files/config/arms/arms.json'  # Путь к файлу юнитов
        self.resources = self.load_resources()

    def load_resources(self):
        """Загружает состояние ресурсов из файла."""
        if os.path.exists(self.cash_resources):
            with open(self.cash_resources, 'r') as file:
                try:
                    resources = json.load(file)  # Читаем данные один раз
                    print(resources)  # Печатаем загруженные ресурсы
                    return resources  # Возвращаем загруженные данные
                except json.JSONDecodeError:
                    print("Ошибка при загрузке ресурсов: файл пуст или повреждён.")

    def hire_unit(self, unit_name, unit_cost, quantity, image_unit, unit_stats):
        """Нанимает юнита, если ресурсов достаточно."""
        crowns, workers = unit_cost  # Извлекаем стоимость юнита
        required_crowns = int(crowns) * int(quantity)  # Рассчитываем общее количество необходимых крон
        required_workers = int(workers) * int(quantity)  # Рассчитываем общее количество необходимых рабочих

        # Умножаем характеристики на количество юнитов, исключая "Индекс эффективности"
        scaled_stats = {}
        for stat_name, value in unit_stats.items():
            if stat_name == "Класс юнита":
                scaled_stats[stat_name] = value  # Сохраняем исходное значение
            else:
                scaled_stats[stat_name] = value * quantity

        # Проверяем, хватает ли ресурсов
        if self.resources['Кроны'] < required_crowns or self.resources['Рабочие'] < required_workers:
            self.show_message("Ошибка найма",
                              f"Нанять юнитов невозможно: недостаточно ресурсов.\nНеобходимые: {required_crowns} крон и {required_workers} рабочих.")
            return False  # Не хватает ресурсов для найма

        # Если ресурсов достаточно, обновляем их
        self.resources['Кроны'] -= required_crowns
        self.resources['Рабочие'] -= required_workers
        with open(self.cash_resources, 'w') as file:
            json.dump(self.resources, file, ensure_ascii=False, indent=4)

        # Чтение существующих юнитов из файла
        units_data = {}
        if os.path.exists(self.units_file):
            with open(self.units_file, 'r', encoding='UTF-8') as file:
                try:
                    units_data = json.load(file)
                except json.JSONDecodeError:
                    units_data = {}

        # Обновление или добавление юнита
        if image_unit in units_data:
            units_data[image_unit]['count'] += quantity  # Увеличиваем количество юнитов
            # Обновляем характеристики, суммируя все кроме "Индекса эффективности"
            for stat_name, value in scaled_stats.items():
                if stat_name == "Класс юнита":
                    continue  # Пропускаем обновление для "Индекса эффективности"
                if stat_name in units_data[image_unit]['stats']:
                    units_data[image_unit]['stats'][stat_name] += value
                else:
                    units_data[image_unit]['stats'][stat_name] = value
        else:
            units_data[image_unit] = {
                'name': unit_name,
                'count': quantity,
                'image': image_unit,
                'stats': scaled_stats
            }

        # Запись обновлённых данных о юнитах в файл
        with open(self.units_file, 'w', encoding='UTF-8') as file:
            json.dump(units_data, file)

        self.show_message("Успех",
                          f"Юнит {unit_name} нанят!\nПотрачено: {required_crowns} крон и {required_workers} рабочих.")
        return True  # Возвращаем успех

    def show_message(self, title, message):
        layout = BoxLayout(orientation='vertical', padding=10)
        label = Label(text=message, halign='center')
        button = Button(text="OK", size_hint=(1, 0.3))

        # Закрываем окно при нажатии на кнопку
        popup = Popup(title=title, content=layout, size_hint=(0.75, 0.5), auto_dismiss=False)
        button.bind(on_press=popup.dismiss)

        layout.add_widget(label)
        layout.add_widget(button)

        popup.open()


def load_unit_data(english_faction):
    """Загружает данные о юнитах для выбранной фракции из JSON-файла"""
    file_path = f"files/config/units/{english_faction}.json"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Файл с юнитами для фракции {english_faction} не найден.")
        return {}


def show_unit_selection(faction, army_hire):
    """Показать окно выбора юнитов для найма"""
    english_faction = translation_dict.get(faction, faction)
    unit_data = load_unit_data(english_faction)

    unit_popup = Popup(title="Выбор юнитов", size_hint=(0.9, 0.9), background_color=(0.1, 0.1, 0.1, 1))

    scroll_view = ScrollView(size_hint=(0.6, 1))

    unit_layout = GridLayout(cols=2, padding=15, spacing=15, size_hint_y=None)
    unit_layout.bind(minimum_height=unit_layout.setter('height'))

    # Используем foreground_color вместо color
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
                                        input_box=quantity_input, img=unit_info['image'], stats=unit_info['stats']:
        broadcast_units(name, cost, input_box, army_hire, img, stats))

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

    try:
        # Проверяем, не пустое ли поле
        if not quantity_text:
            print("Введите количество юнитов.")
            return

        quantity = int(quantity_text)

        if quantity <= 0:
            print("Количество должно быть больше нуля.")
            return

        # Передача ссылки на изображение юнита в функцию hire_unit
        if army_hire.hire_unit(unit_name, unit_cost, quantity, image, unit_stats):
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


def switch_to_economy(faction, game_area):
    import economic  # Импортируем здесь, чтобы избежать циклического импорта
    game_area.clear_widgets()
    economic.start_economy_mode(faction, game_area)


def switch_to_army(faction, game_area):
    import army  # Импортируем здесь, чтобы избежать циклического импорта
    game_area.clear_widgets()
    army.start_army_mode(faction, game_area)


def switch_to_politics(faction, game_area):
    import politic  # Импортируем здесь, чтобы избежать циклического импорта
    game_area.clear_widgets()
    politic.start_politic_mode(faction, game_area)


#--------------------


class GeneralStaff:
    def __init__(self, faction, cities):
        self.garrison_file = None
        self.faction = faction
        self.cities = cities
        self.units = self.load_garrison_data()

    def load_garrison_data(self):
        """Загружает данные о гарнизонах из файла."""
        self.garrison_file = transform_filename(f'files/config/manage_ii/{self.faction}_in_city.json')
        if os.path.exists(self.garrison_file):
            try:
                with open(self.garrison_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print(f"Ошибка загрузки данных из {self.garrison_file}. Файл пуст или содержит некорректные данные.")
                return {}
        else:
            print(f"Файл {self.garrison_file} не найден. Используем пустой набор данных.")
            return {}

    def save_garrison_data(self):
        """Сохраняет текущие данные о гарнизонах в файл."""
        with open(self.garrison_file, 'w', encoding='utf-8') as file:
            json.dump(self.units, file, ensure_ascii=False, indent=4)


# Функция для загрузки информации о юнитах
def load_units_data():
    """Загружает данные юнитов из файла arms.json."""
    units_data = {}
    units_file_path = 'files/config/arms/arms.json'  # Путь к файлу юнитов

    if os.path.exists(units_file_path):
        try:
            with open(units_file_path, 'r', encoding='utf-8') as file:
                units_data = json.load(file)
                print('Данные о загруженных юнитах:', units_data)
        except json.JSONDecodeError:
            print(f"Ошибка загрузки данных из {units_file_path}. Файл пуст или содержит некорректные данные.")
            units_data = {}
    else:
        print(f"Файл {units_file_path} не найден. Используем пустой набор данных.")

    return units_data


class Separator(Widget):
    def __init__(self, **kwargs):
        super(Separator, self).__init__(**kwargs)
        with self.canvas:
            Color(0, 0, 0, 0.5)  # Черная линия с прозрачностью 50%
            self.line = Line(points=[self.x, self.center_y, self.width, self.center_y], width=1.5)
        # Привязываем метод для обновления при изменении размера виджета
        self.bind(size=self.update_line, pos=self.update_line)

    def update_line(self, *args):
        # Обновляем точки линии в соответствии с текущими размерами Separator
        self.line.points = [self.x, self.center_y, self.right, self.center_y]


# Основная функция для отображения интерфейса генштаба
def show_army_headquarters(faction, cities):
    units_data = load_units_data()
    load_units_fraction_city = transform_filename(f'files/config/manage_ii/{faction}_in_city.json')
    unit_popup = Popup(title=f"Генштаб - {faction}", size_hint=(0.9, 0.9))
    unit_popup.background_color = (0, 0, 0, 0.8)  # Сделаем фон прозрачным

    tab_panel = TabbedPanel(do_default_tab=False, size_hint=(1, 1))

    # Вкладка не расквартированных юнитов
    unassigned_tab = TabbedPanelItem(text="Штаб", size_hint=(1, 1))
    unassigned_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
    unassigned_layout.padding = [10, 10, 10, 10]

    # Создаем ScrollView для отображения юнитов
    scroll_view = ScrollView(size_hint=(1, 1))
    unassigned_content = GridLayout(cols=1, padding=(10, 10, 10, 10), size_hint_y=None)
    unassigned_content.bind(minimum_height=unassigned_content.setter('height'))
    scroll_view.add_widget(unassigned_content)

    # Цикл по юнитам для отображения их изображений и численности
    for image, unit_info in units_data.items():
        unit_count = unit_info.get('count', 0)

        # Создаем горизонтальный контейнер для изображения и подписи
        unit_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=120, spacing=10)

        # Добавляем изображение юнита
        if image and os.path.exists(image):
            unit_image = Image(source=image, size_hint=(None, None), width=100, height=100)
            unit_box.add_widget(unit_image)
        else:
            unit_box.add_widget(Label(text="Изображение не найдено", color=(1, 0, 0, 1)))  # Красный цвет для ошибок

        # Подпись с количеством юнитов
        unit_label = Label(text=f"       {unit_info['name']}: {unit_count} юнитов", font_size=16, color=(1, 1, 1, 1), size_hint=(None, None), width=150)
        unit_box.add_widget(unit_label)

        # Добавляем блок юнита в содержимое ScrollView
        unassigned_content.add_widget(unit_box)

    unassigned_layout.add_widget(scroll_view)

    # Кнопки для управления расквартированием
    button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)

    # Стильные кнопки
    select_unit_button = Button(text='Выбрать юнит', size_hint=(1, None), height=50)
    select_unit_button.background_color = (0.2, 0.6, 0.8, 1)  # Голубой фон
    select_unit_button.font_size = 18
    select_unit_button.bind(on_release=lambda instance: open_unit_dropdown(select_unit_button))
    button_layout.add_widget(select_unit_button)

    select_city_button = Button(text='Выбрать город', size_hint=(1, None), height=50)
    select_city_button.background_color = (0.8, 0.8, 0.2, 1)  # Желтый фон
    select_city_button.font_size = 18
    select_city_button.bind(on_release=lambda instance: open_city_dropdown(select_city_button, cities))
    button_layout.add_widget(select_city_button)

    unit_count_input = TextInput(hint_text='Количество юнитов', size_hint=(0.5, None), height=50, multiline=False)
    unit_count_input.background_color = (0.1, 0.1, 0.1, 0.7)  # Темный фон для поля ввода
    unit_count_input.foreground_color = (1, 1, 1, 1)  # Белый текст
    button_layout.add_widget(unit_count_input)

    # Кнопка "Разместить"
    garrison_button = Button(text='Разместить', size_hint=(1, None), height=50)
    garrison_button.background_color = (0.1, 0.8, 0.1, 1)  # Зеленый фон
    garrison_button.font_size = 18
    garrison_button.bind(on_release=lambda instance: garrison_units(
        select_city_button.text, unit_count_input.text, select_unit_button.text, unassigned_layout, assigned_layout,
        cities, load_units_fraction_city))
    button_layout.add_widget(garrison_button)

    unassigned_layout.add_widget(button_layout)
    unassigned_tab.add_widget(unassigned_layout)
    tab_panel.add_widget(unassigned_tab)

    # Вкладка расквартированных юнитов
    assigned_tab = TabbedPanelItem(text="Города", size_hint=(1, 1))
    assigned_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
    assigned_tab.add_widget(assigned_layout)

    # Загружаем данные для таблицы гарнизонов
    update_assigned_units_tab(assigned_layout, load_units_fraction_city)

    tab_panel.add_widget(assigned_tab)
    unit_popup.content = tab_panel
    unit_popup.open()




def garrison_units(city_name, unit_count_str, unit_name, unassigned_layout, assigned_layout, cities, load_units_fraction_city):
    """Обработка расквартирования юнитов и обновление данных о наличии."""
    try:
        units_data = load_units_data()
        print("Данные в units_data:", units_data)

        unit_name = unit_name
        print(f"Проверяем юнит по имени: '{unit_name}'")

        # Поиск данных о юните через значения словаря
        unit_data = next((data for key, data in units_data.items() if data.get("name") == unit_name), None)

        if not unit_data:
            print(f"Юнит с именем {unit_name} не найден.")
            return

        unit_count = int(unit_count_str.strip())
        available_count = unit_data.get("count", 0)
        unit_name = unit_data.get("name", "Неизвестный юнит")

        if unit_count > available_count:
            print(f"Недостаточно юнитов. Доступно только {available_count} единиц.")
            return

        # Обновление данных юнитов
        remaining_count = available_count - unit_count
        if remaining_count > 0:
            unit_data["count"] = remaining_count
        else:
            # Удаление юнита
            unit_key = next((key for key, data in units_data.items() if data.get("name") == unit_name), None)
            if unit_key:
                del units_data[unit_key]
            else:
                print(f"Ошибка: Юнит с именем {unit_name} не найден в данных для удаления.")

        save_units_data(units_data)

        # Загрузка данных о городах
        with open('files/config/cities.json', 'r', encoding='UTF-8') as f:
            cities_data = json.load(f)

        city_coords = next((city['coordinates'] for city in cities_data['cities']
                            if city['name'].strip() == city_name.strip()), None)

        if city_coords is None:
            print(f"Город '{city_name}' не найден в данных.")
            return

        unit_image = unit_data.get("image")
        unit_stats = unit_data.get("stats")
        print(f"Запись в город {city_name}: {unit_image}, {unit_name}, {unit_count}, {unit_stats}")
        save_army_in_city(city_name, city_coords, unit_image, unit_name, unit_count, unit_stats)
        update_assigned_units_tab(assigned_layout, load_units_fraction_city)

        # Пересоздание интерфейса нерасквартированных юнитов
        unassigned_layout.clear_widgets()

        # Создаем ScrollView
        scroll_view = ScrollView(size_hint=(1, 1))
        unassigned_content = GridLayout(cols=1, padding=(10, 10, 10, 10),
                                        size_hint_y=None)  # Задаем 1 колонку как в show_army_headquarters
        unassigned_content.bind(minimum_height=unassigned_content.setter('height'))
        scroll_view.add_widget(unassigned_content)

        # Создаем интерфейс для юнитов
        for image, unit_info in units_data.items():
            unit_count = unit_info.get('count', 0)
            unit_name = unit_info.get('name', "Безымянный юнит")

            # Создаем контейнер для изображения и подписи
            unit_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=120,
                                 spacing=10)  # Высота и отступы как в show_army_headquarters

            # Изображение юнита
            if image and os.path.exists(image):
                unit_image = Image(source=image, size_hint=(None, None), width=100,
                                   height=100)  # Размер изображения одинаковый
                unit_box.add_widget(unit_image)
            else:
                unit_box.add_widget(Label(
                    text="Изображение не найдено",
                    color=(1, 0, 0, 1),
                    font_size=14,
                    halign="center"
                ))

            # Подпись с количеством юнитов
            unit_label = Label(
                text=f"  {unit_name}: {unit_count} юнитов",
                font_size=16,
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height=50,
                halign="left",
                valign="middle"
            )
            unit_label.bind(size=lambda widget, _: setattr(widget, 'text_size', widget.size))
            unit_box.add_widget(unit_label)

            # Добавляем блок юнита в содержимое
            unassigned_content.add_widget(unit_box)

        # Добавляем ScrollView с юнитами в layout
        unassigned_layout.add_widget(scroll_view)

        # Кнопки для управления расквартированием
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)

        # Стильные кнопки
        select_unit_button = Button(text='Выбрать юнит', size_hint=(1, None), height=50)
        select_unit_button.background_color = (0.2, 0.6, 0.8, 1)  # Голубой фон
        select_unit_button.font_size = 18
        select_unit_button.bind(on_release=lambda instance: open_unit_dropdown(select_unit_button))
        button_layout.add_widget(select_unit_button)

        select_city_button = Button(text='Выбрать город', size_hint=(1, None), height=50)
        select_city_button.background_color = (0.8, 0.8, 0.2, 1)  # Желтый фон
        select_city_button.font_size = 18
        select_city_button.bind(on_release=lambda instance: open_city_dropdown(select_city_button, cities))
        button_layout.add_widget(select_city_button)

        unit_count_input = TextInput(hint_text='Количество юнитов', size_hint=(0.5, None), height=50, multiline=False)
        unit_count_input.background_color = (0.1, 0.1, 0.1, 0.7)  # Темный фон для поля ввода
        unit_count_input.foreground_color = (1, 1, 1, 1)  # Белый текст
        button_layout.add_widget(unit_count_input)

        # Кнопка "Разместить"
        garrison_button = Button(text='Разместить', size_hint=(1, None), height=50)
        garrison_button.background_color = (0.1, 0.8, 0.1, 1)  # Зеленый фон
        garrison_button.font_size = 18
        garrison_button.bind(on_release=lambda instance: garrison_units(
            select_city_button.text, unit_count_input.text, select_unit_button.text, unassigned_layout, assigned_layout,
            cities, load_units_fraction_city))
        button_layout.add_widget(garrison_button)

        unassigned_layout.add_widget(button_layout)

        # Вкладка расквартированных юнитов
        assigned_tab = TabbedPanelItem(text="Города", size_hint=(1, 1))
        assigned_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
        assigned_tab.add_widget(assigned_layout)

        # Загружаем данные для таблицы гарнизонов
        update_assigned_units_tab(assigned_layout, load_units_fraction_city)

        print(f"Расквартировано {unit_count} юнитов {unit_name} в городе: {city_name}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")




def update_assigned_units_tab(assigned_layout, load_units_fraction_city):
    assigned_layout.clear_widgets()  # Очищаем виджет

    # Создаем ScrollView для таблицы
    table_scroll_view = ScrollView(size_hint=(1, None), height=420)
    table_layout = GridLayout(cols=2, size_hint_y=None)
    table_layout.bind(minimum_height=table_layout.setter('height'))

    # Добавление заголовков
    table_layout.add_widget(Label(text="Город", bold=True, size_hint_y=None, height=40))
    table_layout.add_widget(Label(text="Состав гарнизона", bold=True, size_hint_y=None, height=40))

    army_data = load_assigned_units_data(load_units_fraction_city)
    # Заполнение таблицы данными
    for city_name, garrisons in army_data.items():
        for garrison in garrisons:
            city_label = Label(text=city_name, size_hint_y=None, height=30)
            table_layout.add_widget(city_label)

            unit_layout = BoxLayout(orientation='vertical', size_hint_y=None)
            unit_layout.bind(minimum_height=unit_layout.setter('height'))

            for unit in garrison['units']:
                unit_image = unit['unit_image']
                unit_name = unit['unit_name']
                unit_count = unit['unit_count']

                unit_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
                if os.path.exists(unit_image):
                    unit_img = Image(source=unit_image, size_hint=(None, None), size=(50, 50))
                    unit_box.add_widget(unit_img)
                else:
                    unit_box.add_widget(Label(text="Изображение не найдено", size_hint=(None, None), size=(50, 50)))

                # Установите size_hint_x для правильного выравнивания
                unit_name_label = Label(text=f"{unit_name}: {unit_count}", size_hint_x=1)
                unit_box.add_widget(unit_name_label)
                unit_layout.add_widget(unit_box)

            table_layout.add_widget(unit_layout)

        # Добавляем отступ между городами
        table_layout.add_widget(Label(size_hint_y=None, height=5))
        table_layout.add_widget(Label(size_hint_y=None, height=5))

    table_scroll_view.add_widget(table_layout)
    assigned_layout.add_widget(table_scroll_view)


def load_assigned_units_data(army_file_path):
    """Загружает данные о расквартированных юнитах из файла ."""
    global army_data

    if os.path.exists(army_file_path):
        try:
            with open(army_file_path, 'r', encoding='utf-8') as file:
                army_data = json.load(file)
                print('Данные о расквартированных юнитах:', army_data)
        except json.JSONDecodeError:
            print(f"Ошибка загрузки данных из {army_file_path}. Файл пуст или содержит некорректные данные.")
            army_data = {}
    else:
        print(f"Файл {army_file_path} не найден. Используем пустой набор данных.")

    return army_data


def open_city_dropdown(button, cities):
    dropdown = DropDown()
    for city in cities:
        btn = Button(text=city['name'], size_hint_y=None, height=44)
        btn.bind(on_release=lambda btn: dropdown.select(btn.text))
        dropdown.add_widget(btn)

    button.bind(on_release=dropdown.open)
    dropdown.bind(on_select=lambda instance, x: setattr(button, 'text', x))


def open_unit_dropdown(button):
    dropdown = DropDown()
    units_data = load_units_data()

    for image_path, unit_info in units_data.items():
        unit_name = unit_info['name']
        btn = Button(text=unit_name, size_hint_y=None, height=44)

        # Используем параметр по умолчанию для правильного захвата переменной
        btn.bind(on_release=lambda btn, name=unit_name, path=image_path: (
            dropdown.select(path),
            setattr(button, 'text', name)  # Устанавливаем текст кнопки как имя юнита
        ))

        dropdown.add_widget(btn)

    button.bind(on_release=dropdown.open)


# Загрузка данных о юнитах из файла
def save_units_data(units_data):
    units_file_path = 'files/config/arms/arms.json'
    with open(units_file_path, 'w', encoding='utf-8') as file:
        json.dump(units_data, file, ensure_ascii=False, indent=4)


# Сохранение данных о расквартированных юнитах в файле
def save_army_in_city(city_name, city_coords, unit_image, unit_name, unit_count, unit_stats):
    fraction = get_faction_of_city(city_name)
    army_in_city_file = transform_filename(f'files/config/manage_ii/{fraction}_in_city.json')

    # Проверка существования файла
    if os.path.exists(army_in_city_file):
        with open(army_in_city_file, 'r', encoding='utf-8') as file:
            try:
                army_data = json.load(file)
                print(f"Содержимое файла до обновления: {army_data}")  # Логируем текущее содержимое
            except json.JSONDecodeError:
                print(f"Ошибка при чтении {army_in_city_file}. Файл может быть пуст или повреждён.")
                army_data = {}  # Если файл не читается, инициализируем пустой словарь
    else:
        army_data = {}  # Если файла не существует, инициализируем пустой словарь

    if city_name not in army_data:
        army_data[city_name] = []

    # Проверка на наличие существующих координат
    coords_exists = False
    for army_unit in army_data[city_name]:
        if army_unit['coordinates'] == city_coords:
            coords_exists = True
            # Проверка на наличие юнита с тем же именем
            unit_exists = False
            for unit in army_unit.get('units', []):
                if unit['unit_name'] == unit_name:
                    unit['unit_count'] += unit_count  # Увеличиваем количество
                    unit_exists = True
                    break

            if not unit_exists:
                # Если юнит с таким именем не найден, добавляем новый юнит в текущие координаты
                army_unit['units'].append({
                    'unit_image': unit_image,
                    'unit_name': unit_name,
                    'unit_count': unit_count,
                    'units_stats': unit_stats
                })
            break

    if not coords_exists:
        # Если координаты не найдены, добавляем новую запись с юнитами
        army_data[city_name].append({
            'coordinates': city_coords,
            'units': [{
                'unit_image': unit_image,
                'unit_name': unit_name,
                'unit_count': unit_count,
                'units_stats': unit_stats
            }]
        })

    with open(army_in_city_file, 'w', encoding='utf-8') as file:
        json.dump(army_data, file, ensure_ascii=False, indent=4)


#--------------------------------
class WeaponCash:
    def __init__(self, faction):
        self.faction = faction
        self.cash_resources = 'files/config/resources/cash.json'
        self.units_file = 'files/config/arms/weapons.json'  # Путь к файлу юнитов
        self.resources = self.load_resources()

    def load_resources(self):
        """Загружает состояние ресурсов из файла."""
        if os.path.exists(self.cash_resources):
            with open(self.cash_resources, 'r') as file:
                try:
                    resources = json.load(file)
                    print(resources)  # Печатаем загруженные ресурсы
                    return resources
                except json.JSONDecodeError:
                    print("Ошибка при загрузке ресурсов: файл пуст или повреждён.")

    def hire_unit(self, unit_name, unit_cost, quantity, weapon_name, koef=0):
        """Нанимает юнита, если ресурсов достаточно, и обновляет данные о них."""
        crowns, workers = unit_cost  # Извлекаем стоимость юнита
        required_crowns = int(crowns) * int(quantity)  # Рассчитываем общее количество необходимых крон
        required_workers = int(workers) * int(quantity)  # Рассчитываем общее количество необходимых рабочих

        # Проверяем, хватает ли ресурсов
        if self.resources['Кроны'] < required_crowns or self.resources['Рабочие'] < required_workers:
            return False  # Не хватает ресурсов для найма

        # Если ресурсов достаточно, обновляем их
        self.resources['Кроны'] -= required_crowns
        self.resources['Рабочие'] -= required_workers
        with open(self.cash_resources, 'w') as file:
            json.dump(self.resources, file, ensure_ascii=False, indent=4)  # Запись с индентацией для удобства

        # Загружаем данные о юнитах
        units_data = {}
        if os.path.exists(self.units_file):
            with open(self.units_file, 'r', encoding='UTF-8') as file:
                try:
                    units_data = json.load(file)
                except json.JSONDecodeError:
                    units_data = {}

        # Загружаем базовые данные об оружии
        weapon_base_data = get_weapons(self.faction)  # Функция для получения исходных данных об оружии

        # Вычисление all_damage на основе урона из исходных данных
        all_damage = 0
        if weapon_name in weapon_base_data:
            base_damage = weapon_base_data[weapon_name]['stats']['Вероятный Урон']
            all_damage = base_damage * quantity  # Общий урон с учетом количества юнитов

        # Обновляем или добавляем юнита с дополнительными параметрами
        if weapon_name in units_data:
            units_data[weapon_name]['count'] += quantity
        else:
            units_data[weapon_name] = {
                'name': unit_name,
                'count': quantity,
                'koef': koef,  # Сохранение коэффициента преодоления ПВО
                'all_damage': all_damage  # Сохранение общего урона
            }

        # Запись обновлённых данных о юнитах в файл
        with open(self.units_file, 'w', encoding='UTF-8') as file:
            json.dump(units_data, file, ensure_ascii=False, indent=4)

        return True  # Возвращаем успех



# Функция для загрузки данных юнитов (оружия) из файла
def load_weapon_data():
    file_path = "files/config/arms/weapons.json"
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден.")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")
        return {}
    except Exception as e:
        print(f"Произошла ошибка при загрузке файла: {e}")
        return {}


# Функция для сохранения данных юнитов
def save_weapon_data(weapon_data):
    with open("files/config/arms/weapons.json", "w", encoding="utf-8") as f:
        json.dump(weapon_data, f, ensure_ascii=False, indent=4)


# Функция для загрузки и очистки данных из файла
def load_and_clear_coordinates_data():
    file_path = "files/config/arms/coordinates_weapons.json"
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Проверяем структуру данных
        if not isinstance(data, dict) or 'city_name' not in data or 'coordinates' not in data or 'path_to_army' not in data:
            return {}

        # Очистка данных в файле
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)

        return data
    except json.JSONDecodeError:
        print("Файл координат для оружия пуст")
        return {}
    except Exception as e:
        print(f"Ошибка: {e}")
        return {}


def check_and_open_weapon_management(faction, army_cash):
    def thread_function():
        while True:  # Бесконечный цикл
            coordinates_data = load_and_clear_coordinates_data()
            if coordinates_data:
                city_name_text = coordinates_data.get('city_name', '')
                coordinates_text = coordinates_data.get('coordinates', '')
                path_to_army = coordinates_data.get('path_to_army', '')

                # Запланировать выполнение функции в основном потоке
                Clock.schedule_once(
                    lambda dt: open_weapon_db_management(faction, army_cash, city_name_text, coordinates_text, path_to_army))

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

    global current_weapon_management_popup, current_weapon_selection_popup

    # Используем FloatLayout для оптимизации интерфейса
    layout = FloatLayout()

    # Логика загрузки изображения фракции
    faction_image_path = transform_filename(f'files/army/{faction}/stations_weapons.jpg')  # Путь к изображению фракции
    faction_image = Image(source=faction_image_path, size_hint=(None, None),
                          size=(240, 270))  # Размер изображения можно настроить
    faction_image.opacity = 0.8  # Сделать изображение немного полупрозрачным

    # Добавляем изображение с отступом снизу с использованием pos_hint для установки положения
    faction_image.pos_hint = {'x': 0, 'y': 0.4}  # Установим его чуть выше низу
    layout.add_widget(faction_image)

    weapon_data = load_weapon_data()  # Загружаем данные оружия

    # Левая часть - Найм оружия
    weapon_selection_layout = BoxLayout(orientation='vertical', size_hint=(0.4, 0.6), padding=10, spacing=5)
    for weapon_name, weapon_info in weapon_data.items():
        if isinstance(weapon_info, dict):
            # Получаем количество для каждого типа оружия (если есть)
            weapon_count = weapon_info.get('count', 0)

            # Создаем метку для отображения типа оружия и его количества
            weapon_label = Label(text=f"{weapon_name}: {weapon_count} шт.", size_hint_y=None, height=40,
                                 color=(0.8, 0.8, 0.8, 1))

            # Задаем позицию метки с помощью pos_hint (например, для первого оружия задаем расположение на высоте 0.8 от верхней границы)
            weapon_label.pos_hint = {'x': 0.1, 'y': 0.1}  # С небольшим отступом от правого верхнего угла

            weapon_labels[weapon_name] = weapon_label
            weapon_selection_layout.add_widget(weapon_label)

    # Список оружия с кнопками для найма
    weapons = get_weapons(faction)  # Получаем список оружия для фракции

    for weapon_name, weapon_info in weapons.items():
        weapon_button = Button(text=weapon_name, size_hint_y=None, height=60, background_normal='', background_color=(0.3, 0.6, 0.3, 1), color=(1, 1, 1, 1), font_size=16)
        weapon_button.bind(on_release=lambda x, name=weapon_name: select_weapon(name, weapons, faction, army_cash))
        weapon_button.radius = [10]  # Закругленные углы
        weapon_button.bind(on_press=lambda x: animate_button(x))  # Добавляем анимацию при нажатии
        weapon_selection_layout.add_widget(weapon_button)

    # Правая часть - Данные миссии и кнопки
    mission_data_layout = BoxLayout(orientation='vertical', size_hint=(0.6, 0.6), padding=10, spacing=10)

    city_name_input = TextInput(hint_text="Название города", text=city_name_text, multiline=False, size_hint_y=None, height=40)
    city_name_input.background_normal = ''
    city_name_input.background_color = (0.9, 0.9, 0.9, 1)
    city_name_input.foreground_color = (0, 0, 0, 1)
    city_name_input.radius = [10]  # Закругленные углы для поля ввода

    coord_input = TextInput(hint_text="Координаты", text=coordinates_text, multiline=False, size_hint_y=None, height=40)
    coord_input.background_normal = ''
    coord_input.background_color = (0.9, 0.9, 0.9, 1)
    coord_input.radius = [10]

    select_weapon_button = Button(text="Выбрать оружие", size_hint_y=None, height=60, background_normal='', background_color=(0.3, 0.4, 0.9, 1), color=(1, 1, 1, 1), font_size=16)
    select_weapon_button.bind(on_release=lambda x: open_weapon_selection_popup(select_weapon_button))
    select_weapon_button.radius = [10]  # Закругленные углы
    select_weapon_button.bind(on_press=lambda x: animate_button(x))

    weapon_quantity_input = TextInput(hint_text="Количество", multiline=False, size_hint_y=None, height=40)
    weapon_quantity_input.background_normal = ''
    weapon_quantity_input.background_color = (0.9, 0.9, 0.9, 1)
    weapon_quantity_input.radius = [10]

    mission_button = Button(text="Запуск", size_hint_y=None, height=60, background_normal='', background_color=(0.8, 0.2, 0.2, 1), color=(1, 1, 1, 1), font_size=16)
    mission_button.bind(on_release=lambda x: start_mission(city_name_input.text, coord_input.text, select_weapon_button.text, weapon_quantity_input.text, path_to_army))
    mission_button.radius = [10]
    mission_button.bind(on_press=lambda x: animate_button(x))

    mission_data_layout.add_widget(city_name_input)
    mission_data_layout.add_widget(coord_input)
    mission_data_layout.add_widget(select_weapon_button)
    mission_data_layout.add_widget(weapon_quantity_input)
    mission_data_layout.add_widget(mission_button)

    # Размещаем блоки в layout с использованием pos_hint для гибкого позиционирования
    weapon_selection_layout.pos_hint = {'x': 0, 'y': 0.1}  # 0.1 от верхнего края
    mission_data_layout.pos_hint = {'x': 0.4, 'y': 0.1}  # 0.4 от левого края

    layout.add_widget(weapon_selection_layout)
    layout.add_widget(mission_data_layout)

    if current_weapon_management_popup:
        current_weapon_management_popup.dismiss()

    current_weapon_management_popup = Popup(title="Управление дальнобойным оружием", content=layout, size_hint=(0.8, 0.8), background_color=(0.2, 0.2, 0.2, 1))
    current_weapon_management_popup.open()


# Улучшение функции открытия окна выбора оружия
class StyledWeaponButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''  # Отключение стандартного фона
        self.background_color = (0, 0, 0, 0)  # Полностью прозрачный фон
        self.color = (1, 1, 1, 1)  # Белый цвет текста
        self.font_size = 18  # Размер шрифта

        with self.canvas.before:
            self.rect_color = Color(0.3, 0.5, 0.7, 1)  # Основной цвет кнопки
            self.rect = RoundedRectangle(radius=[15], size=self.size, pos=self.pos)

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press(self):
        self.rect_color.rgba = (0.2, 0.4, 0.6, 1)  # Темнее при нажатии

    def on_release(self):
        self.rect_color.rgba = (0.3, 0.5, 0.7, 1)  # Возврат к исходному цвету


def open_weapon_selection_popup(button):
    """Открывает всплывающее окно для выбора оружия."""
    global current_weapon_selection_popup
    layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

    weapon_data = load_weapon_data()
    button_height = 50  # Высота одной кнопки

    # Генерация кнопок для оружия
    for weapon_name, weapon_info in weapon_data.items():
        if isinstance(weapon_info, dict):
            # Стилизация кнопки
            weapon_button = StyledWeaponButton(text=weapon_name, size_hint=(1, None), height=button_height)
            weapon_button.bind(on_release=lambda x, name=weapon_name: select_weapon_from_list(button, name))
            layout.add_widget(weapon_button)

    # Закрываем предыдущее окно выбора оружия, если оно существует
    if current_weapon_selection_popup:
        current_weapon_selection_popup.dismiss()

    # Вычисление размера окна на основе количества кнопок
    popup_height = len(weapon_data) * (button_height + 10) + 20  # Высота кнопок + отступы
    popup_height = min(popup_height, 400)  # Ограничение максимальной высоты окна

    # Создание и отображение всплывающего окна выбора оружия
    current_weapon_selection_popup = Popup(
        title="Выберите оружие",
        content=layout,
        size_hint=(None, None),  # Фиксированный размер
        size=(300, popup_height),  # Ширина окна 300, высота подгоняется под кнопки
        title_size=24
    )
    current_weapon_selection_popup.open()



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

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.rect.size = (self.size[0] - 5, self.size[1] - 5)  # Анимация при нажатии
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.rect.size = self.size  # Возврат к исходным размерам
        return super().on_touch_up(touch)


def select_weapon(weapon_name, weapons, faction, army_cash):
    weapon_info = weapons[weapon_name]
    stats_info = '\n'.join([f"{key}: {value}" for key, value in weapon_info.get('stats', {}).items()])

    weapon_details_layout = BoxLayout(orientation='horizontal', padding=20, spacing=15)

    # Фон для Popup
    with weapon_details_layout.canvas.before:
        Color(0.1, 0.1, 0.2, 1)  # Темный фон
        RoundedRectangle(size=weapon_details_layout.size, pos=weapon_details_layout.pos, radius=[20])

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
        text=f"[b]Стоимость:[/b] {weapon_info.get('cost', [0, 0])[0]} Крон, {weapon_info.get('cost', [0, 0])[1]} Рабочих",
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

        # Передаем параметры koef и class_weapon в hire_unit
        if army_cash.hire_unit(weapon_name, cost, quantity, weapon_name, koef):
            print(
                f"Построено {quantity} юнитов {weapon_name}. Общая стоимость: {total_cost[0]} Крон, {total_cost[1]} Рабочих.")

            # Закрываем окно деталей оружия
            if weapon_details_popup:
                weapon_details_popup.dismiss()

            # Обновляем окно управления оружием
            open_weapon_db_management(faction, army_cash)
        else:
            print(f"Недостаточно ресурсов для найма {quantity} юнитов {weapon_name}.")

    except ValueError:
        print("Пожалуйста, введите корректное количество юнитов.")
        error_popup = Popup(title="Ошибка", content=Label(text="Пожалуйста, введите корректное количество юнитов."),
                            size_hint=(0.5, 0.5))
        error_popup.open()


def start_mission(city_name, coordinates, selected_weapon_name, selected_quantity, path_to_army):
    if not city_name or not coordinates:
        print("Поля города и координат должны быть заполнены.")
        error_popup = Popup(title="Ошибка", content=Label(text="Поля города и координат должны быть заполнены."),
                            size_hint=(0.5, 0.5))
        error_popup.open()
        return

    if not selected_weapon_name:
        print("Оружие должно быть выбрано.")
        error_popup = Popup(title="Ошибка", content=Label(text="Оружие должно быть выбрано."), size_hint=(0.5, 0.5))
        error_popup.open()
        return

    try:
        selected_quantity = int(selected_quantity)
    except ValueError:
        print("Количество оружия должно быть числом.")
        error_popup = Popup(title="Ошибка", content=Label(text="Количество оружия должно быть числом."),
                            size_hint=(0.5, 0.5))
        error_popup.open()
        return

    weapon_data = load_weapon_data()
    if selected_weapon_name not in weapon_data:
        print(f"Оружие {selected_weapon_name} не найдено в базе.")
        error_popup = Popup(title="Ошибка", content=Label(text=f"Оружие {selected_weapon_name} не найдено в базе."),
                            size_hint=(0.5, 0.5))
        error_popup.open()
        return

    available_quantity = weapon_data[selected_weapon_name].get('count', 0)
    if selected_quantity > available_quantity:
        print(f"Недостаточно оружия {selected_weapon_name}. Доступно: {available_quantity}, необходимо: {selected_quantity}.")
        error_popup = Popup(title="Ошибка", content=Label(
            text=f"Недостаточно оружия {selected_weapon_name}. Доступно: {available_quantity}, необходимо: {selected_quantity}."),
                            size_hint=(0.5, 0.5))
        error_popup.open()
        return

    # Обновляем количество оружия и сохраняем изменения
    weapon_data[selected_weapon_name]['count'] -= selected_quantity
    save_weapon_data(weapon_data)
    update_unit_quantity(selected_weapon_name, weapon_data[selected_weapon_name]['count'])

    # Извлекаем все характеристики оружия для передачи в strike
    weapon_characteristics = {
        "name": selected_weapon_name,
        "count": weapon_data[selected_weapon_name].get('count', []),
        "koef": weapon_data[selected_weapon_name].get('koef', []),
        "all_damage": weapon_data[selected_weapon_name].get('all_damage', {})
    }

    # Передаем данные в модуль strike
    strike.strike_to_city(city_name, weapon_characteristics, path_to_army)

    # Закрытие попапа после успешного пуска
    if current_weapon_management_popup:
        current_weapon_management_popup.dismiss()



def select_weapon_from_list(button, weapon_name):
    """Устанавливает выбранное оружие в текст кнопки и закрывает всплывающее окно."""
    button.text = weapon_name  # Устанавливаем выбранное оружие на кнопке
    if current_weapon_selection_popup:
        current_weapon_selection_popup.dismiss()  # Закрываем окно выбора оружия

# Функция для получения данных юнитов
def get_weapons(faction):
    english_faction = translation_dict.get(faction, faction)
    weapons_file_path = f"files/config/weapon/{english_faction}.json"
    if os.path.exists(weapons_file_path):
        with open(weapons_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


#------Базовая функция------------

def start_army_mode(faction, game_area):
    """Инициализация армейского режима для выбранной фракции."""

    # Загружаем города из файла
    cities = load_cities_from_file(faction)

    # Создаем layout для кнопок
    army_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, 0.1),
        pos_hint={'x': 0, 'y': 0},
        spacing=10,  # Расстояние между кнопками
        padding=10   # Отступы внутри layout
    )

    # Функция для создания стильных кнопок
    def create_styled_button(text, on_press_callback):
        button = Button(
            text=text,
            size_hint_x=0.33,
            size_hint_y=None,
            height=50,
            background_color=(0, 0, 0, 0),  # Прозрачный фон
            color=(1, 1, 1, 1),             # Цвет текста (белый)
            font_size=16,                   # Размер шрифта
            bold=True                       # Жирный текст
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
    train_btn = create_styled_button("Тренировка войск", lambda x: show_unit_selection(faction, ArmyCash(faction)))
    headquarters_btn = create_styled_button("Генштаб", lambda x: show_army_headquarters(faction, cities))
    defend_btn = create_styled_button("Управление дб. оружием", lambda x: open_weapon_db_management(faction, WeaponCash(faction)))

    # Добавляем кнопки в layout
    army_layout.add_widget(train_btn)
    army_layout.add_widget(headquarters_btn)
    army_layout.add_widget(defend_btn)

    # Добавляем layout с кнопками в нижнюю часть экрана
    game_area.add_widget(army_layout)


def load_cities_from_file(faction):
    try:
        with open('files/config/city.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        # Проверка на существование фракции в данных
        if faction in data['kingdoms']:
            return data['kingdoms'][faction]['fortresses']
        else:
            print(f"Фракция {faction} не найдена в файле city.json.")
            return []
    except FileNotFoundError:
        print("Файл city.json не найден.")
        return []
    except json.JSONDecodeError:
        print("Ошибка при чтении файла city.json.")
        return []
