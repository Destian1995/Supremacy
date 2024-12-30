from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, RoundedRectangle

import os
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

class AdvisorView(FloatLayout):
    def __init__(self, faction, **kwargs):
        super(AdvisorView, self).__init__(**kwargs)
        self.faction = faction
        self.size_hint = (0.8, 0.8)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # Добавление контейнера для изображения и имени советника
        advisor_info_layout = BoxLayout(
            orientation='vertical',
            size_hint=(0.3, 0.7),
            pos_hint={'x': 0.05, 'top': 0.95},
            spacing=10
        )

        # Имя советника
        advisor_name_label = Label(
            text=foreign_ministers.get(self.faction, "Неизвестен"),
            size_hint=(1, 0.2),
            font_size='18sp',
            halign='center'
        )
        advisor_info_layout.add_widget(advisor_name_label)

        # Добавление контейнера с именем советника
        self.add_widget(advisor_info_layout)

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
        # Путь к картинке советника
        advisor_image_path = f"files/sov/sov_{translation_dict.get(self.faction)}.jpg"

        # Загрузка изображения советника
        if os.path.exists(advisor_image_path):
            advisor_layout = FloatLayout(size_hint=(0.5, 0.5), pos_hint={'x': 0.0, 'y': 0.3})

            # Добавляем изображение
            advisor_image = Image(
                source=advisor_image_path,
                size_hint=(1, 1),  # Увеличиваем изображение
                pos_hint={'center_x': 0.3, 'center_y': 0.7}  # Центрируем внутри layout
            )
            advisor_layout.add_widget(advisor_image)

            # Добавляем имя советника (поверх изображения)
            advisor_name_label = Label(
                text=foreign_ministers.get(self.faction, "Неизвестен"),
                size_hint=(1, 0.2),
                pos_hint={'center_x': 0.3, 'y': 0.15},  # Размещаем под изображением
                font_size='20sp',
                halign='center',
                color=(1, 1, 1, 1),  # Белый текст
                outline_color=(0, 0, 0, 1),  # Черная окантовка текста
                outline_width=2
            )
            advisor_layout.add_widget(advisor_name_label)

            self.add_widget(advisor_layout)


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
        """Загружает и отображает состояние отношений с изображением и дипломатической силой."""
        try:
            # Загрузка файлов
            with open("files/config/status/dipforce/force_state.json", "r", encoding="utf-8") as f:
                force_state = json.load(f)
            with open("files/config/status/dipforce/relation.json", "r", encoding="utf-8") as f:
                relation = json.load(f)
        except FileNotFoundError:
            print("Один из файлов не найден.")
            return

        # Очистка текущего виджета для отображения новой информации
        self.clear_widgets()

        # Основной контейнер
        main_layout = BoxLayout(orientation="horizontal", spacing=20, padding=10)

        # Загрузка изображения дворца
        palace_image_path = f"files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg"
        if os.path.exists(palace_image_path):
            palace_image = Image(source=palace_image_path, size_hint=(0.4, 1), allow_stretch=True, keep_ratio=True)
        else:
            palace_image = Label(text="Изображение отсутствует", size_hint=(0.4, 1), font_size="16sp")

        # Добавляем изображение дворца в левую часть
        main_layout.add_widget(palace_image)

        # Создание текстового окна с фоном и скругленными углами
        text_frame = BoxLayout(
            orientation="vertical",
            size_hint=(0.5, 1),
            padding=10,
            spacing=10,
            pos_hint={'top': 1.3},  # Выравнивание блока по правому верхнему краю
        )

        with text_frame.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # Светло-серый фон
            self.rect = RoundedRectangle(size=text_frame.size, pos=text_frame.pos, radius=[40])
            Color(0, 0, 0, 1)  # Чёрная рамка
            self.border = RoundedRectangle(size=(text_frame.size[0], text_frame.size[1]), pos=text_frame.pos,
                                           radius=[40])

        # Обновляем размеры и позиции при изменении размеров окна
        text_frame.bind(
            size=lambda instance, value: setattr(self.rect, "size", value),
            pos=lambda instance, value: setattr(self.rect, "pos", value),
        )

        # Заголовок окна
        text_frame.add_widget(Label(
            text=f"Дипломатическая сила: {force_state.get(self.faction, 'Нет данных')}",
            font_size="20sp",
            color=(0, 0, 0, 1),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=50
        ))

        # Отображение отношений
        relations = relation.get("relations", {}).get(self.faction, {})
        for country, value in relations.items():
            text_frame.add_widget(Label(
                text=f"{country}: {value}%",
                font_size="18sp",
                color=(0.2, 0.2, 0.2, 1),
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=30
            ))

        # Добавляем текстовое окно в правую часть
        main_layout.add_widget(text_frame)

        # Добавляем основной контейнер в виджет
        self.add_widget(main_layout)



    def show_advisor_opinion(self, instance):
        """Отображает мнение советника с его изображением и именем."""
        opinions = {
            "Аркадия": "Нам нужно укрепить отношения с Этерией.",
            "Селестия": "Халидон становится опасным соседом.",
            "Хиперион": "Мы должны инвестировать в дипломатические миссии.",
            "Этерия": "Торговые отношения с Селестией в приоритете.",
            "Халидон": "Следует поддерживать нашу армию на границе.",
        }

        # Очистка текущего виджета для отображения новой информации
        self.clear_widgets()

        # Отображение мнения советника
        opinion = opinions.get(self.faction, "Нет данных о мнении советника.")
        self.add_widget(Label(
            text=f"Мнение: {opinion}",
            pos_hint={'center_x': 0.5, 'y': 0.4},
            font_size='16sp',
            halign='center',
            valign='middle'
        ))
