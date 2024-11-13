# politic.py
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from game_process import *  # Импортируем GameScreen

def start_politic_mode(faction, game_area):
    """Инициализация политического режима для выбранной фракции"""


    # Кнопки для управления политикой
    politics_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), pos_hint={'x': 0, 'y': 0})

    negotiate_btn = Button(text="Переговоры о мире", size_hint_x=0.33, size_hint_y=None, height=50)
    form_alliance_btn = Button(text="Создать союз", size_hint_x=0.33, size_hint_y=None, height=50)
    declare_war_btn = Button(text="Объявить войну", size_hint_x=0.33, size_hint_y=None, height=50)

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
    import politic  # Импортируем здесь, чтобы избежать цикличес
    game_area.clear_widgets()
    politic.start_politic_mode(faction, game_area)
