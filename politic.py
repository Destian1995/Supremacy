import os

from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
import json

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


# transform_filename(f'files/config/status/trade_dogovor/{имя фракции которой направляется договор}.json')
reverse_translation_dict = {v: k for k, v in translation_dict.items()}


class StyledButton(ButtonBehavior, BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)  # Ширина адаптируется, высота фиксированная
        self.height = 40  # Уменьшили высоту кнопки
        self.padding = [5, 5]  # Уменьшили отступы внутри кнопки

        # Цвета для разных состояний
        self.normal_color = (0.2, 0.6, 1, 1)  # Обычный цвет
        self.hover_color = (0.15, 0.5, 0.9, 1)  # Цвет при наведении
        self.pressed_color = (0.1, 0.4, 0.8, 1)  # Цвет при нажатии
        self.current_color = self.normal_color

        with self.canvas.before:
            self.color = Color(*self.current_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[8])  # Скругление углов

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.label = Label(
            text=text,
            font_size=14,
            color=(1, 1, 1, 1),
            bold=True,
            halign='center',
            valign='middle'
        )
        self.label.bind(size=self.label.setter('text_size'))
        self.add_widget(self.label)

        # Применяем эффекты при наведении и клике
        self.bind(on_press=self.on_press_effect, on_release=self.on_release_effect)
        self.bind(on_touch_move=self.on_hover, on_touch_up=self.on_leave)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press_effect(self, instance):
        """Эффект затемнения при нажатии"""
        self.current_color = self.pressed_color
        self.update_color()

    def on_release_effect(self, instance):
        """Возвращаем цвет после нажатия"""
        self.current_color = self.normal_color
        self.update_color()

    def on_hover(self, instance, touch):
        """Эффект при наведении"""
        if self.collide_point(*touch.pos):
            self.current_color = self.hover_color
            self.update_color()

    def on_leave(self, instance, touch):
        """Возвращаем цвет, если курсор ушел с кнопки"""
        if not self.collide_point(*touch.pos):
            self.current_color = self.normal_color
            self.update_color()

    def update_color(self):
        """Обновляет цвет фона"""
        self.canvas.before.clear()
        with self.canvas.before:
            self.color = Color(*self.current_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[8])


def show_new_agreement_window(faction, game_area):
    """Создание красивого окна с кнопками"""
    game_area.clear_widgets()
    # Создаем модальное окно
    modal = ModalView(
        size_hint=(0.8, 0.8),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        background_color=(0, 0, 0, 0)  # Прозрачный фон
    )
    # Основной контейнер для окна
    window = BoxLayout(
        orientation='vertical',
        padding=20,
        spacing=15,
        size_hint=(1, 1)
    )
    # Фон окна
    with window.canvas.before:
        Color(0.1, 0.1, 0.1, 1)  # Темный фон
        window.rect = RoundedRectangle(size=window.size, pos=window.pos, radius=[15])
    window.bind(pos=lambda obj, pos: setattr(window.rect, 'pos', pos),
                size=lambda obj, size: setattr(window.rect, 'size', size))
    # Заголовок
    title = Label(
        text="Новый договор",
        size_hint=(1, None),
        height=50,
        font_size=24,
        color=(1, 1, 1, 1),
        bold=True
    )
    # Список кнопок
    button_layout = BoxLayout(
        orientation='vertical',
        spacing=5,  # Уменьшили расстояние между кнопками
        size_hint=(1, None),  # Высота будет зависеть от содержимого
        height=0  # Начальная высота
    )
    button_layout.bind(minimum_height=button_layout.setter('height'))  # Автоматическая высота

    # Создаем кнопки для каждой категории
    categories = [
        ("Торговое соглашение", show_trade_agreement_form),
        ("Договор об культурном обмене", show_cultural_exchange_form),
        ("Предоставление дип. данных", show_diplomatic_data_form),
        ("Заключение альянса", show_alliance_form),
        ("Объявление войны", show_declare_war_form),
    ]
    for category_name, callback in categories:
        button = StyledButton(text=category_name)
        button.bind(on_press=lambda instance, cb=callback: cb(faction, game_area))
        button_layout.add_widget(button)

    # Кнопка "Вернуться"
    back_button = StyledButton(text="Вернуться")
    back_button.bind(on_press=lambda x: modal.dismiss())

    # Добавляем всё в основное окно
    window.add_widget(title)
    scroll_view = ScrollView(size_hint=(1, 0.7))  # Добавляем ScrollView для кнопок
    scroll_view.add_widget(button_layout)
    window.add_widget(scroll_view)
    window.add_widget(back_button)

    modal.add_widget(window)
    modal.open()


