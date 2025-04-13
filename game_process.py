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
from event_manager import EventManager
import sqlite3
import random

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


class GameStateManager:
    def __init__(self):
        self.faction = None  # Объект фракции
        self.resource_box = None  # Объект ResourceBox
        self.game_area = None  # Центральная область игры
        self.conn = None  # Соединение с базой данных
        self.cursor = None  # Курсор для работы с БД
        self.turn_counter = 1  # Счетчик ходов

    def initialize(self, selected_faction, db_path="game_data.db"):
        """Инициализация объектов игры."""
        self.faction = Faction(selected_faction)  # Создаем объект фракции
        self.conn = sqlite3.connect(db_path)  # Подключаемся к базе данных
        self.cursor = self.conn.cursor()
        self.turn_counter = self.load_turn(selected_faction)  # Загружаем счетчик ходов

    def load_turn(self, faction):
        """Загружает текущее значение счетчика ходов из базы данных."""
        try:
            self.cursor.execute('''
                SELECT turn_count
                FROM turn
                WHERE faction = ?
            ''', (faction,))
            row = self.cursor.fetchone()
            return row[0] if row else 1
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке счетчика ходов: {e}")
            return 0

    def save_turn(self, faction, turn_count):
        """Сохраняет текущее значение счетчика ходов в базу данных."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO turn (faction, turn_count)
                VALUES (?, ?)
            ''', (faction, turn_count))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении счетчика ходов: {e}")

    def close_connection(self):
        """Закрывает соединение с базой данных."""
        if self.conn:
            self.conn.close()

class ResourceBox(BoxLayout):
    def __init__(self, resource_manager, **kwargs):
        super(ResourceBox, self).__init__(**kwargs)
        self.resource_manager = resource_manager
        self.orientation = 'vertical'  # Вертикальное расположение ресурсов
        self.size_hint = (0.2, 0.3)  # Занимает 20% ширины и 30% высоты экрана
        self.pos_hint = {'x': 0, 'top': 1}  # Расположен в левом верхнем углу
        self.padding = [10, 10, 10, 10]  # Внешние отступы
        self.spacing = 5  # Расстояние между метками
        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)  # Темно-серый фон
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)
        # Сохраняем метки для ресурсов, чтобы обновлять их при изменении значений
        self.labels = {}
        self.update_resources()
        # Связываем изменение размеров виджета с обновлением шрифтов
        self.bind(size=self.update_font_sizes)

    def update_rect(self, *args):
        """Обновление размеров и позиции прямоугольника фона."""
        self.rect.size = self.size
        self.rect.pos = self.pos

    def update_resources(self):
        """Обновление отображаемых ресурсов."""
        resources = self.resource_manager.get_resources()
        # Очищаем старые виджеты
        self.clear_widgets()
        self.labels.clear()
        # Добавляем новые метки для ресурсов
        for resource_name, value in resources.items():
            label = Label(
                text=f"{resource_name}: {value}",
                size_hint_y=None,
                height=self.calculate_label_height(),
                font_size=self.calculate_font_size(),
                color=(1, 1, 1, 1),  # Белый цвет текста
                markup=True  # Поддержка форматирования текста
            )
            self.labels[resource_name] = label
            self.add_widget(label)

    def calculate_font_size(self):
        """Расчет размера шрифта на основе высоты виджета."""
        base_font_size = 16  # Базовый размер шрифта
        scale_factor = self.height / 800  # Масштабирование относительно высоты экрана
        return max(base_font_size * scale_factor, 12)  # Минимальный размер шрифта

    def calculate_label_height(self):
        """Расчет высоты метки на основе размера шрифта."""
        return self.calculate_font_size() * 2  # Высота метки в два раза больше размера шрифта

    def update_font_sizes(self, *args):
        """Обновление размеров шрифтов всех меток при изменении размеров виджета."""
        new_font_size = self.calculate_font_size()
        for label in self.labels.values():
            label.font_size = new_font_size
            label.height = self.calculate_label_height()

# Класс для кнопки с изображением
class ImageButton(ButtonBehavior, Image):
    pass


class GameScreen(Screen):
    def __init__(self, selected_faction, cities, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.selected_faction = selected_faction
        self.cities = cities
        # Инициализация GameStateManager
        self.game_state_manager = GameStateManager()
        self.game_state_manager.initialize(selected_faction)
        # Доступ к объектам через менеджер состояния
        self.faction = self.game_state_manager.faction
        self.conn = self.game_state_manager.conn
        self.cursor = self.game_state_manager.cursor
        self.turn_counter = self.game_state_manager.turn_counter

        # Сохраняем текущую фракцию игрока
        self.save_selected_faction_to_db()
        # Инициализация политических данных
        self.initialize_political_data()
        # Инициализация AI-контроллеров
        self.ai_controllers = {}
        # Инициализация EventManager
        self.event_manager = EventManager(self.selected_faction, self, self.game_state_manager.faction)
        # Инициализация UI
        self.init_ui()
        # Запускаем обновление ресурсов каждую 1 секунду
        Clock.schedule_interval(self.update_cash, 1)

    def init_ui(self):
        # Панель с выбранной фракцией
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
        # Кнопки режимов
        btn_economy = ImageButton(source='files/status/economy.jpg', size_hint_y=None, height=50, width=50,
                                  on_press=self.switch_to_economy)
        btn_army = ImageButton(source='files/status/army.jpg', size_hint_y=None, height=65, width=30,
                               on_press=self.switch_to_army)
        btn_politics = ImageButton(source='files/status/politic.jpg', size_hint_y=None, height=65, width=40,
                                   on_press=self.switch_to_politics)
        btn_advisor = ImageButton(
            source=transform_filename(f'files/sov/sov_{self.selected_faction}.jpg'),
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

        # Добавляем кнопку "Завершить ход"
        end_turn_button = Button(
            text="Завершить ход",
            size_hint=(None, None),
            size=(190, 43),
            pos_hint={'right': 1, 'top': 1},
            on_press=self.process_turn
        )
        self.add_widget(end_turn_button)

        # Добавляем метку для отображения текущего хода
        self.turn_label = Label(
            text=f"Текущий ход: {self.turn_counter}",
            font_size='18sp',
            size_hint=(None, None),
            size=(190, 30),
            pos_hint={'right': 1, 'top': 0.93},  # Размещаем под кнопкой "Завершить ход"
            color=(0, 0, 0, 1)  # Черный цвет текста
        )
        self.add_widget(self.turn_label)

        # Добавление ResourceBox в верхний правый угол
        self.resource_box = ResourceBox(resource_manager=self.faction)
        self.add_widget(self.resource_box)

        # Инициализация ИИ для остальных фракций
        self.init_ai_controllers()

    def save_selected_faction_to_db(self):
        """
        Сохраняет выбранную фракцию пользователя в таблицу user_faction.
        """
        try:
            # SQL-запрос для вставки данных
            query = "INSERT INTO user_faction (faction) VALUES (?)"
            # Выполнение запроса с кортежем в качестве параметра
            self.cursor.execute(query, (self.selected_faction,))
            # Фиксация изменений в базе данных
            self.conn.commit()
            print(f"Фракция '{self.selected_faction}' успешно сохранена для пользователя.")
        except Exception as e:
            # Откат изменений в случае ошибки
            self.conn.rollback()
            print(f"Ошибка при сохранении фракции: {e}")

    def process_turn(self, instance=None):
        """Обработка хода игрока и ИИ"""
        # Увеличиваем счетчик ходов
        self.turn_counter += 1

        # Обновляем метку с текущим ходом
        self.turn_label.text = f"Текущий ход: {self.turn_counter}"

        # Сохраняем текущее значение хода в таблицу turn
        self.save_turn(self.selected_faction, self.turn_counter)
        # Сохраняем историю ходов в таблицу turn_save
        self.save_turn_history(self.selected_faction, self.turn_counter)

        # Обновляем ресурсы игрока
        self.faction.update_resources()
        self.resource_box.update_resources()

        # Путь к каталогу с файлами
        attack_in_city_dir = r'files\config\attack_in_city'
        # Проставляем 'True' во всех файлах в каталоге после нападения
        for filename in os.listdir(attack_in_city_dir):
            if filename.endswith('_check.txt'):
                file_path = os.path.join(attack_in_city_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write("True")

        # Выполнение хода для всех ИИ
        for ai_controller in self.ai_controllers.values():
            ai_controller.make_turn()

        # Логирование или обновление интерфейса после хода
        print(f"Ход {self.turn_counter} завершён")
        self.event_now = random.randint(4, 7)
        # Проверяем, нужно ли запустить событие
        if self.turn_counter % self.event_now == 0:
            print("Генерация события...")
            self.event_manager.generate_event(self.turn_counter)

    def initialize_political_data(self):
        """
        Инициализирует таблицу political_systems значениями по умолчанию,
        если она пуста. Политическая система для каждой фракции выбирается случайным образом.
        Условие: не может быть меньше 2 и больше 3 стран с одним политическим строем.
        """
        try:
            # Проверяем, есть ли записи в таблице
            self.cursor.execute("SELECT COUNT(*) FROM political_systems")
            count = self.cursor.fetchone()[0]
            if count == 0:
                # Список всех фракций
                factions = ["Аркадия", "Селестия", "Хиперион", "Этерия", "Халидон"]

                # Список возможных политических систем
                systems = ["Капитализм", "Коммунизм"]

                # Функция для проверки распределения
                def is_valid_distribution(distribution):
                    counts = {system: distribution.count(system) for system in systems}
                    return all(2 <= count <= 3 for count in counts.values())

                # Генерация случайного распределения
                while True:
                    default_systems = [(faction, random.choice(systems)) for faction in factions]
                    distribution = [system for _, system in default_systems]

                    if is_valid_distribution(distribution):
                        break

                # Вставляем данные в таблицу
                self.cursor.executemany(
                    "INSERT INTO political_systems (faction, system) VALUES (?, ?)",
                    default_systems
                )
                self.conn.commit()
                print("Таблица political_systems инициализирована случайными значениями.")
        except sqlite3.Error as e:
            print(f"Ошибка при инициализации таблицы political_systems: {e}")

    def update_cash(self, dt):
        """Обновление текущего капитала фракции через каждые 1 секунду."""
        self.faction.update_cash()
        self.resource_box.update_resources()

    def switch_to_economy(self, instance):
        """Переключение на экономическую вкладку."""
        self.clear_game_area()
        economic.start_economy_mode(self.game_state_manager.faction, self.game_area)

    def switch_to_army(self, instance):
        """Переключение на армейскую вкладку."""
        self.clear_game_area()
        army.start_army_mode(self.selected_faction, self.game_area, self.game_state_manager.faction)

    def switch_to_politics(self, instance):
        """Переключение на политическую вкладку."""
        self.clear_game_area()
        politic.start_politic_mode(self.selected_faction, self.game_area, self.game_state_manager.faction)


    def clear_game_area(self):
        """Очистка центральной области."""
        self.game_area.clear_widgets()

    def on_stop(self):
        """Закрытие соединения с базой данных при завершении игры."""
        self.game_state_manager.close_connection()

    def show_advisor(self, instance):
        """Показать экран советника"""
        self.clear_game_area()
        advisor_view = AdvisorView(self.selected_faction)
        self.game_area.add_widget(advisor_view)


    def init_ai_controllers(self):
        """Создание контроллеров ИИ для каждой фракции кроме выбранной"""
        for faction in FACTIONS:
            if faction != self.selected_faction:
                self.ai_controllers[faction] = AIController(faction)

    def load_turn(self, faction):
        """Загрузка текущего значения хода для фракции."""
        self.cursor.execute('SELECT turn_count FROM turn WHERE faction = ?', (faction,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def save_turn(self, faction, turn_count):
        """Сохранение текущего значения хода для фракции."""
        self.cursor.execute('''
            INSERT OR REPLACE INTO turn (faction, turn_count)
            VALUES (?, ?)
        ''', (faction, turn_count))
        self.conn.commit()

    def save_turn_history(self, faction, turn_count):
        """Сохранение истории ходов в таблицу turn_save."""
        self.cursor.execute('''
            INSERT INTO turn_save (faction, turn_count)
            VALUES (?, ?)
        ''', (faction, turn_count))
        self.conn.commit()


    def reset_game(self):
        """Сброс игры (например, при новой игре)."""
        self.save_turn(self.selected_faction, 0)  # Сбрасываем счетчик ходов до 0
        self.turn_counter = 0
        print("Счетчик ходов сброшен.")