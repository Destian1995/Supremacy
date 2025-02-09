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
    {"description": "Обнаружены новые месторождения....", "resource": "Сырье", "change": 6000},
    {"description": "Эпидемия подкосила рабочих.", "resource": "Рабочие", "change": -10000},
    {"description": "Нам удалось собрать дополнительные налоги с должников.", "resource": "Кроны", "change": 24000},
    {"description": "Урожай поела тля...", "resource": "Сырье", "change": -5000},
    {"description": "Новые технологи добычи, позволили нам увеличить поставки сырья", "resource": "Сырье", "change": 20000},
    {"description": "Неизвестная болезнь подкосила людей", "resource": "Рабочие", "change": -1500},
    {"description": "Люди нашли клад, и уплатили налог на прибыль...", "resource": "Кроны", "change": 8000},
    {"description": "Новый вирус поразил рабочих при добыче, нам пришлось уничтожить урожай...", "resource": "Сырье", "change": -80000}
]

ACTIVE_EVENTS = [
    {
        "description": "Протесты в одной провинции переросли в беспорядки...",
        "option_1": "Поддержать правительство (+1 отношения, -7000 Крон)",
        "option_2": "Поддержать протестующих (-4 отношения, +15000 Крон)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -7000}, "relation_change": 1},
            "option_2": {"resource_changes": {"Кроны": 15000}, "relation_change": -4},
        },
    },
    {
        "description": "Граждане требуют снижения налогов в этом квартале.",
        "option_1": "Повысить зарплаты (-25000 Крон, +3000 Рабочих)",
        "option_2": "Отказать (-100 Населения, +10000 Сырье)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -25000, "Рабочие": 3000}},
            "option_2": {"resource_changes": {"Население": -100, "Сырье": 10000}},
        },
    },
    {
        "description": "В одной провинции пришли к выводу \n забивать людей камнями за ложь..",
        "option_1": "Поддержать людей (-15000 Крон, +5000 Рабочих, -15 отношения)",
        "option_2": "Проигнорировать проблему (+40000 Крон, +3 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -15000, "Рабочие": 5000}, "relation_change": -15},
            "option_2": {"resource_changes": {"Кроны": 40000}, "relation_change": 3},
        },
    },
    {
        "description": "Наркокартели объявили награду за каждого убитого полицейского",
        "option_1": "Использовать военных для подавления картелей (-25000 Крон, -3000 Рабочих, +4 отношения)",
        "option_2": "Игнорировать проблему (+75000 Крон, -5 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -25000, "Рабочие": -3000}, "relation_change": 4},
            "option_2": {"resource_changes": {"Кроны": 75000}, "relation_change": -5},
        },
    },
    {
        "description": "Новый закон предлагаемый международной организацией,\n устанавливает новые нормы налогов",
        "option_1": "Поддержать закон (+120000 Крон, +4 отношения)",
        "option_2": "Наложить запрет (+7000 Рабочих, +50000 Сырье, -12 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": 120000}, "relation_change": 4},
            "option_2": {"resource_changes": {"Рабочие": 7000, "Сырье": 50000}, "relation_change": -12},
        },
    },
    {
        "description": "В одной из стран к власти дорвались террористы",
        "option_1": "Начать специальную операцию (-25000 Крон, -25000 Рабочих, +6 отношения)",
        "option_2": "Признать новое правительство (+60000 Крон, +20000 Сырье, +4000 Рабочих, -12 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -25000, "Рабочие": -25000}, "relation_change": 6},
            "option_2": {"resource_changes": {"Кроны": 60000, "Сырье": 20000, "Рабочие": 4000}, "relation_change": -12},
        },
    },
    {
        "description": "Одна из стран выпустила новую вакцину,\n но ВОЗ запретил ее использование",
        "option_1": "Принять риски новой вакцины (-25000 Крон, +4000 Рабочих, +3 отношения)",
        "option_2": "Поддержать ВОЗ (+40000 Крон, +15000 Сырье, -10 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -25000, "Рабочие": 4000}, "relation_change": 3},
            "option_2": {"resource_changes": {"Кроны": 40000, "Сырье": 15000}, "relation_change": -10},
        },
    },
    {
        "description": "Институт развития предлагает профинансировать\n новые разработки в области ИИ.",
        "option_1": "Поддержать (-60000 Крон, -5000 Рабочих, +2 отношения)",
        "option_2": "Отказать (+15000 Крон, +20000 Сырье, -4 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -60000, "Рабочие": -5000}, "relation_change": 2},
            "option_2": {"resource_changes": {"Кроны": 15000, "Сырье": 20000}, "relation_change": -4},
        },
    },
    # Новые события
    {
        "description": "Эпидемия гриппа охватила регион.",
        "option_1": "Закупить вакцины (-30000 Крон, +5000 Населения)",
        "option_2": "Игнорировать проблему (-10000 Населения, +20000 Крон)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -30000, "Население": 5000}},
            "option_2": {"resource_changes": {"Население": -10000, "Кроны": 20000}},
        },
    },
    {
        "description": "Международная конференция предлагает сотрудничество.",
        "option_1": "Принять участие (+50000 Крон, +5 отношения)",
        "option_2": "Отказаться (-30000 Крон, -3 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": 50000}, "relation_change": 5},
            "option_2": {"resource_changes": {"Кроны": -30000}, "relation_change": -3},
        },
    },
    {
        "description": "Завод по производству сырья вышел из строя.",
        "option_1": "Ремонт завода (-40000 Крон, +20000 Сырье)",
        "option_2": "Закрыть завод (-10000 Рабочих, +10000 Крон)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -40000, "Сырье": 20000}},
            "option_2": {"resource_changes": {"Рабочие": -10000, "Кроны": 10000}},
        },
    },
    {
        "description": "Ученые открыли новый источник энергии.",
        "option_1": "Финансировать исследования (-80000 Крон, +10000 Рабочих)",
        "option_2": "Отложить проект (+20000 Крон, -5 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -80000, "Рабочие": 10000}, "relation_change": 3},
            "option_2": {"resource_changes": {"Кроны": 20000}, "relation_change": -5},
        },
    },
    {
        "description": "Землетрясение разрушило часть инфраструктуры.",
        "option_1": "Восстановить инфраструктуру (-50000 Крон, +5000 Рабочих)",
        "option_2": "Оставить как есть (-20000 Населения, +30000 Крон)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -50000, "Рабочие": 5000}},
            "option_2": {"resource_changes": {"Население": -20000, "Кроны": 30000}},
        },
    },
    {
        "description": "Тайное общество предлагает союз.",
        "option_1": "Принять предложение (+100000 Крон, -8 отношения)",
        "option_2": "Отклонить предложение (-50000 Крон, +5 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": 100000}, "relation_change": -8},
            "option_2": {"resource_changes": {"Кроны": -50000}, "relation_change": 5},
        },
    },
    {
        "description": "СМИ раскрывают коррупцию в правительстве.",
        "option_1": "Начать расследование (-20000 Крон, +3 отношения)",
        "option_2": "Замять скандал (+50000 Крон, -10 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -20000}, "relation_change": 3},
            "option_2": {"resource_changes": {"Кроны": 50000}, "relation_change": -10},
        },
    },
    {
        "description": "Новая технология позволяет увеличить добычу сырья.",
        "option_1": "Внедрить технологию (-70000 Крон, +30000 Сырье)",
        "option_2": "Отказаться от внедрения (+20000 Крон, -5 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -70000, "Сырье": 30000}},
            "option_2": {"resource_changes": {"Кроны": 20000}, "relation_change": -5},
        },
    },
    {
        "description": "Группа беженцев просит убежища.",
        "option_1": "Предоставить убежище (-10000 Крон, +5000 Населения)",
        "option_2": "Отказать (-5000 Населения, +20000 Крон)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -10000, "Население": 5000}},
            "option_2": {"resource_changes": {"Население": -5000, "Кроны": 20000}},
        },
    },
    {
        "description": "Обнаружены древние артефакты.",
        "option_1": "Исследовать находку (-30000 Крон, +10000 Рабочих)",
        "option_2": "Продать артефакты (+50000 Крон, -8 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -30000, "Рабочие": 10000}, "relation_change": 4},
            "option_2": {"resource_changes": {"Кроны": 50000}, "relation_change": -8},
        },
    },
    {
        "description": "Сильные дожди затопили часть территории.",
        "option_1": "Строительство дамбы (-40000 Крон, +5000 Рабочих)",
        "option_2": "Переселить жителей (-10000 Населения, +30000 Крон)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -40000, "Рабочие": 5000}},
            "option_2": {"resource_changes": {"Население": -10000, "Кроны": 30000}},
        },
    },
    {
        "description": "Международный суд требует компенсации.",
        "option_1": "Выплатить компенсацию (-60000 Крон, +5 отношения)",
        "option_2": "Игнорировать требование (+30000 Крон, -12 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -60000}, "relation_change": 5},
            "option_2": {"resource_changes": {"Кроны": 30000}, "relation_change": -12},
        },
    },
    {
        "description": "Новое оборудования для медицины доступно для покупки.",
        "option_1": "Купить (-50000 Крон, +10000 Рабочих)",
        "option_2": "Отказаться от покупки (+20000 Крон, -3 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -50000, "Рабочие": 10000}, "relation_change": 2},
            "option_2": {"resource_changes": {"Кроны": 20000}, "relation_change": -3},
        },
    },
    {
        "description": "Пираты блокируют торговые пути.",
        "option_1": "Отправить флот (-40000 Крон, +20000 Сырье)",
        "option_2": "Искать альтернативные пути (-10000 Крон, -5 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -40000, "Сырье": 20000}},
            "option_2": {"resource_changes": {"Кроны": -10000}, "relation_change": -5},
        },
    },
    {
        "description": "Группа хакеров угрожает атаковать системы.",
        "option_1": "Заплатить выкуп (-30000 Крон, +3 отношения)",
        "option_2": "Активировать защиту (-50000 Крон, -8 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -30000}, "relation_change": 3},
            "option_2": {"resource_changes": {"Кроны": -50000}, "relation_change": -8},
        },
    },
    {
        "description": "Обнаружена неисследованная территория.",
        "option_1": "Организовать экспедицию (-20000 Крон, +10000 Рабочих)",
        "option_2": "Игнорировать находку (+10000 Крон, -2 отношения)",
        "effects": {
            "option_1": {"resource_changes": {"Кроны": -20000, "Рабочие": 10000}, "relation_change": 4},
            "option_2": {"resource_changes": {"Кроны": 10000}, "relation_change": -2},
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