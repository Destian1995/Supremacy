import random
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.core.window import Window
import os
import yaml
import json
import chardet

from kivy.uix.textinput import TextInput

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
        self.relations_path = r'files\config\status\dipforce'
        self.relations_file = r'files\config\status\dipforce\relations.json'
        # Настройки темы
        self.colors = {
            'background': (0.95, 0.95, 0.95, 1),
            'primary': (0.118, 0.255, 0.455, 1),  # Темно-синий
            'accent': (0.227, 0.525, 0.835, 1),   # Голубой
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

        news_button = Button(
            text="Торговые условия",
            size_hint=(None, None),
            size=(Window.width * 0.2, Window.height * 0.08),  # Адаптивный размер
            background_normal='',
            background_color=(0.227, 0.525, 0.835, 1),
            color=(1, 1, 1, 1),
            font_size=Window.height * 0.02,  # Размер шрифта зависит от высоты окна
            bold=True,
            border=(0, 0, 0, 0)
        )
        news_button.bind(on_press=lambda x: self.trade_news(self.faction))

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
        bottom_panel.add_widget(news_button)
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


    def close_window(self, instance):
        """Закрытие окна"""
        self.popup.dismiss()

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
        """Загружает текущие отношения из файла relations.json"""
        relations_file = r'files/config/status/dipforce/relations.json'
        try:
            with open(relations_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Файл relations.json не найден. Создаем новый.")
            return {"relations": {}}

    def calculate_coefficient(self, relation_level):
        """Рассчитывает коэффициент на основе уровня отношений"""
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

    def save_relations(self, relations_data):
        """Сохраняем обновленные отношения в файл relations.json"""
        try:
            with open(self.relations_file, "w", encoding="utf-8") as f:
                json.dump(relations_data, f, ensure_ascii=False, indent=4)
        except PermissionError:
            print("Ошибка доступа к файлу relations.json. Проверьте права доступа.")

    def manage_relations(self):
        """Управление отношениями только для фракций, заключивших дипломатическое соглашение"""
        my_fraction = translation_dict.get(self.faction)
        faction_dir_path = os.path.join(self.relations_path, my_fraction)

        if not os.path.exists(faction_dir_path):
            print(f"Путь {faction_dir_path} не существует.")
            return

        relations_data = self.load_relations()

        if self.faction not in relations_data["relations"]:
            print(f"Отношения для фракции {self.faction} не найдены.")
            return

        # Перебираем файлы в директории, обрабатываем только тех, с кем заключены соглашения
        for filename in os.listdir(faction_dir_path):
            if filename.endswith(".json"):
                faction_name_en = filename.replace('.json', '')
                faction_name_ru = reverse_translation_dict.get(faction_name_en, faction_name_en)

                # Проверяем, есть ли дипломатическое соглашение
                if faction_name_ru in relations_data["relations"][self.faction]:
                    current_value_self = relations_data["relations"][self.faction][faction_name_ru]
                    current_value_other = relations_data["relations"][faction_name_ru][self.faction]

                    relations_data["relations"][self.faction][faction_name_ru] = min(current_value_self + 7, 100)
                    relations_data["relations"][faction_name_ru][self.faction] = min(current_value_other + 7, 100)

                # Удаляем обработанный файл (чтобы это изменение было одноразовым)
                os.remove(os.path.join(faction_dir_path, filename))

        # Сохраняем обновленные данные
        self.save_relations(relations_data)


    def show_relations(self, instance):
        """Отображает окно с таблицей отношений."""
        self.manage_relations()
        try:
            with open(self.relations_file, "r", encoding="utf-8") as f:
                relation = json.load(f)
        except FileNotFoundError:
            print("Файл relations.json не найден.")
            return
        faction_relations = relation.get("relations", {}).get(self.faction, {})
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
            text=f"Отношения {self.faction}",
            font_size=Window.height * 0.03,  # Адаптивный размер шрифта
            bold=True,
            size_hint_y=None,
            height=Window.height * 0.06,  # Адаптивная высота
            color=(0.15, 0.15, 0.15, 1)
        )
        main_layout.add_widget(header)

        # Таблица с данными
        table = GridLayout(
            cols=2,
            size_hint_y=None,
            spacing=dp(5),
            row_default_height=Window.height * 0.06  # Адаптивная высота строки
        )
        table.bind(minimum_height=table.setter('height'))

        # Заголовки таблицы
        table.add_widget(self.create_header("Фракция"))
        table.add_widget(self.create_header("Отношения"))

        # Добавление данных
        for country, value in faction_relations.items():
            table.add_widget(self.create_cell(country))
            table.add_widget(self.create_value_cell(value))

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
