import random
import json
import os

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

class AIController:
    def __init__(self, faction):
        self.faction = faction
        self.diplomacy_status = {}
        self.economic_params = {}
        self.bulidings_path = transform_filename(f'files/config/buildings_in_city/{self.faction}_buildings_city.json')
        self.garrison_path = transform_filename(f'files/config/manage_ii/{self.faction}_in_city.json')
        self.resources_path = transform_filename(f'files/config/manage_ii/resources/{self.faction}_resources.json')
        self.bulidings = {}
        self.garrison = {}
        self.resources = {}
        self.load_data_fractions()
        self.money = self.resources.get('Кроны', 0)
        self.workers = self.resources.get('Рабочие', 0)
        self.food = self.resources.get('Еда', 0)
        self.population = self.resources.get('Население', 0)
        self.hospitals = self.bulidings.get('Больницы', 0)
        self.factory = self.bulidings.get('Фабрики', 0)
        self.born_peoples = 0
        self.process_turn()

    def load_data(self, file_path):
        if not os.path.exists(file_path):
            print(f"Файл {file_path} не найден. Данные будут инициализированы пустым словарем.")
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Ошибка загрузки данных из {file_path}: {e}. Инициализация пустым словарем.")
            return {}

    def load_data_fractions(self):
        self.bulidings = self.load_data(self.bulidings_path)
        self.garrison = self.load_data(self.garrison_path)
        self.resources = self.load_data(self.resources_path)

    def unqiue_fraction_tax_rate(self):
        rates = {
            "Хиперион": 0.02,
            "Этерия": 0.012,
            "Халидон": 0.01,
            "Аркадия": 0.03,
            "Селестия": 0.015
        }
        tax_rate = rates.get(self.faction, 0)
        self.economic_params = {self.faction: {"tax_rate": tax_rate}}
        return self.economic_params

    def get_hospital_count(self):
        """Получить общее количество больниц в зданиях."""
        hospital_count = 0
        for city, data in self.bulidings.items():
            hospital_count += data.get("Здания", {}).get("Больница", 0)
        return hospital_count

    def get_factory_count(self):
        """Получить общее количество фабрик в зданиях."""
        factory_count = 0
        for city, data in self.bulidings.items():
            factory_count += data.get("Здания", {}).get("Фабрика", 0)
        return factory_count

    def update_resources(self):
        """Обновление ресурсов для ИИ."""
        # Коэффициенты для фракций
        faction_coefficients = {
            'Аркадия': {'free_peoples_gain': 190, 'free_peoples_loss': 30, 'money_loss': 100, 'food_gain': 600,
                        'food_loss': 1.2},
            'Селестия': {'free_peoples_gain': 170, 'free_peoples_loss': 20, 'money_loss': 200, 'food_gain': 540,
                         'food_loss': 1.1},
            'Хиперион': {'free_peoples_gain': 210, 'free_peoples_loss': 40, 'money_loss': 200, 'food_gain': 530,
                         'food_loss': 0.9},
            'Этерия': {'free_peoples_gain': 240, 'free_peoples_loss': 60, 'money_loss': 300, 'food_gain': 500,
                       'food_loss': 0.5},
            'Халидон': {'free_peoples_gain': 230, 'free_peoples_loss': 50, 'money_loss': 300, 'food_gain': 500,
                        'food_loss': 0.4},
        }

        # Проверяем фракцию
        coeffs = faction_coefficients.get(self.faction)
        if not coeffs:
            raise ValueError(f"Фракция '{self.faction}' не найдена.")

        # Пересчет ресурсов
        tax_rate = self.unqiue_fraction_tax_rate().get(self.faction, {}).get("tax_rate", 0)
        self.born_peoples = int(self.hospitals * 500)
        self.workers = int(self.factory * 200)

        clear_up_peoples = self.born_peoples - self.workers
        self.resources['Рабочие'] += clear_up_peoples
        self.resources['Кроны'] += int(tax_rate * self.resources['Население'] - self.hospitals * coeffs['money_loss'])

        # Производство еды фабриками
        food_production = int(self.factory * 1000)
        food_consumption = int(self.resources['Население'] * coeffs['food_loss'])
        self.resources['Еда'] += food_production - food_consumption

        # Логика изменения населения
        if self.resources['Еда'] > 0:
            self.resources['Население'] += clear_up_peoples
        else:
            if self.resources['Население'] > 100:
                loss = int(self.resources['Население'] * 0.45)
            else:
                loss = min(self.resources['Население'], 50)
            self.resources['Население'] -= loss
            self.resources['Рабочие'] = max(0, self.resources['Рабочие'] - loss)

        # Проверка на отрицательные значения
        self.resources = {key: max(0, int(value)) for key, value in self.resources.items()}

        # Сохранение обновленных данных
        self.save_resources()
        print(f"ИИ {self.faction}: ресурсы обновлены -> {self.resources}")

    def save_resources(self):
        """Записывает текущее состояние ресурсов в файл."""
        resources_data = {
            'Кроны': self.money,
            'Рабочие': self.workers,
            'Еда': self.food,
            'Население': self.population
        }

        try:
            with open(self.resources_path, 'w') as file:
                json.dump(resources_data, file, ensure_ascii=False, indent=4)  # Запись с индентацией для удобства
        except Exception as e:
            print(f"Ошибка при сохранении ресурсов: {e}")

    def diplomacy_status_update(self):
        with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
            self.diplomacy_status = json.load(file)

    def process_turn(self):
        """Обработка хода ИИ фракции"""
        #print(f"ИИ {self.faction} делает ход...")
        self.update_resources()
        # Экономические действия
        self.build_buildings()
        # Военные действия
        self.manage_army()

        # Дипломатические действия
        self.manage_politics()


    def build_buildings(self):
        """Построить экономические объекты"""
        if self.resources['Кроны'] >= 500:
            self.factory += 1
            self.hospitals += 1
            self.resources['Кроны'] -= 500


    def build_army(self):
        pass

    def trade_resources(self):
        """Торговля ресурсами с другими фракциями"""
        if self.resources['money'] >= 100:
            self.resources['money'] -= 100
            self.resources['people'] += 50
            #print(f"{self.faction} торгует. Деньги: {self.resources['money']}, Люди: {self.resources['people']}")
        else:
            pass  #print(f"{self.faction} не хватает денег для торговли.")

    def expand_economy(self):
        """Расширение экономики (например, колонизация или захват территорий)"""
        if self.resources['people'] >= 100:
            self.resources['people'] -= 100
            self.economy_level += 0.5
            #print(f"{self.faction} расширяет экономику. Новый уровень экономики: {self.economy_level}")
        else:
            pass  #print(f"{self.faction} не хватает людей для расширения экономики.")

    def manage_army(self):
        """Управление армией ИИ"""
        action = random.choice(['train', 'attack', 'defend'])
        if action == 'train':
            self.train_army()
        elif action == 'attack':
            self.attack_enemy()
        elif action == 'defend':
            self.defend_territory()

    def train_army(self):
        """Тренировка войск"""
        if self.resources['money'] >= 150:
            self.army_strength += 1
            self.resources['money'] -= 150
            #print(f"{self.faction} тренирует войска. Сила армии: {self.army_strength}")
        else:
            pass  #print(f"{self.faction} не хватает средств для тренировки армии.")

    def attack_enemy(self):
        """Атака на соседнюю фракцию"""
        if self.army_strength > 2:
            target = random.choice(list(self.diplomacy_status.keys()))
            print(f"{self.faction} атакует {target}.")
            # Логика успеха атаки
            success = random.random() < 0.5
            if success:
                pass  #print(f"Атака {self.faction} на {target} была успешной!")
            else:
                pass  #print(f"Атака {self.faction} на {target} провалилась.")
        else:
            pass  #print(f"{self.faction} армия слишком слаба для атаки.")

    def defend_territory(self):
        """Защита территории"""
        #print(f"{self.faction} готовится к защите.")

    def manage_politics(self):
        """Управление дипломатией ИИ"""
        if len(self.diplomacy_status) > 0:
            target = random.choice(list(self.diplomacy_status.keys()))
            action = random.choice(['ally', 'negotiate', 'betray'])
            if action == 'ally':
                self.form_alliance(target)
            elif action == 'negotiate':
                self.negotiate_peace(target)
            elif action == 'betray':
                self.betray_ally(target)

    def form_alliance(self, target):
        """Создание альянса"""
        pass

    def negotiate_peace(self, target):
        """Переговоры о мире"""
        pass

    def betray_ally(self, target):
        """Предательство альянса"""
        pass
