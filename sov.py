from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
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

reverse_translation_dict = {v: k for k, v in translation_dict.items()}

class AdvisorView(FloatLayout):
    def __init__(self, faction, **kwargs):
        super(AdvisorView, self).__init__(**kwargs)
        self.faction = faction
        self.relations_path = r'files\config\status\dipforce'
        self.relations_file = r'files\config\status\dipforce\relations.json'

        # Создаем окно интерфейса (Popup)
        self.interface_window = FloatLayout(size_hint=(1, 1))  # Окно занимает весь доступный размер
        self.interface_window.pos_hint = {'center_x': 0.5, 'center_y': 0.5}  # Центрируем окно

        # Разделим окно на 2 части: Левую (картинка) и Правую (кнопки и информация)
        layout = GridLayout(cols=2, size_hint=(1, 1), spacing=10, padding=[20, 20, 20, 20])

        # Левый блок — картинка (фото парламента или советника)
        left_layout = FloatLayout(size_hint=(0.5, 1))
        palace_image_path = f"files/sov/parlament/{self.faction}_palace.jpg"
        if os.path.exists(palace_image_path):
            palace_image = Image(
                source=palace_image_path,
                size_hint=(1, 1),
                allow_stretch=True,
                keep_ratio=True
            )
            left_layout.add_widget(palace_image)

        # Правый блок — кнопки и информация
        right_layout = GridLayout(cols=1, size_hint=(0.5, 1), spacing=10, padding=5)

        # Блок для отображения мнения советника (в правом верхнем углу)
        opinion_box = TextInput(
            text="Здесь будет мнение советника...",
            font_size='12sp',
            size_hint=(1, 0.3),
            readonly=True,
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            padding=[5, 5, 5, 5]
        )
        right_layout.add_widget(opinion_box)

        # Добавление вкладок (кнопок)
        self.tabs_layout = ScrollView(size_hint=(1, 0.6))  # Скроллинг вкладок
        self.tabs_content = GridLayout(cols=1, size_hint_y=None)
        self.tabs_content.bind(minimum_height=self.tabs_content.setter('height'))  # Адаптивная высота
        self.add_tab_button("Сообщения")
        self.add_tab_button("Состояние отношений", self.show_relations)
        self.add_tab_button("Мнения советника", self.show_advisor_opinion)
        self.tabs_layout.add_widget(self.tabs_content)  # Добавляем контейнер в ScrollView
        right_layout.add_widget(self.tabs_layout)

        # Добавление левой и правой части в главный макет
        layout.add_widget(left_layout)
        layout.add_widget(right_layout)

        # Добавляем главный макет в окно интерфейса
        self.interface_window.add_widget(layout)

        # Кнопки внизу окна
        buttons_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=50,
            spacing=10,
            padding=10
        )
        close_button = Button(
            text="Закрыть",
            size_hint=(None, None),
            size=(100, 40),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        close_button.bind(on_press=self.close_window)
        buttons_layout.add_widget(close_button)

        # Добавляем кнопки в нижнюю часть окна
        self.interface_window.add_widget(buttons_layout)
        buttons_layout.pos_hint = {'x': 0, 'y': 0}

        # Создаем Popup с окном интерфейса
        self.popup = Popup(
            title="Министерство Иностранных Дел",
            content=self.interface_window,
            size_hint=(0.8, 0.8),  # Размер окна
            pos_hint={'center_x': 0.5, 'center_y': 0.5}  # Центрирование окна
        )
        self.popup.open()  # Открываем окно

    def close_window(self, instance):
        """Закрытие окна"""
        self.popup.dismiss()  # Закрывает окно Popup

    def add_tab_button(self, text, on_press=None):
        """Добавляет кнопку вкладки с эффектом при наведении"""
        button = Button(
            text=text,
            size_hint=(1, None),  # Убираем фиксированную высоту кнопок
            height=40,  # Компактная высота
            font_size='14sp',
            background_normal='',
            background_color=(0.2, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            border=(5, 5, 5, 5)
        )
        if on_press:
            button.bind(on_press=on_press)

        # Эффект на кнопке при наведении
        button.bind(on_enter=self.on_button_hover)
        button.bind(on_leave=self.on_button_leave)
        self.tabs_content.add_widget(button)  # Добавляем кнопку в контейнер

    def on_button_hover(self, instance):
        """Меняет цвет кнопки при наведении мыши"""
        instance.background_color = (0.3, 0.7, 1, 1)

    def on_button_leave(self, instance):
        """Возвращает цвет кнопки при уходе мыши"""
        instance.background_color = (0.2, 0.6, 0.9, 1)



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
        # Перезагружаем данные о отношениях
        self.manage_relations()

        try:
            # Загрузка файлов
            with open(self.relations_file, "r", encoding="utf-8") as f:
                relation = json.load(f)
        except FileNotFoundError:
            print("Файл relations.json не найден.")
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