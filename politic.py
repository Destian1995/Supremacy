from kivy.uix.slider import Slider
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
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

def show_new_agreement_window(faction, game_area):
    """Главное окно 'Новый договор' с кнопками категорий"""

    game_area.clear_widgets()

    # Основной layout
    layout = FloatLayout()

    # Главное окно
    window = BoxLayout(
        orientation='vertical',
        padding=10,
        spacing=10,
        size_hint=(0.6, 0.7),
        pos_hint={'center_x': 0.5, 'center_y': 0.5}
    )

    # Заголовок
    title = Label(
        text="Новый договор",
        size_hint=(1, None),
        height=50,
        font_size=20
    )

    # Список кнопок
    button_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 1))

    # Создаем кнопки для каждой категории
    categories = [
        ("Торговое соглашение", show_trade_agreement_form),
        ("Договор об культурном обмене", show_cultural_exchange_form),
        ("Предоставление дип. данных", show_diplomatic_data_form),
        ("Заключение альянса", show_alliance_form),
        ("Объявление войны", show_declare_war_form),
    ]

    for category_name, callback in categories:
        button = Button(
            text=category_name,
            size_hint=(1, None),
            height=50
        )
        button.bind(on_press=lambda instance, cb=callback: cb(faction, game_area))
        button_layout.add_widget(button)

    # Кнопка "Вернуться"
    back_button = Button(
        text="Вернуться",
        size_hint=(1, None),
        height=40
    )
    back_button.bind(on_press=lambda x: game_area.clear_widgets())

    # Добавляем всё в основное окно
    window.add_widget(title)
    window.add_widget(button_layout)
    window.add_widget(back_button)

    layout.add_widget(window)

    # Отображаем интерфейс в game_area
    game_area.add_widget(layout)


def show_trade_agreement_form(faction, game_area):
    """Окно формы для торгового соглашения"""
    game_area.clear_widgets()
    layout = FloatLayout()

    # Список всех фракций
    all_factions = ["Селестия", "Аркадия", "Этерия", "Халидон", "Хиперион"]

    # Исключаем текущую фракцию
    available_factions = [f for f in all_factions if f != faction]

    window = BoxLayout(
        orientation='vertical',
        padding=20,
        spacing=8,
        size_hint=(0.6, 0.9),
        pos_hint={'center_x': 0.5, 'center_y': 0.5}
    )

    title = Label(
        text="Торговое соглашение",
        size_hint=(1, None),
        height=40,
        font_size=18
    )

    factions_spinner = Spinner(
        text="С какой фракцией?",
        values=available_factions,
        size_hint=(1, None),
        height=30
    )
    duration_spinner = Spinner(
        text="На какой срок?",
        values=["1 год(20 ходов)", "5 лет(100 ходов)", "10 лет(500 ходов)", "Бессрочно"],
        size_hint=(1, None),
        height=30
    )
    our_resource_spinner = Spinner(
        text="Наш ресурс",
        values=["Рабочие", "Сырье", "Деньги"],
        size_hint=(1, None),
        height=30
    )
    their_resource_spinner = Spinner(
        text="Их ресурс",
        values=["Рабочие", "Сырье", "Деньги"],
        size_hint=(1, None),
        height=30
    )

    # Поля ввода процентов
    our_percentage_input = TextInput(
        hint_text="Процент доходов нашему союзнику (0-100%)",
        multiline=False,
        size_hint=(1, None),
        height=35,
        input_filter="int"
    )

    their_percentage_input = TextInput(
        hint_text="Процент доходов от союзника (0-100%)",
        multiline=False,
        size_hint=(1, None),
        height=35,
        input_filter="int"
    )

    agreement_summary = TextInput(
        readonly=True,
        multiline=True,
        size_hint=(1, None),
        height=120,
        hint_text="Условия соглашения..."
    )

    generate_button = Button(
        text="Сформировать условия",
        size_hint=(1, None),
        height=35
    )

    send_button = Button(
        text="Отправить условия договора",
        size_hint=(1, None),
        height=35,
        opacity=0  # Скрываем кнопку изначально
    )

    def generate_agreement(instance):
        """Формирование текста соглашения"""
        faction_selected = factions_spinner.text
        duration_selected = duration_spinner.text
        our_resource_selected = our_resource_spinner.text
        their_resource_selected = their_resource_spinner.text
        our_percentage = our_percentage_input.text
        their_percentage = their_percentage_input.text

        if faction_selected == "С какой фракцией?":
            agreement_summary.text = "Пожалуйста, выберите фракцию для соглашения."
            return

        if not our_percentage.isdigit() or not their_percentage.isdigit():
            agreement_summary.text = "Пожалуйста, укажите проценты корректно (0-100)."
            return

        # Формируем текст для отображения
        agreement_summary.text = (
            f"Торговое соглашение с фракцией {faction_selected}.\n"
            f"Инициатор: {faction}.\n"
            f"Срок: {duration_selected}.\n"
            f"Наш ресурс: {our_resource_selected}.\n"
            f"Их ресурс: {their_resource_selected}.\n"
            f"Мы отправляем союзнику: {our_percentage}% доходов.\n"
            f"Мы получаем от союзника: {their_percentage}% доходов."
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
            "duration": duration_spinner.text,
            "our_resource": our_resource_spinner.text,
            "their_resource": their_resource_spinner.text,
            "our_percentage": our_percentage_input.text,
            "their_percentage": their_percentage_input.text
        }

        # Генерируем путь к файлу
        filename = transform_filename(f'files/config/status/trade_dogovor/{faction_selected}.json')

        # Сохраняем данные в файл JSON
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(agreement_data, file, ensure_ascii=False, indent=4)

        # Подтверждение отправки
        agreement_summary.text = f"Условия договора отправлены фракции {faction_selected}."

    generate_button.bind(on_press=generate_agreement)
    send_button.bind(on_press=send_agreement)

    back_button = Button(
        text="Назад",
        size_hint=(1, None),
        height=35
    )
    back_button.bind(on_press=lambda x: show_new_agreement_window(faction, game_area))

    window.add_widget(title)
    window.add_widget(factions_spinner)
    window.add_widget(duration_spinner)
    window.add_widget(our_resource_spinner)
    window.add_widget(their_resource_spinner)
    window.add_widget(our_percentage_input)
    window.add_widget(their_percentage_input)
    window.add_widget(generate_button)
    window.add_widget(agreement_summary)
    window.add_widget(send_button)  # Добавляем кнопку отправки
    window.add_widget(back_button)

    layout.add_widget(window)
    game_area.add_widget(layout)



def show_cultural_exchange_form(faction, game_area):
    """Заглушка: Договор о культурном обмене"""
    pass


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
