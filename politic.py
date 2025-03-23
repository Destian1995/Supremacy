import os

from kivy.animation import Animation
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanelItem, TabbedPanel
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

# Словарь для перевода названий файлов в русскоязычные названия фракций
faction_names = {
    "arkadia_in_city": "Аркадия",
    "celestia_in_city": "Селестия",
    "eteria_in_city": "Этерия",
    "giperion_in_city": "Хиперион",
    "halidon_in_city": "Халидон"
}

faction_names_build = {
    "arkadia_buildings_city": "Аркадия",
    "celestia_buildings_city": "Селестия",
    "eteria_buildings_city": "Этерия",
    "giperion_buildings_city": "Хиперион",
    "halidon_buildings_city": "Халидон"
}

def transform_filename(file_path):
    path_parts = file_path.split('/')
    for i, part in enumerate(path_parts):
        for ru_name, en_name in translation_dict.items():
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)
    return '/'.join(path_parts)


reverse_translation_dict = {v: k for k, v in translation_dict.items()}


# Функция для расчета базового размера шрифта
def calculate_font_size():
    """Рассчитывает базовый размер шрифта на основе высоты окна."""
    base_height = 720  # Базовая высота окна для нормального размера шрифта
    default_font_size = 16  # Базовый размер шрифта
    scale_factor = Window.height / base_height  # Коэффициент масштабирования
    return max(8, int(default_font_size * scale_factor))  # Минимальный размер шрифта — 8


