import os

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import  Screen
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
import economic
# Файл, который включает режимы игры
from economic import Faction
import army
import politic
from ii import AIController
from sov import AdvisorView

# Список всех фракций
FACTIONS = ["Аркадия", "Селестия", "Хиперион", "Халидон", "Этерия"]
global_resource_manager = {}
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


class ResourceBox(BoxLayout):
    def __init__(self, resource_manager, **kwargs):
        super(ResourceBox, self).__init__(**kwargs)
        self.resource_manager = resource_manager
        self.orientation = 'horizontal'
        self.size_hint = (0.8, 0.14)
        self.pos_hint = {'center_x': 0.36, 'center_y': 1}
        self.padding = [0, 0, 0, 0]  # Внешние отступы
        self.spacing = -65  # Расстояние между метками

        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Цвет фона
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

        # Сохраняем метки для ресурсов, чтобы обновлять их при изменении значений
        self.labels = {}
        self.update_resources()

    def update_rect(self, *args):
        """Обновление размеров и позиции прямоугольника фона."""
        self.rect.size = self.size
        self.rect.pos = self.pos

    def update_resources(self):
        """Обновление отображаемых ресурсов."""
        resources = self.resource_manager.get_resources()

        for resource_name, value in resources.items():
            if resource_name in self.labels:
                # Обновляем текст существующей метки
                self.labels[resource_name].text = f"{resource_name}: {value}"
            else:
                # Создаем новую метку, если она не существует
                label = Label(
                    text=f"{resource_name}: {value}",
                    size_hint_y=None,
                    height=35,  # Уменьшенная высота метки
                    font_size=13,  # Уменьшенный размер шрифта
                    color=(1, 1, 1, 1)  # Белый цвет текста
                )
                self.labels[resource_name] = label
                self.add_widget(label)


# Класс для кнопки с изображением
class ImageButton(ButtonBehavior, Image):
    pass


class GameScreen(Screen):
    def __init__(self, selected_faction, cities, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.selected_faction = selected_faction
        self.cities = cities
        self.faction = Faction(selected_faction)
        self.ai_controllers = {}

        # Инициализация UI
        self.init_ui()

        # Запускаем обновление ресурсов каждую 1 секунду
        Clock.schedule_interval(self.update_cash, 1)

    def init_ui(self):
        # панель с выбранной фракцией
        self.faction_label = Label(
            text=f"{self.selected_faction}",
            font_size='30sp',
            size_hint=(1, 0.1),
            pos_hint={'right': 1, 'top': 0.95},
            color=(0, 0, 0, 1)  # Черный цвет текста
        )
        self.add_widget(self.faction_label)

        # Боковая панель с кнопками режимов
        self.mode_panel = BoxLayout(orientation='vertical', size_hint=(0.2, 1), pos_hint={'x': -0.06, 'y': 0})

        # Уменьшенные иконки
        btn_economy = ImageButton(source='files/status/economy.jpg', size_hint_y=None, height=50, width=50,
                                  on_press=self.switch_to_economy)
        btn_army = ImageButton(source='files/status/army.jpg', size_hint_y=None, height=65, width=30,
                               on_press=self.switch_to_army)
        btn_politics = ImageButton(source='files/status/politic.jpg', size_hint_y=None, height=65, width=40,
                                   on_press=self.switch_to_politics)
        btn_advisor = ImageButton(
            source=transform_filename(f'files/sov/sov_{self.selected_faction}.jpg'),  # Иконка для кнопки
            size_hint_y=None,
            height=65,
            width=40,
            on_press=self.show_advisor
        )
        self.mode_panel.add_widget(btn_advisor)

        self.mode_panel.add_widget(btn_economy)
        self.mode_panel.add_widget(btn_army)
        self.mode_panel.add_widget(btn_politics)

        self.add_widget(self.mode_panel)

        # Центральная часть для отображения карты и игрового процесса
        self.game_area = FloatLayout(size_hint=(0.8, 1), pos_hint={'x': 0.2, 'y': 0})
        self.add_widget(self.game_area)

        # Добавляем кнопку "Завершить ход" в правый верхний угол
        end_turn_button = Button(
            text="Завершить ход",
            size_hint=(None, None),
            size=(190, 43),
            pos_hint={'right': 1, 'top': 1},
            on_press=self.process_turn
        )
        self.add_widget(end_turn_button)

        # Добавление ResourceBox в верхний правый угол, передаем resource_manager
        self.resource_box = ResourceBox(resource_manager=self.faction)
        self.add_widget(self.resource_box)

        # Инициализация ИИ для остальных фракций
        self.init_ai_controllers()

    def update_cash(self, dt):
        """Обновление текущего капитала фракции через каждые 15 секунд"""
        self.faction.update_cash()
        # Обновляем отображение в ResourceBox
        self.resource_box.update_resources()

    def show_advisor(self, instance):
        """Показать экран советника"""
        self.clear_game_area()
        advisor_view = AdvisorView(self.selected_faction)
        self.game_area.add_widget(advisor_view)

    def switch_to_economy(self, instance):
        """Переключение на экономическую вкладку"""
        self.clear_game_area()
        economic.start_economy_mode(self.faction, self.game_area)

    def switch_to_army(self, instance):
        """Переключение на армейскую вкладку"""
        self.clear_game_area()
        army.start_army_mode(self.selected_faction, self.game_area)

    def switch_to_politics(self, instance):
        """Переключение на политическическую вкладку"""
        self.clear_game_area()
        politic.start_politic_mode(self.selected_faction, self.game_area)

    def clear_game_area(self):
        """Очистка центральной области"""
        self.game_area.clear_widgets()

    def init_ai_controllers(self):
        """Создание контроллеров ИИ для каждой фракции кроме выбранной"""
        for faction in FACTIONS:
            if faction != self.selected_faction:
                self.ai_controllers[faction] = AIController(faction)

    def process_turn(self, instance=None):
        """Обработка хода игрока и ИИ"""
        # Обновляем ресурсы игрока
        self.faction.update_resources()
        self.resource_box.update_resources()

        # Путь к каталогу с файлами
        attack_in_city_dir = r'files\config\attack_in_city'

        # Проставляем 'True' во всех файлах в каталоге
        for filename in os.listdir(attack_in_city_dir):
            if filename.endswith('_check.txt'):
                file_path = os.path.join(attack_in_city_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write("True")

        # Выполнение хода для всех ИИ
        for ai_controller in self.ai_controllers.values():
            ai_controller.make_turn()

        # Логирование или обновление интерфейса после хода
        print("Ход завершён")
