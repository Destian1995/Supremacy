from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.gridlayout import GridLayout
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
    # Список всех фракций
    all_factions = ["Селестия", "Аркадия", "Этерия", "Халидон", "Хиперион"]
    # Исключаем текущую фракцию
    available_factions = [f for f in all_factions if f != faction]
    # Создаем контент для Popup
    content = BoxLayout(orientation='vertical', padding=10, spacing=5)  # Уменьшаем отступы и промежутки

    # Заголовок
    title = Label(
        text="Торговое соглашение",
        size_hint=(1, None),
        height=40,  # Фиксированная высота заголовка
        font_size=16  # Увеличиваем размер шрифта для заголовка
    )
    content.add_widget(title)

    # Спиннеры и поля ввода
    factions_spinner = Spinner(
        text="С какой фракцией?",
        values=available_factions,
        size_hint=(1, None),
        height=30,  # Фиксированная высота спиннера
        font_size=14
    )
    content.add_widget(factions_spinner)

    our_resource_spinner = Spinner(
        text="Наш ресурс",
        values=["Рабочие", "Сырье", "Кроны"],
        size_hint=(1, None),
        height=30,
        font_size=14
    )
    content.add_widget(our_resource_spinner)

    their_resource_spinner = Spinner(
        text="Их ресурс",
        values=["Рабочие", "Сырье", "Кроны"],
        size_hint=(1, None),
        height=30,
        font_size=14
    )
    content.add_widget(their_resource_spinner)

    our_percentage_input = TextInput(
        hint_text="Сумма отчислений нашему союзнику",
        multiline=False,
        size_hint=(1, None),
        height=30,
        font_size=14
    )
    content.add_widget(our_percentage_input)

    their_percentage_input = TextInput(
        hint_text="Сумма прихода от нашего союзника",
        multiline=False,
        size_hint=(1, None),
        height=30,
        font_size=14
    )
    content.add_widget(their_percentage_input)

    agreement_summary = TextInput(
        readonly=True,
        multiline=True,
        size_hint=(1, None),
        height=80,  # Фиксированная высота текстового поля
        font_size=14
    )
    content.add_widget(agreement_summary)

    # Кнопки
    button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=5)  # Высота кнопок 20% от окна
    generate_button = Button(
        text="Сформировать условия",
        size_hint=(0.5, 1),  # Кнопка занимает 50% ширины и всю высоту
        font_size=14
    )
    send_button = Button(
        text="Отправить условия договора",
        size_hint=(0.5, 1),  # Кнопка занимает 50% ширины и всю высоту
        font_size=14,
        opacity=0  # Скрываем кнопку изначально
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
        # Путь к собственному пути, для вычитывания данных
        filename_i_am = transform_filename(f'files/config/status/trade_dogovor/{faction}.json')
        # Сохраняем данные в файл JSON
        with open(filename_friend, 'w', encoding='utf-8') as file:
            json.dump(agreement_data, file, ensure_ascii=False, indent=4)
        # Сохраняем данные в собственный файл
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
    back_button = Button(
        text="Назад",
        size_hint=(1, 0.1),  # Кнопка занимает 10% высоты окна
        font_size=14
    )
    content.add_widget(back_button)

    # Создаем Popup с увеличенными размерами
    popup = Popup(
        title="Торговое соглашение",
        content=content,
        size_hint=(0.6, 0.7),  # Размер окна
        auto_dismiss=False
    )

    # Привязываем кнопку "Назад" к закрытию Popup
    back_button.bind(on_press=popup.dismiss)

    # Открываем Popup
    popup.open()


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
