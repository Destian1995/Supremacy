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

reverse_translation_dict = {v: k for k, v in translation_dict.items()}

class AdvisorView(FloatLayout):
    def __init__(self, faction, **kwargs):
        super(AdvisorView, self).__init__(**kwargs)
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
        palace_image_path = f"files/sov/parlament/{self.faction}_palace.jpg"
        if os.path.exists(palace_image_path):
            palace_image = Image(
                source=palace_image_path,
                size_hint=(1, 1),
                allow_stretch=True,
                keep_ratio=False
            )
            left_panel.add_widget(palace_image)

        # Правая панель
        right_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.55, 1),
            spacing=0,  # Убираем промежутки между элементами
            padding=0   # Убираем отступы
        )

        # Блок с мнением советника (ВПЛОТНУЮ К ВЕРХУ)
        advice_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,  # Убираем растяжение по высоте
            height=dp(120),    # Фиксированная высота, можно увеличить
            padding=dp(10)
        )
        with advice_card.canvas.before:
            Color(*self.colors['card'])
            RoundedRectangle(pos=advice_card.pos, size=advice_card.size, radius=[10])

        advice_text = Label(
            text="Наши дипломатические усилия должны быть сосредоточены на укреплении связей с нейтральными фракциями.",
            font_size=dp(14),
            color=(0.2, 0.2, 0.2, 1),
            halign='left',
            valign='top',
            size_hint=(1, 1),
            text_size=(Window.width * 0.5 - dp(40), None)
        )
        advice_card.add_widget(advice_text)

        # Добавляем советника в правую панель
        right_panel.add_widget(advice_card)

        # Панель вкладок (СРАЗУ ПОД СОВЕТНИКОМ)
        tabs_panel = ScrollView(
            size_hint=(1, 1),  # Позволяет вкладкам заполнять оставшееся пространство
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

        # Добавляем вкладки
        self.add_tab_button("Последние новости", self.last_news)
        self.add_tab_button("Состояние отношений", self.show_relations)

        tabs_panel.add_widget(self.tabs_content)
        right_panel.add_widget(tabs_panel)

        # Сборка интерфейса
        main_layout.add_widget(left_panel)
        main_layout.add_widget(right_panel)
        self.interface_window.add_widget(main_layout)

        # Нижняя панель с кнопками
        bottom_panel = BoxLayout(
            size_hint=(1, None),
            height=dp(60),
            padding=dp(10),
            pos_hint={'x': 0, 'y': 0}
        )
        close_button = Button(
            text="Закрыть",
            size_hint=(None, None),
            size=(dp(120), dp(50)),
            background_normal='',
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=dp(16),
            bold=True,
            border=(0, 0, 0, 0)
        )
        close_button.bind(on_press=self.close_window)
        bottom_panel.add_widget(close_button)
        self.interface_window.add_widget(bottom_panel)

        # Создаем Popup (уменьшен размер до 70%)
        self.popup = Popup(
            title=f"[size=20][b]{foreign_ministers[self.faction]}[/b], Министр Иностранных Дел[/size]",
            title_size=dp(18),
            content=self.interface_window,
            size_hint=(0.7, 0.7),  # Уменьшено с 0.85 до 0.7
            separator_height=dp(0),
            background='files/sov/parlament/popup_bg.png' if os.path.exists('files/sov/parlament/popup_bg.png') else ''
        )
        self.popup.open()

    def add_tab_button(self, text, on_press=None):
        """Создает стилизованную кнопку вкладки"""
        btn = Button(
            text=text,
            size_hint=(1, None),
            height=dp(60),
            font_size=dp(16),
            bold=True,
            background_normal='',
            background_color=(0.95, 0.95, 0.95, 1),
            color=self.colors['primary'],
            border=(0, 0, 0, 0)
        )
        with btn.canvas.before:
            Color(*self.colors['primary'])
            RoundedRectangle(pos=btn.pos, size=btn.size, radius=[5])
            Color(rgba=(1, 1, 1, 0.1))
            Rectangle(pos=btn.pos, size=(btn.width, 2))

        btn.bind(on_press=on_press)
        btn.bind(on_enter=lambda x: setattr(btn, 'background_color', (0.9, 0.9, 0.9, 1)))
        btn.bind(on_leave=lambda x: setattr(btn, 'background_color', (0.95, 0.95, 0.95, 1)))
        self.tabs_content.add_widget(btn)

    def close_window(self, instance):
        """Закрытие окна"""
        self.popup.dismiss()  # Закрывает окно Popup

    def on_button_hover(self, instance):
        """Меняет цвет кнопки при наведении мыши"""
        instance.background_color = (0.3, 0.7, 1, 1)

    def on_button_leave(self, instance):
        """Возвращает цвет кнопки при уходе мыши"""
        instance.background_color = (0.2, 0.6, 0.9, 1)

    def last_news(self):
        pass

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

    def load_relations(self):
        """Загружаем текущие отношения из файла relations.json"""
        try:
            with open(self.relations_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Файл relations.json не найден. Создаем новый.")
            return {"relations": {}}

    def save_relations(self, relations_data):
        """Сохраняем обновленные отношения в файл relations.json"""
        try:
            with open(self.relations_file, "w", encoding="utf-8") as f:
                json.dump(relations_data, f, ensure_ascii=False, indent=4)
        except PermissionError:
            print("Ошибка доступа к файлу relations.json. Проверьте права доступа.")


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
            padding=dp(10)
        )

        # Заголовок
        header = Label(
            text=f"Отношения {self.faction}",
            font_size='20sp',
            bold=True,
            size_hint_y=None,
            height=dp(40),
            color=(0.15, 0.15, 0.15, 1)
        )
        main_layout.add_widget(header)

        # Таблица с данными
        table = GridLayout(
            cols=2,
            size_hint_y=None,
            spacing=dp(5),
            row_default_height=dp(40)
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
            font_size='18sp',
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(45)
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
            font_size='16sp',
            bold=True,
            color=(1, 1, 1, 1),  # Белый цвет текста
            halign='left',
            valign='middle',
            padding_x=dp(15),
            size_hint_y=None,
            height=dp(40)
        )
        lbl.bind(size=lbl.setter('text_size'))  # Автоматический перенос текста
        return lbl

    def create_value_cell(self, value):
        """Создает ячейку со значением отношений"""
        color = self.get_relation_color(value)
        lbl = Label(
            text=f"{value}%",
            font_size='16sp',
            bold=True,
            color=color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(40)
        )
        return lbl

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
        elif 25 < value <= 40:
            return (1.0, 0.8, 0.0, 1)
        elif 40 < value <= 50:
            return (0.2, 0.7, 0.3, 1)
        elif 50 < value <= 60:
            return (0.0, 0.8, 0.8, 1)
        elif 60 < value <= 75:
            return (0.0, 0.6, 1.0, 1)
        elif 75 < value <= 90:
            return (0.1, 0.3, 0.9, 1)
        else:
            return (1, 1, 1, 1)
