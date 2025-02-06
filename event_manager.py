import os
import json
import random
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# Путь к файлам данных
RELATIONS_PATH = "files/config/status/dipforce/relations.json"
RESOURCE_USER_PATH = "files/config/resources/resources.json"

translation_dict = {
    "Аркадия": "arkadia",
    "Селестия": "celestia",
    "Этерия": "eteria",
    "Хиперион": "giperion",
    "Халидон": "halidon",
}

faction_names_build = {
    "arkadia_buildings_city": "Аркадия",
    "celestia_buildings_city": "Селестия",
    "eteria_buildings_city": "Этерия",
    "giperion_buildings_city": "Хиперион",
    "halidon_buildings_city": "Халидон"
}

# Словари с событиями
PASSIVE_EVENTS = [
    {"description": "Обнаружены новые месторождения....", "resource": "Сырье", "change": 5000},
    {"description": "Эпидемия подкосила рабочих.", "resource": "Рабочие", "change": -10000},
    {"description": "Нам удалось собрать дополнительные налоги с должников.", "resource": "Кроны", "change": 20000},
    {"description": "Урожай поела тля...", "resource": "Сырье", "change": -5000},
    {"description": "Новые технологи добычи, позволили нам увеличить поставки сырья", "resource": "Сырье", "change": 20000},
    {"description": "Неизвестная болезнь подкосила людей", "resource": "Рабочие", "change": -1500},
    {"description": "Люди нашли клад, и уплатили налог на прибыль...", "resource": "Кроны", "change": 5000},
    {"description": "Новый вирус поразил рабочих при добыче, нам пришлось уничтожить урожай...", "resource": "Сырье", "change": -500000}
]

ACTIVE_EVENTS = [
    {
        "description": "Протесты в одной провинции переросли в беспорядки...",
        "option_1": "Поддержать правительство (+3 отношения, -7000 Крон)",
        "option_2": "Поддержать протестующих (-3 отношения, +15000 Крон)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -7000}, "relation_change": 3},
            "option_2": {"resource_changes": {"Кроны": 15000}, "relation_change": -3},
        },
    },
    {
        "description": "Граждане требуют снижения налогов в этом квартале.",
        "option_1": "Повысить зарплаты (-25000 Крон, +300 Рабочих)",
        "option_2": "Отказать (-100 Населения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -25000, "Рабочие": 300}},
            "option_2": {"resource_changes": {"Население": -100}},
        },
    },
    {
        "description": "В одной провинции пришли к выводу забивать людей камнями за ложь..",
        "option_1": "Поддержать людей (-45000 Крон, +4000 Рабочих, -15 отношения)",
        "option_2": "Проигнорировать проблему (+90000 Крон, +10 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -45000, "Рабочие": 4000}, "relation_change": -15},
            "option_2": {"resource_changes": {"Кроны": 90000}, "relation_change": 10},
        },
    },
    {
        "description": "Наркокартели объявили награду за каждого убитого полицейского",
        "option_1": "Использовать военных для подавления картелей (-250000 Крон, -3000 Рабочих, +8 отношения)",
        "option_2": "Игнорировать проблему ( +650000 Крон, -11 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -250000, "Рабочие": -3000}, "relation_change": 8},
            "option_2": {"resource_changes": {"Кроны": 650000}, "relation_change": -11},
        },
    },
    {
        "description": "Новый закон предлагаемый международной организацией, устанавливает новые нормы налогов",
        "option_1": "Поддержать закон (-7500000 Крон, +30000 Рабочих)",
        "option_2": "Наложить запрет  (+5000000 Крон, -50000 Рабочих)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -7500000, "Рабочие": 30000}},
            "option_2": {"resource_changes": {"Кроны": 5000000, "Рабочие": -50000}}
        },
    },
    {
        "description": "В одной из стран к власти дорвались террористы",
        "option_1": "Начать специальную операцию (-3500000 Крон, -75000 Рабочих, +20 отношения)",
        "option_2": "Признать новое правительство (+600000 Крон, +120000 Сырья, -35 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -3500000, "Рабочие": -75000}, "relation_change": 20},
            "option_2": {"resource_changes": {"Кроны": 600000, "Сырье": 120000, "Рабочие": -3000}, "relation_change": -35},
        },
    },
    {
        "description": "Гражданин одной из стран выпустил новую вакцину, но ВОЗ запретил ее использование",
        "option_1": "Принять риски новой вакцины (-25000 Крон, +30000 Рабочих, -5 отношения)",
        "option_2": "Поддержать ВОЗ (+ 40000 Крон, -250000 Рабочих, +10 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -25000, "Рабочие": 30000}, "relation_change": -5},
            "option_2": {"resource_changes": {"Кроны": 40000, "Рабочие": -250000}, "relation_change": 10},
        },
    },
    {
        "description": "Институт развития предлагает профинансировать новые разработки в области ИИ.",
        "option_1": "Поддержать (-1500000 Крон, +7000 Рабочих)",
        "option_2": "Отказать (+2500000 Крон, -10000 Рабочих)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -1500000, "Рабочие": 7000}},
            "option_2": {"resource_changes": {"Кроны": 2500000, "Рабочие": -10000}},
        },
    },
]

