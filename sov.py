from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
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


class AdvisorView(FloatLayout):
    def __init__(self, faction, **kwargs):
        super(AdvisorView, self).__init__(**kwargs)
        self.faction = faction
        self.size_hint = (0.8, 0.8)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # Инициализация истории ресурсов
        self.resource_history = {resource: [] for resource in ["cash", "people", "food"]}

        # Вкладки слева
        self.tabs_layout = BoxLayout(
            orientation='vertical',
            size_hint=(0.4, 0.6),
            pos_hint={'x': 0.4, 'top': 0.95}
        )
        self.add_tab_button("Сообщения")
        self.add_tab_button("Состояние отношений", self.show_relations)
        self.add_tab_button("Мнения советника", self.show_advisor_opinion)
        self.add_widget(self.tabs_layout)

        # Путь к картинке парламента
        palace_image_path = f"files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg"

        # Загрузка изображения парламента
        if os.path.exists(palace_image_path):
            palace_layout = FloatLayout(size_hint=(0.5, 0.5), pos_hint={'x': 0.0, 'y': 0.3})

            # Добавляем изображение
            advisor_image = Image(
                source=palace_image_path,
                size_hint=(1.2, 1.2),  # Увеличиваем изображение
                pos_hint={'center_x': 0.1, 'center_y': 0.7}  # Центрируем внутри layout
            )
            palace_layout.add_widget(advisor_image)
            self.add_widget(palace_layout)

    # Инициализация истории ресурсов
    def load_resources(self):
        try:
            # Detect encoding
            with open('files/config/resources/cash.json', 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']

            # Use the detected encoding to read the file
            with open('files/config/resources/cash.json', 'r', encoding=encoding) as file:
                result = json.load(file)
                print('Данные по ресурсам игрока:', result)
                return result

        except FileNotFoundError:
            print("Файл с ресурсами не найден.")
            return {}

    def track_resources(self):
        """Сохраняет текущие ресурсы в историю."""
        resources = self.load_resources()
        if resources:
            for key in self.resource_history:
                self.resource_history[key].append(resources.get(key, 0))
                # Сохраняем только последние три значения
                if len(self.resource_history[key]) > 3:
                    self.resource_history[key].pop(0)

    def analyze_resource_trend(self):
        """Анализирует тенденцию изменения ресурсов."""
        resources = self.load_resources()
        if not resources:
            return "Нет данных о ресурсах."

        changes = {}
        for resource, history in self.resource_history.items():
            if len(history) < 2:
                continue
            # Считаем разницу между последними значениями
            change = history[-1] - history[-2]
            changes[resource] = change

        # Определяем какой ресурс изменился больше всего
        if not changes:
            return "Нет изменений в ресурсах."

        # Сортируем ресурсы по величине изменения
        sorted_changes = sorted(changes.items(), key=lambda item: abs(item[1]), reverse=True)
        resource, change = sorted_changes[0]

        if change > 0:
            return f"Ресурс '{resource}' растет. Хорошие новости!"
        elif change < 0:
            return f"Ресурс '{resource}' падает. Нам нужно что-то делать!"
        else:
            return f"Ресурс '{resource}' стабилен."

    # Отображение мнения советника
    def show_advisor_opinion(self, instance):
        """Отображает мнение советника с его изображением, именем и рамкой."""
        # Очистка текущих виджетов
        self.clear_widgets()

        opinions_path = f'files/config/status/dipforce/{translation_dict.get(self.faction)}/message.yaml'
        try:
            with open(opinions_path, 'r', encoding='utf-8') as file:
                opinions = yaml.safe_load(file)
                print(f'Подгруженные opinions: {opinions}')
        except FileNotFoundError:
            opinions = {}
            print(f"Файл {opinions_path} не найден.")
        except yaml.YAMLError as e:
            opinions = {}
            print(f"Ошибка декодирования YAML в файле {opinions_path}: {e}")

        # Словарь путей к изображениям советников
        advisor_images = {
            "Аркадия": "files/sov/sov_arkadia.jpg",
            "Селестия": "files/sov/sov_celestia.jpg",
            "Хиперион": "files/sov/sov_giperion.jpg",
            "Этерия": "files/sov/sov_eteria.jpg",
            "Халидон": "files/sov/sov_halidon.jpg",
        }

        # Внешний макет с отступом вправо
        main_layout = BoxLayout(orientation='horizontal', spacing=20, padding=[200, 10, 10, 10])

        # Левый блок: изображение, имя и мнение советника
        advisor_layout = BoxLayout(orientation='vertical', size_hint=(0.4, 1), spacing=10)

        # Изображение советника
        advisor_image_path = advisor_images.get(self.faction)
        if advisor_image_path:
            advisor_image = Image(source=advisor_image_path, size_hint=(1, 0.7), allow_stretch=True, keep_ratio=True)
        else:
            advisor_image = Image(source="files/sov/default.jpg", size_hint=(1, 0.7), allow_stretch=True,
                                  keep_ratio=True)

        advisor_layout.add_widget(advisor_image)

        # Имя советника с рамкой
        advisor_name = foreign_ministers.get(self.faction, "Неизвестен")
        advisor_name_box = BoxLayout(size_hint=(1, 0.1), padding=[10, 10])
        with advisor_name_box.canvas.before:
            Color(0.8, 0.8, 0.8, 1)  # Цвет фона рамки
            advisor_name_box.rect = Rectangle(size=advisor_name_box.size, pos=advisor_name_box.pos)
            advisor_name_box.bind(size=lambda _, s: setattr(advisor_name_box.rect, 'size', s))
            advisor_name_box.bind(pos=lambda _, p: setattr(advisor_name_box.rect, 'pos', p))

        advisor_name_label = Label(
            text=advisor_name,
            font_size='20sp',
            halign='center',
            valign='middle',
            color=(0, 0, 0, 1)  # Цвет текста
        )
        advisor_name_box.add_widget(advisor_name_label)
        advisor_layout.add_widget(advisor_name_box)

        # Мнение советника
        faction_opinion = opinions.get("Экономические", [])
        opinion_message = faction_opinion[0].get("сообщение",
                                                 "Нет данных.") if faction_opinion else "Мне нечего Вам сказать."

        # Анализ изменений ресурсов
        resource_trend_message = self.analyze_resource_trend()
        opinion_message = f"{opinion_message} {resource_trend_message}"

        opinion_box = TextInput(
            text=opinion_message,
            size_hint=(1, 0.2),
            font_size='16sp',
            halign='center',
            readonly=True,
            background_color=(0.9, 0.9, 0.9, 1),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 10, 10, 10]
        )
        advisor_layout.add_widget(opinion_box)

        # Добавляем левый блок в основной макет
        main_layout.add_widget(advisor_layout)

        # Добавление основного макета в виджет
        self.add_widget(main_layout)


    def add_tab_button(self, text, on_press=None):
        """Добавляет кнопку вкладки."""
        button = Button(
            text=text,
            size_hint=(1, 0.2),
            font_size='16sp'
        )
        if on_press:
            button.bind(on_press=on_press)
        self.tabs_layout.add_widget(button)

    def show_relations(self, instance):
        """Отображает окно с таблицей отношений."""
        try:
            # Загрузка файлов
            with open("files/config/status/dipforce/relation.json", "r", encoding="utf-8") as f:
                relation = json.load(f)
        except FileNotFoundError:
            print("Файл relation.json не найден.")
            return

        # Получение отношений для текущей фракции
        faction_relations = relation.get("relations", {}).get(self.faction, {})
        if not faction_relations:
            print(f"Нет данных об отношениях для фракции {self.faction}.")
            return

        # Создание основного макета для таблицы
        layout = GridLayout(cols=2, size_hint_y=None, spacing=10)
        layout.bind(minimum_height=layout.setter('height'))

        # Заголовки столбцов
        layout.add_widget(Label(
            text="Фракция",
            bold=True,
            font_size="18sp",
            size_hint_y=None,
            height=40
        ))
        layout.add_widget(Label(
            text="Отношения",
            bold=True,
            font_size="18sp",
            size_hint_y=None,
            height=40
        ))

        # Добавление данных в таблицу
        for country, value in faction_relations.items():
            layout.add_widget(Label(
                text=country,
                font_size="16sp",
                size_hint_y=None,
                height=30
            ))
            layout.add_widget(Label(
                text=f"{value}%",
                font_size="16sp",
                size_hint_y=None,
                height=30
            ))

        # Добавление прокрутки для большого количества данных
        scroll_view = ScrollView(size_hint=(1, None), size=(400, 300))
        scroll_view.add_widget(layout)

        # Создание всплывающего окна
        popup = Popup(
            title=f"Отношения {self.faction}",
            content=scroll_view,
            size_hint=(0.8, 0.6),
            auto_dismiss=True
        )
        popup.open()