# Кастомная кнопка с анимациями и эффектами
class StyledButton(ButtonBehavior, BoxLayout):
    def __init__(self, text, font_size, button_color, text_color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = font_size * 3  # Высота кнопки зависит от размера шрифта
        self.padding = [font_size // 2, font_size // 4]  # Отступы внутри кнопки
        self.normal_color = button_color
        self.hover_color = [c * 0.9 for c in button_color]  # Темнее при наведении
        self.pressed_color = [c * 0.8 for c in button_color]  # Еще темнее при нажатии
        self.current_color = self.normal_color

        with self.canvas.before:
            self.color = Color(*self.current_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[font_size // 2])

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.label = Label(
            text=text,
            font_size=font_size * 1.2,
            color=text_color,
            bold=True,
            halign='center',
            valign='middle'
        )
        self.label.bind(size=self.label.setter('text_size'))
        self.add_widget(self.label)

        self.bind(on_press=self.on_press_effect, on_release=self.on_release_effect)
        self.bind(on_touch_move=self.on_hover, on_touch_up=self.on_leave)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press_effect(self, instance):
        """Эффект затемнения при нажатии"""
        anim = Animation(current_color=self.pressed_color, duration=0.1)
        anim.start(self)
        self.update_color()

    def on_release_effect(self, instance):
        """Возвращаем цвет после нажатия"""
        anim = Animation(current_color=self.normal_color, duration=0.1)
        anim.start(self)
        self.update_color()

    def on_hover(self, instance, touch):
        """Эффект при наведении"""
        if self.collide_point(*touch.pos):
            anim = Animation(current_color=self.hover_color, duration=0.1)
            anim.start(self)
            self.update_color()

    def on_leave(self, instance, touch):
        """Возвращаем цвет, если курсор ушел с кнопки"""
        if not self.collide_point(*touch.pos):
            anim = Animation(current_color=self.normal_color, duration=0.1)
            anim.start(self)
            self.update_color()

    def update_color(self):
        """Обновляет цвет фона"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.current_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[self.height // 4])


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

    # Рассчитываем базовый размер шрифта
    font_size = calculate_font_size()

    # Цвета для кнопок
    default_button_color = (0.2, 0.6, 1, 1)  # Синий цвет
    default_text_color = (1, 1, 1, 1)  # Белый текст

    # Создаем кнопки для каждой категории
    categories = [
        ("Торговое соглашение", show_trade_agreement_form),
        ("Договор об культурном обмене", show_cultural_exchange_form),
        ("Заключение мира", show_peace_form),
        ("Заключение альянса", show_alliance_form),
        ("Объявление войны", show_declare_war_form),
    ]

    for category_name, callback in categories:
        button = StyledButton(
            text=category_name,
            font_size=font_size * 1.2,
            button_color=default_button_color,
            text_color=default_text_color
        )
        button.bind(on_press=lambda instance, cb=callback: cb(faction, game_area))
        button_layout.add_widget(button)

    # Кнопка "Вернуться"
    back_button = StyledButton(
        text="Вернуться",
        font_size=font_size * 1.2,
        button_color=(0.8, 0.2, 0.2, 1),  # Красный цвет
        text_color=default_text_color
    )
    back_button.bind(on_press=lambda x: modal.dismiss())

    # Добавляем всё в основное окно
    window.add_widget(title)
    scroll_view = ScrollView(size_hint=(1, 0.7))  # Добавляем ScrollView для кнопок
    scroll_view.add_widget(button_layout)
    window.add_widget(scroll_view)
    window.add_widget(back_button)

    modal.add_widget(window)
    modal.open()


# Обновленная функция для формы торгового соглашения
# Обновленная функция для создания формы торгового соглашения
def show_trade_agreement_form(faction, game_area):
    """Окно формы для торгового соглашения"""
    # Рассчитываем базовый размер шрифта
    font_size = calculate_font_size()
    button_height = font_size * 3  # Увеличиваем высоту кнопок (в 3 раза от размера шрифта)
    input_height = font_size * 2.5  # Увеличиваем высоту полей ввода (в 2.5 раза от размера шрифта)
    padding = font_size // 2  # Отступы
    spacing = font_size // 4  # Промежутки между элементами

    # Список всех фракций
    all_factions = ["Селестия", "Аркадия", "Этерия", "Халидон", "Хиперион"]
    available_factions = [f for f in all_factions if f != faction]

    # Создаем контент для Popup
    content = BoxLayout(
        orientation='vertical',
        padding=padding,
        spacing=spacing
    )

    # Заголовок
    title = Label(
        text="Торговое соглашение",
        size_hint=(1, None),
        height=button_height,
        font_size=font_size * 1.5,  # Заголовок крупнее
        color=(1, 1, 1, 1),
        bold=True,
        halign='center'
    )
    content.add_widget(title)

    # Спиннеры и поля ввода
    factions_spinner = Spinner(
        text="С какой фракцией?",
        values=available_factions,
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(factions_spinner)

    our_resource_spinner = Spinner(
        text="Наш ресурс",
        values=["Рабочие", "Сырье", "Кроны"],
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(our_resource_spinner)

    their_resource_spinner = Spinner(
        text="Их ресурс",
        values=["Рабочие", "Сырье", "Кроны"],
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(their_resource_spinner)

    our_percentage_input = TextInput(
        hint_text="Сумма отчислений с нашей стороны",
        multiline=False,
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.1, 0.1, 0.1, 1),
        foreground_color=(1, 1, 1, 1)
    )
    content.add_widget(our_percentage_input)

    their_percentage_input = TextInput(
        hint_text="Сумма прихода с их стороны",
        multiline=False,
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.1, 0.1, 0.1, 1),
        foreground_color=(1, 1, 1, 1)
    )
    content.add_widget(their_percentage_input)

    agreement_summary = TextInput(
        readonly=True,
        multiline=True,
        size_hint=(1, None),
        height=button_height * 2,
        font_size=font_size,
        background_color=(0.1, 0.1, 0.1, 1),
        foreground_color=(1, 1, 1, 1)
    )
    content.add_widget(agreement_summary)

    # Кнопки
    button_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=button_height,
        spacing=font_size // 2
    )

    generate_button = Button(
        text="Сформировать условия",
        size_hint=(1, None),
        height=button_height,
        font_size=font_size * 1.2  # Увеличиваем размер текста на кнопках
    )

    send_button = Button(
        text="Отправить условия договора",
        size_hint=(1, None),
        height=button_height,
        font_size=font_size * 1.2,
        opacity=0
    )

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

        if our_resource_selected == "Наш ресурс" or their_resource_selected == "Их ресурс":
            agreement_summary.text = "Пожалуйста, выберите ресурсы для обмена."
            return

        if not our_percentage.isdigit() or not their_percentage.isdigit():
            agreement_summary.text = "Укажите желаемую сумму."
            return

        agreement_summary.text = (
            f"Торговое соглашение с фракцией {faction_selected}.\n"
            f"Инициатор: {faction}.\n"
            f"Наш ресурс: {our_resource_selected}.\n"
            f"Их ресурс: {their_resource_selected}.\n"
            f"Мы отправляем союзнику: {our_percentage} единиц.\n"
            f"Мы получаем от союзника: {their_percentage} единиц."
        )
        send_button.opacity = 1

    def send_agreement(instance):
        """Отправка условий договора в файл"""
        faction_selected = factions_spinner.text
        if faction_selected == "С какой фракцией?":
            return

        agreement_data = {
            "initiator": faction,
            "target_faction": faction_selected,
            "initiator_type_resource": our_resource_spinner.text,
            "target_type_resource": their_resource_spinner.text,
            "initiator_summ_resource": our_percentage_input.text,
            "target_summ_resource": their_percentage_input.text
        }

        filename_friend = transform_filename(f'files/config/status/trade_dogovor/{faction_selected}.json')
        filename_i_am = transform_filename(f'files/config/status/trade_dogovor/{faction}.json')

        with open(filename_friend, 'w', encoding='utf-8') as file:
            json.dump(agreement_data, file, ensure_ascii=False, indent=4)
        with open(filename_i_am, 'w', encoding='utf-8') as file:
            json.dump(agreement_data, file, ensure_ascii=False, indent=4)

        agreement_summary.text = (f"Условия договора отправлены фракции {faction_selected}. \n"
                                  f"Если его примут поставки придут через 1 ход")

    generate_button.bind(on_press=generate_agreement)
    send_button.bind(on_press=send_agreement)
    button_layout.add_widget(generate_button)
    button_layout.add_widget(send_button)
    content.add_widget(button_layout)

    back_button = Button(
        text="Назад",
        size_hint=(1, None),
        height=button_height,
        font_size=font_size * 1.2
    )
    back_button.bind(on_press=lambda x: popup.dismiss())
    content.add_widget(back_button)

    popup = Popup(
        title="Торговое соглашение",
        content=content,
        size_hint=(0.7, 0.8),
        auto_dismiss=False
    )
    popup.open()


# Обработчик изменения размера окна
def on_window_resize(instance, width, height):
    """Обновляет интерфейс при изменении размера окна."""
    global font_size
    font_size = calculate_font_size()


def show_cultural_exchange_form(faction, game_area):
    """Окно формы для договора о культурном обмене"""
    # Рассчитываем базовый размер шрифта
    font_size = calculate_font_size()
    button_height = font_size * 3  # Высота кнопок
    input_height = font_size * 2.5  # Высота полей ввода
    padding = font_size // 2  # Отступы
    spacing = font_size // 4  # Промежутки между элементами

    # Чтение данных из файла diplomaties.json
    file_path = os.path.join("files", "config", "status", "diplomaties.json")
    if not os.path.exists(file_path):
        print("Файл diplomaties.json не найден.")
        return

    with open(file_path, 'r', encoding='utf-8') as file:
        diplomaties = json.load(file)

    # Проверка, существует ли указанная фракция
    if faction not in diplomaties:
        print(f"Ошибка: Фракция '{faction}' не найдена.")
        return

    # Получение текущих отношений фракции
    relations = diplomaties[faction]["отношения"]

    # Список всех фракций
    all_factions = ["Селестия", "Аркадия", "Этерия", "Халидон", "Хиперион"]
    available_factions = [f for f in all_factions if f != faction]

    # Создаем контент для Popup
    content = BoxLayout(
        orientation='vertical',
        padding=padding,
        spacing=spacing
    )

    # Заголовок
    title = Label(
        text="Договор о культурном обмене",
        size_hint=(1, None),
        height=button_height,
        font_size=font_size * 1.5,
        color=(1, 1, 1, 1),
        bold=True,
        halign='center'
    )
    content.add_widget(title)

    # Спиннер для выбора фракции
    factions_spinner = Spinner(
        text="С какой фракцией?",
        values=available_factions,
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(factions_spinner)

    # Описание
    description_label = Label(
        text="Обмен культурными ценностями повышает доверие между фракциями (+7% к отношениям).\nСтоимость: 10 000 000 крон",
        size_hint=(1, None),
        height=font_size * 4,  # Высота зависит от количества строк
        font_size=font_size,
        color=(1, 1, 1, 1),
        halign='center'
    )
    description_label.bind(size=description_label.setter('text_size'))
    content.add_widget(description_label)

    # Сообщения пользователю
    message_label = Label(
        text="",
        size_hint=(1, None),
        height=font_size * 2,
        font_size=font_size,
        color=(0, 1, 0, 1),
        halign='center'
    )
    content.add_widget(message_label)

    # Функция для вывода предупреждений
    def show_warning(text, color=(1, 0, 0, 1)):
        """Выводит предупреждение."""
        message_label.text = text
        message_label.color = color

    # Функция для отправки предложения
    def send_proposal(instance):
        """Отправляет предложение, если фракция выбрана и хватает денег"""
        target_faction = factions_spinner.text
        if target_faction == "С какой фракцией?":
            show_warning("Пожалуйста, выберите фракцию!")
            return

        # Проверяем состояние отношений
        if relations.get(target_faction) == "война":
            show_warning(f"Невозможно отправить предложение: идет война с {target_faction}!")
            return

        # Проверяем, хватает ли денег
        cash_file = 'files/config/resources/cash.json'
        if os.path.exists(cash_file):
            try:
                with open(cash_file, 'r') as file:
                    resources_data = json.load(file)
                money = resources_data.get('Кроны', 0)
                if money < 10_000_000:
                    show_warning("Недостаточно крон для заключения договора!")
                    return
                # Списываем деньги
                resources_data['Кроны'] -= 10_000_000
                with open(cash_file, 'w') as file:
                    json.dump(resources_data, file, indent=4)
                # Отправляем предложение
                send_cultural_exchange_proposal(target_faction, faction)
                show_warning(f"Договор заключён с {target_faction}! (-10 млн крон)", color=(0, 1, 0, 1))
            except json.JSONDecodeError:
                show_warning("Ошибка чтения файла ресурсов!")
        else:
            show_warning("Файл ресурсов не найден!")

    # Кнопки
    button_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=button_height,
        spacing=font_size // 2
    )

    # Цвета для кнопок
    default_button_color = (0.2, 0.6, 1, 1)  # Синий цвет
    default_text_color = (1, 1, 1, 1)  # Белый текст
    send_button = Button(
        text="Отправить предложение",
        font_size=font_size,
        background_color=default_button_color,
        color=default_text_color,
        size_hint=(0.5, None),
        height=button_height
    )
    send_button.bind(on_press=send_proposal)
    back_button = Button(
        text="Назад",
        font_size=font_size,
        background_color=(0.8, 0.2, 0.2, 1),  # Красный цвет
        color=default_text_color,
        size_hint=(0.5, None),
        height=button_height
    )

    # Создаем и открываем Popup
    popup = Popup(
        title="Культурный обмен",
        content=content,
        size_hint=(0.7, 0.5),
        auto_dismiss=False
    )
    back_button.bind(on_press=popup.dismiss)

    button_layout.add_widget(send_button)
    button_layout.add_widget(back_button)
    content.add_widget(button_layout)

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


def calculate_peace_army_points(faction_file):
    """Вычисляет общие очки армии для указанной фракции."""
    # Коэффициенты для классов юнитов
    class_coefficients = {
        '1': 1.1,
        '2': 1.4,
        '3': 1.9,
        '4': 2.8
    }

    total_points = 0

    if not os.path.exists(faction_file):
        print(f"Файл {faction_file} не найден.")
        return total_points

    try:
        with open(faction_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for city_data in data.values():
            for city_info in city_data:
                for unit in city_info.get("units", []):
                    stats = unit.get("units_stats", {})
                    unit_class = str(stats.get("Класс юнита", "1"))
                    damage = stats.get("Урон", 0)
                    defense = stats.get("Защита", 0)
                    endurance = stats.get("Живучесть", 0)
                    coefficient = class_coefficients.get(unit_class, 1.0)

                    # Формула для вычисления очков юнита
                    unit_points = defense + endurance + (damage * coefficient)
                    total_points += unit_points * unit.get("unit_count", 1)

    except json.JSONDecodeError:
        print(f"Ошибка чтения файла {faction_file}.")

    return total_points


def show_peace_form(player_faction, game_area):
    """Окно формы для предложения о заключении мира."""
    # Рассчитываем базовый размер шрифта
    font_size = calculate_font_size()
    button_height = font_size * 3  # Высота кнопок
    input_height = font_size * 2.5  # Высота полей ввода
    padding = font_size // 2  # Отступы
    spacing = font_size // 4  # Промежутки между элементами

    # Чтение данных из файла diplomaties.json
    diplomaties_file_path = os.path.join("files", "config", "status", "diplomaties.json")
    if not os.path.exists(diplomaties_file_path):
        print("Файл diplomaties.json не найден.")
        return

    with open(diplomaties_file_path, 'r', encoding='utf-8') as file:
        diplomaties = json.load(file)

    # Проверка, существует ли указанная фракция
    if player_faction not in diplomaties:
        print(f"Ошибка: Фракция '{player_faction}' не найдена.")
        return

    # Получение текущих отношений фракции
    relations = diplomaties[player_faction]["отношения"]

    # Список всех фракций
    all_factions = ["Селестия", "Аркадия", "Этерия", "Халидон", "Хиперион"]
    available_factions = [f for f, status in relations.items() if status == "война"]

    # Если нет доступных фракций для заключения мира
    if not available_factions:
        # Выводим сообщение "Мы сейчас ни с кем не воюем"
        popup_content = BoxLayout(
            orientation='vertical',
            padding=padding,
            spacing=spacing
        )
        message_label = Label(
            text="Мы сейчас ни с кем не воюем",
            size_hint=(1, None),
            height=font_size * 2,
            font_size=font_size,
            color=(0, 1, 0, 1),  # Зеленый цвет
            halign='center'
        )
        popup_content.add_widget(message_label)

        close_button = Button(
            text="Закрыть",
            font_size=font_size,
            background_color=(0.8, 0.2, 0.2, 1),  # Красный цвет
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=button_height
        )

        popup = Popup(
            title="Заключение мира",
            content=popup_content,
            size_hint=(0.7, 0.3),
            auto_dismiss=False
        )
        close_button.bind(on_press=popup.dismiss)
        popup_content.add_widget(close_button)
        popup.open()
        return

    # Создаем контент для Popup
    content = BoxLayout(
        orientation='vertical',
        padding=padding,
        spacing=spacing
    )

    # Заголовок
    title = Label(
        text="Предложение о заключении мира",
        size_hint=(1, None),
        height=button_height,
        font_size=font_size * 1.5,
        color=(1, 1, 1, 1),
        bold=True,
        halign='center'
    )
    content.add_widget(title)

    # Спиннер для выбора фракции
    factions_spinner = Spinner(
        text="С какой фракцией?",
        values=available_factions,
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(factions_spinner)

    # Сообщения пользователю
    message_label = Label(
        text="",
        size_hint=(1, None),
        height=font_size * 2,
        font_size=font_size,
        color=(0, 1, 0, 1),  # Зеленый цвет по умолчанию
        halign='center'
    )
    content.add_widget(message_label)

    # Функция для вывода предупреждений
    def show_warning(text, color=(1, 0, 0, 1)):
        """Выводит предупреждение с указанным цветом."""
        message_label.text = text
        message_label.color = color

    # Функция для отправки предложения
    def send_proposal(instance):
        """Отправляет предложение о заключении мира."""
        target_faction = factions_spinner.text
        if target_faction == "С какой фракцией?":
            show_warning("Пожалуйста, выберите фракцию!", color=(1, 0, 0, 1))  # Красный цвет
            return

        # Преобразование русских названий в английские
        player_english_name = translation_dict.get(player_faction)
        enemy_english_name = translation_dict.get(target_faction)

        if not player_english_name or not enemy_english_name:
            show_warning("Ошибка при определении фракций.", color=(1, 0, 0, 1))  # Красный цвет
            return

        # Путь к файлам армий
        player_file = os.path.join("files", "config", "manage_ii", f"{player_english_name}_in_city.json")
        enemy_file = os.path.join("files", "config", "manage_ii", f"{enemy_english_name}_in_city.json")

        # Вычисление очков армии
        player_points = calculate_peace_army_points(player_file)
        enemy_points = calculate_peace_army_points(enemy_file)

        if player_points == 0 or enemy_points == 0:
            show_warning("Ошибка при вычислении очков армии.", color=(1, 0, 0, 1))  # Красный цвет
            return

        # Вычисление процента превосходства
        if player_points > enemy_points:
            superiority_percentage = ((player_points - enemy_points) / enemy_points) * 100
            if superiority_percentage >= 70:
                response = "А смысл нам сопротивляться? Все приплыли.."
            elif 30 <= superiority_percentage < 70:
                response = "Нихера себе повоевали...."
            elif 20 <= superiority_percentage < 30:
                response = "Что там случилось...такое.."
            elif 10 <= superiority_percentage < 20:
                response = "По-моему мы что-то упустили"
            else:
                response = "В следующий раз мы будем лучше готовы"
            # Меняем статус на "мир"
            diplomaties[player_faction]["отношения"][target_faction] = "нейтралитет"
            diplomaties[target_faction]["отношения"][player_faction] = "нейтралитет"
            with open(diplomaties_file_path, 'w', encoding='utf-8') as file:
                json.dump(diplomaties, file, ensure_ascii=False, indent=4)
            show_warning(response, color=(0, 1, 0, 1))  # Зеленый цвет
        elif player_points < enemy_points:
            inferiority_percentage = ((enemy_points - player_points) / player_points) * 100
            if inferiority_percentage <= 15:
                response = "Почти то что надо, подкинь пару крон и договоримся"
                show_warning(response, color=(1, 1, 0, 1))  # Желтый цвет
            else:
                response = "Мы еще не закончили Вас бить"
                show_warning(response, color=(1, 0, 0, 1))  # Красный цвет
        else:
            response = "Сейчас передохнем и в рыло дадим"
            show_warning(response, color=(1, 0, 0, 1))  # Красный цвет

    # Кнопки
    button_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=button_height,
        spacing=font_size // 2
    )

    # Цвета для кнопок
    default_button_color = (0.2, 0.6, 1, 1)  # Синий цвет
    default_text_color = (1, 1, 1, 1)  # Белый текст
    send_button = Button(
        text="Отправить предложение",
        font_size=font_size,
        background_color=default_button_color,
        color=default_text_color,
        size_hint=(0.5, None),
        height=button_height
    )
    send_button.bind(on_press=send_proposal)
    back_button = Button(
        text="Назад",
        font_size=font_size,
        background_color=(0.8, 0.2, 0.2, 1),  # Красный цвет
        color=default_text_color,
        size_hint=(0.5, None),
        height=button_height
    )

    # Создаем и открываем Popup
    popup = Popup(
        title="Заключение мира",
        content=content,
        size_hint=(0.7, 0.5),
        auto_dismiss=False
    )
    back_button.bind(on_press=popup.dismiss)

    button_layout.add_widget(send_button)
    button_layout.add_widget(back_button)
    content.add_widget(button_layout)

    popup.open()


def show_alliance_form(faction, game_area):
    """Окно формы для предложения о создании альянса."""
    # Рассчитываем базовый размер шрифта
    font_size = calculate_font_size()
    button_height = font_size * 3  # Высота кнопок
    input_height = font_size * 2.5  # Высота полей ввода
    padding = font_size // 2  # Отступы
    spacing = font_size // 4  # Промежутки между элементами

    # Чтение данных из файла diplomaties.json
    diplomaties_file_path = os.path.join("files", "config", "status", "diplomaties.json")
    if not os.path.exists(diplomaties_file_path):
        print("Файл diplomaties.json не найден.")
        return

    with open(diplomaties_file_path, 'r', encoding='utf-8') as file:
        diplomaties = json.load(file)

    # Чтение данных из файла relations.json
    relations_file_path = os.path.join("files", "config", "status", "dipforce", "relations.json")
    if not os.path.exists(relations_file_path):
        print("Файл relations.json не найден.")
        return

    with open(relations_file_path, 'r', encoding='utf-8') as file:
        relations_data = json.load(file)

    # Проверка, существует ли указанная фракция
    if faction not in diplomaties or faction not in relations_data["relations"]:
        print(f"Ошибка: Фракция '{faction}' не найдена.")
        return

    # Получение текущих отношений фракции
    relations = relations_data["relations"][faction]

    # Список всех фракций
    all_factions = ["Селестия", "Аркадия", "Этерия", "Халидон", "Хиперион"]
    available_factions = [f for f in all_factions if f != faction]

    # Создаем контент для Popup
    content = BoxLayout(
        orientation='vertical',
        padding=padding,
        spacing=spacing
    )

    # Заголовок
    title = Label(
        text="Предложение о создании альянса",
        size_hint=(1, None),
        height=button_height,
        font_size=font_size * 1.5,
        color=(1, 1, 1, 1),
        bold=True,
        halign='center'
    )
    content.add_widget(title)

    # Спиннер для выбора фракции
    factions_spinner = Spinner(
        text="С какой фракцией?",
        values=available_factions,
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(factions_spinner)

    # Описание
    description_label = Label(
        text="Создание альянса возможно только при высоком уровне доверия (>90).\nУровень отношений влияет на возможность заключения союза.",
        size_hint=(1, None),
        height=font_size * 4,  # Высота зависит от количества строк
        font_size=font_size,
        color=(1, 1, 1, 1),
        halign='center'
    )
    description_label.bind(size=description_label.setter('text_size'))
    content.add_widget(description_label)

    # Сообщения пользователю
    message_label = Label(
        text="",
        size_hint=(1, None),
        height=font_size * 2,
        font_size=font_size,
        color=(0, 1, 0, 1),
        halign='center'
    )
    content.add_widget(message_label)

    # Функция для вывода предупреждений
    def show_warning(text, color=(1, 0, 0, 1)):
        """Выводит предупреждение."""
        message_label.text = text
        message_label.color = color

    # Функция для отправки предложения
    def send_proposal(instance):
        """Отправляет предложение о создании альянса."""
        target_faction = factions_spinner.text
        if target_faction == "С какой фракцией?":
            show_warning("Пожалуйста, выберите фракцию!")
            return

        # Проверяем уровень отношений
        relation_level = relations.get(target_faction, 0)

        if relation_level >= 90:
            # Меняем статус отношений на "союз"
            diplomaties[faction]["отношения"][target_faction] = "союз"
            diplomaties[target_faction]["отношения"][faction] = "союз"

            # Сохраняем изменения в файл diplomaties.json
            with open(diplomaties_file_path, 'w', encoding='utf-8') as file:
                json.dump(diplomaties, file, ensure_ascii=False, indent=4)

            show_warning("Пусть наши враги боятся нас! Светлого неба!", color=(0, 1, 0, 1))
        elif 75 <= relation_level < 90:
            show_warning("Друг. Мы должны сильнее доверять друг другу, тогда союз будет возможен.")
        elif 50 <= relation_level < 75:
            show_warning("Приятель. Пока сложно о чем-то конкретном говорить, давай лучше поближе узнаем друг друга.")
        elif 30 <= relation_level < 50:
            show_warning("Не сказал бы что в данный момент нас интересуют подобные предложения.")
        elif 15 <= relation_level < 30:
            show_warning("Да я лучше башку в осиное гнездо засуну чем вообще буду Вам отвечать.")
        else:
            show_warning("Вы там еще не сдохли? Ну ничего, мы это исправим.")

    # Кнопки
    button_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=button_height,
        spacing=font_size // 2
    )

    # Цвета для кнопок
    default_button_color = (0.2, 0.6, 1, 1)  # Синий цвет
    default_text_color = (1, 1, 1, 1)  # Белый текст
    send_button = Button(
        text="Отправить предложение",
        font_size=font_size,
        background_color=default_button_color,
        color=default_text_color,
        size_hint=(0.5, None),
        height=button_height
    )
    send_button.bind(on_press=send_proposal)
    back_button = Button(
        text="Назад",
        font_size=font_size,
        background_color=(0.8, 0.2, 0.2, 1),  # Красный цвет
        color=default_text_color,
        size_hint=(0.5, None),
        height=button_height
    )

    # Создаем и открываем Popup
    popup = Popup(
        title="Создание альянса",
        content=content,
        size_hint=(0.7, 0.5),
        auto_dismiss=False
    )
    back_button.bind(on_press=popup.dismiss)

    button_layout.add_widget(send_button)
    button_layout.add_widget(back_button)
    content.add_widget(button_layout)

    popup.open()


def show_declare_war_form(faction, game_area):
    """Окно формы для объявления войны."""
    # Рассчитываем базовый размер шрифта
    font_size = calculate_font_size()
    button_height = font_size * 3  # Высота кнопок
    input_height = font_size * 2.5  # Высота полей ввода
    padding = font_size // 2  # Отступы
    spacing = font_size // 4  # Промежутки между элементами

    # Чтение данных из файла diplomaties.json
    file_path = os.path.join("files", "config", "status", "diplomaties.json")
    if not os.path.exists(file_path):
        print("Файл diplomaties.json не найден.")
        return

    with open(file_path, 'r', encoding='utf-8') as file:
        diplomaties = json.load(file)

    # Проверка, существует ли указанная фракция
    if faction not in diplomaties:
        print(f"Ошибка: Фракция '{faction}' не найдена.")
        return

    # Получение текущих отношений фракции
    relations = diplomaties[faction]["отношения"]

    # Фильтрация стран, которым можно объявить войну (не "война")
    available_targets = [country for country, status in relations.items() if status != "война"]
    if not available_targets:
        print("Нет доступных целей для объявления войны.")
        return

    # Создаем контент для Popup
    content = BoxLayout(
        orientation='vertical',
        padding=padding,
        spacing=spacing
    )

    # Заголовок
    title = Label(
        text="Объявление войны",
        size_hint=(1, None),
        height=button_height,
        font_size=font_size * 1.5,
        color=(1, 1, 1, 1),
        bold=True,
        halign='center'
    )
    content.add_widget(title)

    # Спиннер для выбора фракции
    factions_spinner = Spinner(
        text="Выберите цель",
        values=available_targets,
        size_hint=(1, None),
        height=input_height,
        font_size=font_size,
        background_color=(0.2, 0.6, 1, 1),
        background_normal=''
    )
    content.add_widget(factions_spinner)

    # Сообщения пользователю
    message_label = Label(
        text="",
        size_hint=(1, None),
        height=font_size * 2,
        font_size=font_size,
        color=(0, 1, 0, 1),
        halign='center'
    )
    content.add_widget(message_label)

    # Функция для вывода предупреждений
    def show_warning(text, color=(1, 0, 0, 1)):
        """Выводит предупреждение."""
        message_label.text = text
        message_label.color = color

    # Функция для объявления войны
    def declare_war(instance):
        """Объявляет войну выбранной фракции."""
        target_faction = factions_spinner.text
        if target_faction == "Выберите цель":
            show_warning("Пожалуйста, выберите цель!")
            return

        # Обновление статуса отношений в diplomaties.json
        diplomaties[faction]["отношения"][target_faction] = "война"
        diplomaties[target_faction]["отношения"][faction] = "война"

        # Сохранение изменений в файл diplomaties.json
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(diplomaties, file, ensure_ascii=False, indent=4)

        # Обнуление отношений в relations.json
        reset_relations_between_factions(faction, target_faction)

        # Вывод сообщения об успешном объявлении войны
        show_warning(f"Война объявлена против {target_faction}!", color=(0, 1, 0, 1))

    # Кнопки
    button_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=button_height,
        spacing=font_size // 2
    )

    # Цвета для кнопок
    default_button_color = (0.2, 0.6, 1, 1)  # Синий цвет
    default_text_color = (1, 1, 1, 1)  # Белый текст

    declare_button = Button(
        text="Объявить войну",
        font_size=font_size,
        background_color=default_button_color,
        color=default_text_color,
        size_hint=(0.5, None),
        height=button_height
    )
    declare_button.bind(on_press=declare_war)

    back_button = Button(
        text="Назад",
        font_size=font_size,
        background_color=(0.8, 0.2, 0.2, 1),  # Красный цвет
        color=default_text_color,
        size_hint=(0.5, None),
        height=button_height
    )

    # Создаем и открываем Popup
    popup = Popup(
        title="Объявление войны",
        content=content,
        size_hint=(0.7, 0.5),
        auto_dismiss=False
    )

    # Привязываем кнопку "Назад" к закрытию Popup
    back_button.bind(on_press=popup.dismiss)

    # Добавляем кнопки в макет
    button_layout.add_widget(declare_button)
    button_layout.add_widget(back_button)
    content.add_widget(button_layout)

    # Открываем Popup
    popup.open()


def reset_relations_between_factions(faction, target_faction):
    """
    Обнуляет отношения между двумя фракциями в файле relations.json.

    :param faction: Наша фракция (например, "Хиперион").
    :param target_faction: Целевая фракция (например, "Аркадия").
    """
    # Путь к файлу relations.json
    file_path = os.path.join("files", "config", "status", "dipforce", "relations.json")

    # Проверка существования файла
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл '{file_path}' не найден.")
        return

    # Чтение данных из файла
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            relations_data = json.load(file)
    except json.JSONDecodeError:
        print("Ошибка: Невозможно прочитать файл relations.json.")
        return

    # Проверка наличия ключей в данных
    if "relations" not in relations_data:
        print("Ошибка: В файле relations.json отсутствует ключ 'relations'.")
        return

    relations = relations_data["relations"]

    # Проверка наличия наших фракций в данных
    if faction not in relations or target_faction not in relations:
        print(f"Ошибка: Фракция '{faction}' или '{target_faction}' не найдена в relations.json.")
        return

    # Обнуление отношений
    if target_faction in relations[faction]:
        relations[faction][target_faction] = 0
    else:
        print(f"Ошибка: Отношения между '{faction}' и '{target_faction}' не найдены.")

    if faction in relations[target_faction]:
        relations[target_faction][faction] = 0
    else:
        print(f"Ошибка: Отношения между '{target_faction}' и '{faction}' не найдены.")

    # Сохранение изменений в файл
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(relations_data, file, ensure_ascii=False, indent=4)
        print(f"Отношения между '{faction}' и '{target_faction}' успешно обнулены.")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")

#-------------------------------------

def load_faction_files(folder_path):
    """Загружает данные о фракциях из указанной папки."""
    faction_files = {}
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не найдена.")
        return faction_files
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            faction_name = filename[:-5]  # Убираем расширение .json
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    json.load(file)  # Просто проверяем, что файл можно прочитать
                    faction_files[faction_name] = file_path
            except Exception as e:
                print(f"Ошибка чтения файла {file_path}: {e}")
    return faction_files

def calculate_economy_points(buildings_file):
    """Вычисляет общие очки экономики для указанной фракции."""
    total_buildings = 0
    if not os.path.exists(buildings_file):
        print(f"Файл {buildings_file} не найден.")
        return total_buildings
    try:
        with open(buildings_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("Некорректный формат данных: ожидался словарь.")
            for city_info in data.values():
                buildings = city_info.get("Здания", {})
                total_buildings += sum(buildings.values())
    except Exception as e:
        print(f"Ошибка обработки файла {buildings_file}: {e}")
    return total_buildings

def create_economy_rating_table(faction_files):
    """Создает таблицу рейтинга экономик."""
    economy_points = {}
    for faction, file in faction_files.items():
        points = calculate_economy_points(file)
        economy_points[faction] = points

    max_points = max(economy_points.values(), default=1)
    layout = GridLayout(cols=3, size_hint_y=None, spacing=5, padding=10)
    layout.bind(minimum_height=layout.setter('height'))

    def add_header_with_background(text):
        header = Label(text=text, bold=True, color=(1, 1, 1, 1), size_hint_y=None, height=40)
        with header.canvas.before:
            Color(0.2, 0.6, 1, 1)  # Синий фон
            header.rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(
            pos=lambda _, value: setattr(header.rect, 'pos', value),
            size=lambda _, value: setattr(header.rect, 'size', value)
        )
        return header

    layout.add_widget(add_header_with_background("Фракция"))
    layout.add_widget(add_header_with_background("Рейтинг (%)"))
    layout.add_widget(add_header_with_background("Плотность застройки"))

    rank_colors = {
        0: (1, 1, 1, 1),       # Белый (1-й)
        1: (0, 0.8, 0.8, 1),   # Бирюзовый (2-й)
        2: (0, 1, 0, 1),       # Зеленый (3-й)
        3: (1, 1, 0, 1),       # Желтый (4-й)
        4: (1, 0, 0, 1)        # Красный (5-й)
    }

    sorted_factions = sorted(economy_points.items(), key=lambda x: x[1], reverse=True)
    for rank, (faction, points) in enumerate(sorted_factions):
        rating = (points / max_points) * 100 if max_points > 0 else 0
        russian_name = faction_names_build.get(faction, faction)
        row_color = rank_colors.get(rank, (0.5, 0.5, 0.5, 1))

        layout.add_widget(Label(text=russian_name, color=row_color, size_hint_y=None, height=40))
        layout.add_widget(Label(text=f"{rating:.2f}%", color=row_color, size_hint_y=None, height=40))
        layout.add_widget(Label(text=str(points), color=row_color, size_hint_y=None, height=40))

    return layout


def create_ratings_tab():
    """Создает вкладку 'Рейтинги' с выпадающим меню для выбора таблиц."""
    # Загружаем данные для армий и экономики
    faction_army_files = load_faction_files(os.path.join("files", "config", "manage_ii"))
    faction_economy_files = load_faction_files(os.path.join("files", "config", "buildings_in_city"))

    # Основной контейнер
    layout = BoxLayout(orientation="vertical")

    # Выпадающее меню для выбора таблицы
    spinner = Spinner(
        text="Выберите рейтинг",
        values=("Рейтинг армий", "Рейтинг экономик"),
        size_hint=(1, None),
        height=40,
        background_color=(0.2, 0.6, 1, 1),  # Синий фон
        color=(1, 1, 1, 1)  # Белый текст
    )

    # Контейнер для отображения выбранной таблицы
    content_area = BoxLayout(orientation="vertical", size_hint=(1, 1))

    # Функция для обновления содержимого при выборе элемента из Spinner
    def update_content(instance, value):
        content_area.clear_widgets()  # Очищаем текущее содержимое
        if value == "Рейтинг армий":
            table_layout = create_army_rating_table(faction_army_files)
        elif value == "Рейтинг экономик":
            table_layout = create_economy_rating_table(faction_economy_files)
        else:
            table_layout = Label(text="Нет данных", color=(1, 1, 1, 1))

        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(table_layout)
        content_area.add_widget(scroll_view)

    # Привязываем обработчик к событию выбора элемента
    spinner.bind(text=update_content)

    # Добавляем выпадающее меню и контейнер с содержимым
    layout.add_widget(spinner)
    layout.add_widget(content_area)

    return layout

def show_ratings_popup():
    """Открывает всплывающее окно с рейтингами."""
    content = create_ratings_tab()
    popup = Popup(
        title="Рейтинги",
        content=content,
        size_hint=(0.8, 0.8),
        auto_dismiss=True
    )
    popup.open()


def calculate_army_points(faction_file):
    """Вычисляет общие очки армии и численность армии для указанной фракции."""
    class_coefficients = {
        "1": 1.1,  # Класс 1: базовые юниты
        "2": 1.4,  # Класс 2: улучшенные юниты
        "3": 1.9,  # Класс 3: элитные юниты
        "4": 2.8   # Класс 4: легендарные юниты
    }
    total_points = 0
    total_units = 0  # Численность армии
    if not os.path.exists(faction_file):
        print(f"Файл {faction_file} не найден.")
        return total_points, total_units
    try:
        with open(faction_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("Некорректный формат данных: ожидался словарь.")
            for city_data in data.values():
                for city_info in city_data:
                    for unit in city_info.get("units", []):
                        stats = unit.get("units_stats", {})
                        unit_class = str(stats.get("Класс юнита", "1"))
                        damage = stats.get("Урон", 0)
                        defense = stats.get("Защита", 0)
                        endurance = stats.get("Живучесть", 0)
                        coefficient = class_coefficients.get(unit_class, 1.0)
                        unit_points = defense + endurance + (damage * coefficient)
                        unit_count = unit.get("unit_count", 1)
                        total_points += unit_points * unit_count
                        total_units += unit_count
    except Exception as e:
        print(f"Ошибка обработки файла {faction_file}: {e}")
    return total_points, total_units

def create_army_rating_table(faction_files):
    """Создает таблицу рейтинга армий."""
    army_points = {}
    army_units = {}  # Словарь для хранения численности армий
    for faction, file in faction_files.items():
        points, units = calculate_army_points(file)
        army_points[faction] = points
        army_units[faction] = units

    max_points = max(army_points.values(), default=1)
    layout = GridLayout(cols=3, size_hint_y=None, spacing=5, padding=10)
    layout.bind(minimum_height=layout.setter('height'))

    def add_header_with_background(text):
        header = Label(
            text=text,
            bold=True,
            color=(1, 1, 1, 1),  # Белый текст
            size_hint_y=None,
            height=40
        )
        with header.canvas.before:
            Color(0.2, 0.6, 1, 1)  # Синий фон
            header.rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(
            pos=lambda _, value: setattr(header.rect, 'pos', value),
            size=lambda _, value: setattr(header.rect, 'size', value)
        )
        return header

    layout.add_widget(add_header_with_background("Фракция"))
    layout.add_widget(add_header_with_background("Рейтинг (%)"))
    layout.add_widget(add_header_with_background("Численность армии"))

    rank_colors = {
        0: (1, 1, 1, 1),       # Белый (1-й)
        1: (0, 0.8, 0.8, 1),   # Бирюзовый (2-й)
        2: (0, 1, 0, 1),       # Зеленый (3-й)
        3: (1, 1, 0, 1),       # Желтый (4-й)
        4: (1, 0, 0, 1)        # Красный (5-й)
    }

    sorted_factions = sorted(army_points.items(), key=lambda x: x[1], reverse=True)
    for rank, (faction, points) in enumerate(sorted_factions):
        rating = (points / max_points) * 100 if max_points > 0 else 0
        russian_name = faction_names.get(faction, faction)
        row_color = rank_colors.get(rank, (0.5, 0.5, 0.5, 1))
        units = army_units[faction]

        layout.add_widget(Label(text=russian_name, color=row_color, size_hint_y=None, height=40))
        layout.add_widget(Label(text=f"{rating:.2f}%", color=row_color, size_hint_y=None, height=40))
        layout.add_widget(Label(text=str(units), color=row_color, size_hint_y=None, height=40))

    return layout




#------------------------------------------------------------------
def start_politic_mode(faction, game_area, class_faction):
    """Инициализация политического режима для выбранной фракции"""
    # Создаем layout для кнопок
    politics_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, 0.1),
        pos_hint={'x': 0, 'y': 0},
        spacing=10,
        padding=10
    )

    # Функция для создания стильных кнопок
    def create_styled_button(text, on_press_callback):
        button = Button(
            text=text,
            size_hint_x=0.33,
            size_hint_y=None,
            height=50,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_size=16,
            bold=True
        )
        with button.canvas.before:
            Color(0.2, 0.6, 1, 1)
            button.rect = Rectangle(pos=button.pos, size=button.size)

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        button.bind(pos=update_rect, size=update_rect)
        button.bind(on_press=on_press_callback)
        return button

    # Создаем кнопки
    negotiate_btn = create_styled_button("Новый договор", lambda x: show_new_agreement_window(faction, game_area))
    form_alliance_btn = create_styled_button("Управление союзниками", lambda x: print("Управление союзниками"))
    declare_raite_btn = create_styled_button(
        "Рейтинги",
        lambda x: show_ratings_popup()
    )

    # Добавляем кнопки в layout
    politics_layout.add_widget(negotiate_btn)
    politics_layout.add_widget(form_alliance_btn)
    politics_layout.add_widget(declare_raite_btn)

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