class EventManager:
    def __init__(self, player_faction, game_screen):
        self.player_faction = player_faction
        self.game_screen = game_screen  # Ссылка на экран игры для отображения событий
        self.relations_path = RELATIONS_PATH
        self.resource_user_path = RESOURCE_USER_PATH
        self.relations = {}
        self.resource_user = {}  # Используем словарь для хранения ресурсов
        self.load_data()

    def load_json_file(self, file_path):
        """Загрузка данных из JSON-файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Файл {file_path} не найден!")
        except json.JSONDecodeError:
            print(f"Ошибка декодирования JSON в файле {file_path}")
        except Exception as e:
            print(f"Неожиданная ошибка при чтении файла {file_path}: {e}")
        return {}

    def save_json_file(self, file_path, data):
        """Сохранение данных в JSON-файл."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при сохранении файла {file_path}: {e}")

    def load_data(self):
        """Загружает данные отношений и ресурсов."""
        # Загрузка отношений
        relations_data = self.load_json_file(self.relations_path)
        if not isinstance(relations_data, dict):
            print(f"Ошибка: Некорректные данные в файле {self.relations_path}.")
            relations_data = {}
        self.relations = relations_data.get("relations", {})
        # Загрузка ресурсов
        resources_data = self.load_json_file(self.resource_user_path)
        if not isinstance(resources_data, dict):
            print(f"Ошибка: Некорректные данные в файле {self.resource_user_path}.")
            resources_data = {}
        self.resource_user = resources_data
        print(f"Загруженные отношения: {self.relations}")
        print(f"Загруженные ресурсы игрока: {self.resource_user}")

    def handle_passive_event(self):
        """Обработка пассивного события."""
        event = random.choice(PASSIVE_EVENTS)
        resource = event["resource"]
        change = event["change"]
        # Обновляем ресурсы
        if resource in self.resource_user:
            self.resource_user[resource] += change
        else:
            self.resource_user[resource] = change
        print(f"Пассивное событие: {event['description']}. {resource} изменился на {change}.")
        self.save_resources()
        # Отображаем пассивное событие в виде всплывающего окна
        description = f"{event['description']} ({resource}: {change})"
        self.show_event_popup(description)

    def show_event_popup(self, description):
        """Отображение события в виде всплывающего окна."""
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        label = Label(text=description, font_size=16, size_hint_y=None, height=100)
        button_close = Button(text="Закрыть", size_hint_y=None, height=50, background_color=(0.2, 0.6, 1, 1))
        popup = Popup(title="Событие", content=content, size_hint=(0.8, 0.5), title_align="center")

        def on_button_close(instance):
            popup.dismiss()

        button_close.bind(on_press=on_button_close)
        content.add_widget(label)
        content.add_widget(button_close)
        popup.open()

    def apply_effects(self, effects):
        """Применение эффектов события."""
        # Применение изменений ресурсов
        if "resource_changes" in effects:
            for resource, change in effects["resource_changes"].items():
                if resource in self.resource_user:
                    self.resource_user[resource] += change
                else:
                    self.resource_user[resource] = change

        # Применение изменений отношений
        if "relation_change" in effects:
            factions = list(self.relations.get(self.player_faction, {}).keys())
            for faction in factions:
                # Проверяем случайность для применения изменения
                if random.choice([True, False]):
                    current_relation = self.relations[self.player_faction][faction]
                    new_relation = current_relation + effects["relation_change"]
                    # Ограничиваем значение отношений минимальным значением 0
                    self.relations[self.player_faction][faction] = max(new_relation, 0)

        # Сохраняем изменения в файлы
        self.save_resources()
        self.save_relations()

    def generate_event(self):
        """Генерация случайного события."""
        event_type = random.choice(["passive", "active"])
        if event_type == "passive":
            self.handle_passive_event()
        else:
            self.handle_active_event()

    def handle_active_event(self):
        """Обработка активного события."""
        event = random.choice(ACTIVE_EVENTS)
        description = event["description"]
        option_1 = event["option_1"]
        option_2 = event["option_2"]
        self.show_event_active_popup(event, description, option_1, option_2)

    def show_event_active_popup(self, event, description, option_1, option_2):
        """Отображение события в виде всплывающего окна."""
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        label = Label(text=description, font_size=16, size_hint_y=None, height=100)
        button_1 = Button(text=option_1, size_hint_y=None, height=50, background_color=(0.2, 0.6, 1, 1))
        button_2 = Button(text=option_2, size_hint_y=None, height=50, background_color=(1, 0.2, 0.2, 1))
        popup = Popup(title="Событие", content=content, size_hint=(0.8, 0.5), title_align="center")

        def on_button_1(instance):
            self.apply_effects(event["effects"]["option_1"])
            popup.dismiss()

        def on_button_2(instance):
            self.apply_effects(event["effects"]["option_2"])
            popup.dismiss()

        button_1.bind(on_press=on_button_1)
        button_2.bind(on_press=on_button_2)
        content.add_widget(label)
        content.add_widget(button_1)
        content.add_widget(button_2)
        popup.open()

    def save_resources(self):
        """Сохранение ресурсов игрока в файл и очистка словаря."""
        # Сохраняем текущие ресурсы в файл
        self.save_json_file(self.resource_user_path, self.resource_user)
        print("Ресурсы успешно сохранены в файл.")
        # Очищаем словарь ресурсов
        self.resource_user.clear()
        print("Словарь ресурсов очищен.")

    def save_relations(self):
        """Сохранение отношений в файл."""
        self.save_json_file(self.relations_path, {"relations": self.relations})