def show_trade_agreement_form(faction, game_area):
    """Окно формы для торгового соглашения"""
    # Список всех фракций
    all_factions = ["Селестия", "Аркадия", "Этерия", "Халидон", "Хиперион"]
    # Исключаем текущую фракцию
    available_factions = [f for f in all_factions if f != faction]

    # Создаем контент для Popup
    content = BoxLayout(orientation='vertical', padding=10, spacing=8)  # Уменьшили отступы и промежутки

    # Заголовок
    title = Label(
        text="Торговое соглашение",
        size_hint=(1, None),
        height=35,  # Уменьшили высоту заголовка
        font_size=16,  # Уменьшили размер шрифта для заголовка
        color=(1, 1, 1, 1),  # Белый цвет текста
        bold=True,
        halign='center'
    )
    content.add_widget(title)

    # Спиннеры и поля ввода
    factions_spinner = Spinner(
        text="С какой фракцией?",
        values=available_factions,
        size_hint=(1, None),
        height=30,  # Уменьшили высоту спиннера
        font_size=12,  # Уменьшили размер шрифта
        background_color=(0.2, 0.6, 1, 1),  # Цвет фона спиннера
        background_normal=''  # Убираем стандартный фон
    )
    content.add_widget(factions_spinner)

    our_resource_spinner = Spinner(
        text="Наш ресурс",
        values=["Рабочие", "Сырье", "Кроны"],
        size_hint=(1, None),
        height=30,
        font_size=12,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(our_resource_spinner)

    their_resource_spinner = Spinner(
        text="Их ресурс",
        values=["Рабочие", "Сырье", "Кроны"],
        size_hint=(1, None),
        height=30,
        font_size=12,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(their_resource_spinner)

    our_percentage_input = TextInput(
        hint_text="Сумма отчислений с нашей стороны",
        multiline=False,
        size_hint=(1, None),
        height=30,  # Уменьшили высоту поля ввода
        font_size=12,  # Уменьшили размер шрифта
        background_color=(0.1, 0.1, 0.1, 1),  # Темный фон
        foreground_color=(1, 1, 1, 1)  # Белый текст
    )
    content.add_widget(our_percentage_input)

    their_percentage_input = TextInput(
        hint_text="Сумма прихода с их стороны",
        multiline=False,
        size_hint=(1, None),
        height=30,
        font_size=12,
        background_color=(0.1, 0.1, 0.1, 1),
        foreground_color=(1, 1, 1, 1)
    )
    content.add_widget(their_percentage_input)

    agreement_summary = TextInput(
        readonly=True,
        multiline=True,
        size_hint=(1, None),
        height=60,  # Уменьшили высоту текстового поля
        font_size=12,
        background_color=(0.1, 0.1, 0.1, 1),
        foreground_color=(1, 1, 1, 1)
    )
    content.add_widget(agreement_summary)

    # Кнопки
    button_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=35, spacing=8)

    generate_button = StyledButton(text="Сформировать условия", size_hint=(1, None), height=30)
    send_button = StyledButton(text="Отправить условия договора", size_hint=(1, None), height=30)
    send_button.opacity = 0  # Скрываем кнопку изначально

    def generate_agreement(instance):
        """Формирование текста соглашения"""
        faction_selected = factions_spinner.text
        our_resource_selected = our_resource_spinner.text
        their_resource_selected = their_resource_spinner.text
        our_percentage = our_percentage_input.text
        their_percentage = their_percentage_input.text

        if faction_selected == "С какой фракцией?":
            agreement_summary.text = "Пожалуйста, выберите фракцию для соглашения."
            return
        if not our_percentage.isdigit() or not their_percentage.isdigit():
            agreement_summary.text = "Укажите желаемую сумму."
            return

        # Формируем текст для отображения
        agreement_summary.text = (
            f"Торговое соглашение с фракцией {faction_selected}.\n"
            f"Инициатор: {faction}.\n"
            f"Наш ресурс: {our_resource_selected}.\n"
            f"Их ресурс: {their_resource_selected}.\n"
            f"Мы отправляем союзнику: {our_percentage} единиц.\n"
            f"Мы получаем от союзника: {their_percentage} единиц."
        )
        # Показываем кнопку отправки условий договора
        send_button.opacity = 1

    def send_agreement(instance):
        """Отправка условий договора в файл"""
        faction_selected = factions_spinner.text
        if faction_selected == "С какой фракцией?":
            return

        # Собираем данные в словарь
        agreement_data = {
            "initiator": faction,  # Добавляем инициатора
            "target_faction": faction_selected,
            "initiator_type_resource": our_resource_spinner.text,
            "target_type_resource": their_resource_spinner.text,
            "initiator_summ_resource": our_percentage_input.text,
            "target_summ_resource": their_percentage_input.text
        }

        # Генерируем путь к файлу
        filename_friend = transform_filename(f'files/config/status/trade_dogovor/{faction_selected}.json')
        filename_i_am = transform_filename(f'files/config/status/trade_dogovor/{faction}.json')

        # Сохраняем данные в файл JSON
        with open(filename_friend, 'w', encoding='utf-8') as file:
            json.dump(agreement_data, file, ensure_ascii=False, indent=4)
        with open(filename_i_am, 'w', encoding='utf-8') as file:
            json.dump(agreement_data, file, ensure_ascii=False, indent=4)

        # Подтверждение отправки
        agreement_summary.text = (f"Условия договора отправлены фракции {faction_selected}. \n"
                                  f"Если его примут поставки придут через 1 ход")

    generate_button.bind(on_press=generate_agreement)
    send_button.bind(on_press=send_agreement)

    button_layout.add_widget(generate_button)
    button_layout.add_widget(send_button)
    content.add_widget(button_layout)

    # Кнопка "Назад"
    back_button = StyledButton(text="Назад", size_hint=(1, None), height=30)
    back_button.bind(on_press=lambda x: popup.dismiss())
    content.add_widget(back_button)

    # Создаем Popup с увеличенными размерами
    popup = Popup(
        title="Торговое соглашение",
        content=content,
        size_hint=(0.7, 0.8),  # Увеличили размер окна
        auto_dismiss=False
    )

    # Открываем Popup
    popup.open()


def show_cultural_exchange_form(faction, game_area):
    """Окно формы для договора о культурном обмене"""
    all_factions = ["Селестия", "Аркадия", "Этерия", "Халидон", "Хиперион"]
    available_factions = [f for f in all_factions if f != faction]

    content = BoxLayout(orientation='vertical', padding=10, spacing=8)

    title = Label(
        text="Договор о культурном обмене",
        size_hint=(1, None),
        height=35,
        font_size=16,
        color=(1, 1, 1, 1),
        bold=True,
        halign='center'
    )
    content.add_widget(title)

    factions_spinner = Spinner(
        text="С какой фракцией?",
        values=available_factions,
        size_hint=(1, None),
        height=30,
        font_size=12,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(factions_spinner)

    description_label = Label(
        text="Обмен культурными ценностями повышает доверие между фракциями.(+7% к отношениям).\nСтоимость 10 000 000 крон",
        size_hint=(1, None),
        height=60,
        font_size=12,
        color=(1, 1, 1, 1),
        halign='center'
    )
    description_label.bind(size=description_label.setter('text_size'))
    content.add_widget(description_label)

    message_label = Label(
        text="",
        size_hint=(1, None),
        height=30,
        font_size=12,
        color=(0, 1, 0, 1),
        halign='center'
    )
    content.add_widget(message_label)

    def show_warning():
        """Выводит предупреждение, если фракция не выбрана"""
        message_label.text = "Пожалуйста, выберите фракцию!"
        message_label.color = (1, 0, 0, 1)  # Красный цвет

    def send_proposal(instance):
        """Отправляет предложение, если фракция выбрана и хватает денег"""
        if factions_spinner.text == "С какой фракцией?":
            show_warning()
            return

        # Проверяем, хватает ли денег
        cash_file = 'files/config/resources/cash.json'
        if os.path.exists(cash_file):
            try:
                with open(cash_file, 'r') as file:
                    resources_data = json.load(file)
                    money = resources_data.get('Кроны', 0)

                if money < 10_000_000:
                    message_label.text = "Недостаточно крон для заключения договора!"
                    message_label.color = (1, 0, 0, 1)  # Красный цвет
                    return

                # Списываем деньги
                resources_data['Кроны'] -= 10_000_000
                with open(cash_file, 'w') as file:
                    json.dump(resources_data, file, indent=4)

                send_cultural_exchange_proposal(factions_spinner.text, faction)
                message_label.text = f"Договор заключён с {factions_spinner.text}! (-10 млн крон)"
                message_label.color = (0, 1, 0, 1)  # Зеленый цвет

            except json.JSONDecodeError:
                message_label.text = "Ошибка чтения файла ресурсов!"
                message_label.color = (1, 0, 0, 1)  # Красный цвет
        else:
            message_label.text = "Файл ресурсов не найден!"
            message_label.color = (1, 0, 0, 1)  # Красный цвет

    button_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=35, spacing=8)

    send_button = StyledButton(text="Отправить предложение", size_hint=(0.5, None), height=30)
    send_button.bind(on_press=send_proposal)

    back_button = StyledButton(text="Назад", size_hint=(0.5, None), height=30)
    back_button.bind(on_press=lambda x: popup.dismiss())

    button_layout.add_widget(send_button)
    button_layout.add_widget(back_button)
    content.add_widget(button_layout)

    popup = Popup(
        title="Культурный обмен",
        content=content,
        size_hint=(0.7, 0.5),
        auto_dismiss=False
    )

    popup.open()


def send_cultural_exchange_proposal(fraction, target_faction):
    # Преобразуем путь к файлу
    source_faction = transform_filename(target_faction)
    dogovor_path_target = transform_filename(rf'files\config\status\dipforce\{fraction}\{source_faction}.json')
    dogovor_path_my_fraction = transform_filename(rf'files\config\status\dipforce\{source_faction}\{fraction}.json')
    # Создаем директорию, если она не существует
    os.makedirs(os.path.dirname(dogovor_path_target), exist_ok=True)
    os.makedirs(os.path.dirname(dogovor_path_my_fraction), exist_ok=True)

    # Данные для записи в JSON
    data = {
        "Source_faction": target_faction,
        "Target_faction": fraction
    }
    # Записываем данные в JSON-файл
    with open(dogovor_path_my_fraction, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # Записываем данные в JSON-файл
    with open(dogovor_path_target, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(
        f"Договор о культурном обмене между {fraction} и {target_faction} успешно записан в {dogovor_path_target}")
    manage_relations(source_faction)


def manage_relations(faction):
    """Управление отношениями только для фракций, заключивших дипломатическое соглашение"""
    # Проверяем, есть ли фракция в translation_dict
    ru_name_fraction = reverse_translation_dict.get(faction, faction)
    # Формируем путь к директории фракции
    relations_path = r'files\config\status\dipforce'
    faction_dir_path = os.path.join(relations_path, faction)

    # Проверяем существование директории
    if not os.path.exists(faction_dir_path):
        print(f"Путь {faction_dir_path} не существует.")
        return

    # Загружаем текущие отношения
    relations_data = load_relations()
    if ru_name_fraction not in relations_data["relations"]:
        print(f"Отношения для фракции {ru_name_fraction} не найдены.")
        return

    # Перебираем файлы в директории, обрабатываем только тех, с кем заключены соглашения
    for filename in os.listdir(faction_dir_path):
        if filename.endswith(".json"):
            faction_name_en = filename.replace('.json', '')
            faction_name_ru = reverse_translation_dict.get(faction_name_en, faction_name_en)

            # Проверяем, есть ли дипломатическое соглашение
            if faction_name_ru in relations_data["relations"][ru_name_fraction]:
                current_value_self = relations_data["relations"][ru_name_fraction][faction_name_ru]
                current_value_other = relations_data["relations"][faction_name_ru][ru_name_fraction]
                relations_data["relations"][ru_name_fraction][faction_name_ru] = min(current_value_self + 7, 100)
                relations_data["relations"][faction_name_ru][ru_name_fraction] = min(current_value_other + 7, 100)

            # Удаляем обработанный файл (чтобы это изменение было одноразовым)
            os.remove(os.path.join(faction_dir_path, filename))

    # Сохраняем обновленные данные
    save_relations(relations_data)


def load_relations():
    relations_file = r'files\config\status\dipforce\relations.json'
    """Загружаем текущие отношения из файла relations.json"""
    try:
        with open(relations_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл relations.json не найден. Создаем новый.")
        return {"relations": {}}


def save_relations(relations_data):
    """Сохраняем обновленные отношения в файл relations.json"""
    relations_file = r'files\config\status\dipforce\relations.json'
    try:
        with open(relations_file, "w", encoding="utf-8") as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=4)
    except PermissionError:
        print("Ошибка доступа к файлу relations.json. Проверьте права доступа.")


def show_diplomatic_data_form(faction, game_area):
    """Заглушка: Предоставление дип. данных"""
    pass


def show_alliance_form(faction, game_area):
    """Заглушка: Заключение альянса"""
    pass


def show_declare_war_form(faction, game_area):
    """Заглушка: Объявление войны"""
    pass


def start_politic_mode(faction, game_area):
    """Инициализация политического режима для выбранной фракции"""

    # Кнопки для управления политикой
    politics_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), pos_hint={'x': 0, 'y': 0})

    negotiate_btn = Button(text="Новый договор", size_hint_x=0.33, size_hint_y=None, height=50)
    form_alliance_btn = Button(text="Управление союзниками", size_hint_x=0.33, size_hint_y=None, height=50)
    declare_war_btn = Button(text="Переговоры", size_hint_x=0.33, size_hint_y=None, height=50)

    # Привязываем функцию для кнопки "Новый договор"
    negotiate_btn.bind(on_press=lambda x: show_new_agreement_window(faction, game_area))

    # Добавляем кнопки в layout
    politics_layout.add_widget(negotiate_btn)
    politics_layout.add_widget(form_alliance_btn)
    politics_layout.add_widget(declare_war_btn)

    # Добавляем layout с кнопками в нижнюю часть экрана
    game_area.add_widget(politics_layout)


def switch_to_army(faction, game_area):
    import army  # Импортируем здесь, чтобы избежать циклического импорта
    game_area.clear_widgets()
    army.start_army_mode(faction, game_area)


def switch_to_economy(faction, game_area):
    import economic  # Импортируем здесь, чтобы избежать циклического импорта
    game_area.clear_widgets()
    economic.start_economy_mode(faction, game_area)


def switch_to_politics(faction, game_area):
    import politic  # Импортируем здесь, чтобы избежать циклического импорта
    game_area.clear_widgets()
    politic.start_politic_mode(faction, game_area)
