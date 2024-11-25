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
        """
        Загружает данные из указанного JSON-файла.
        Если файл отсутствует, пуст или некорректен, возвращается пустой словарь.
        """
        if not os.path.exists(file_path):
            print(f"Файл {file_path} не найден. Данные будут инициализированы пустым словарем.")
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()  # Удаляем лишние пробелы и символы новой строки
                if not content:  # Проверяем, пуст ли файл
                    print(f"Файл {file_path} пуст. Инициализация пустым словарем.")
                    return {}
                data = json.loads(content)  # Загружаем JSON из содержимого файла
            return data
        except UnicodeDecodeError as e:
            print(f"Ошибка кодировки в файле {file_path}: {e}. Инициализация пустым словарем.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Ошибка загрузки данных из {file_path}: {e}. Инициализация пустым словарем.")
            return {}
        except Exception as e:
            print(f"Неожиданная ошибка при загрузке {file_path}: {e}. Инициализация пустым словарем.")
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

        coeffs = faction_coefficients.get(self.faction)
        if not coeffs:
            raise ValueError(f"Фракция '{self.faction}' не найдена.")

        # Инициализируем значения по умолчанию
        self.resources.setdefault('Рабочие', 0)
        self.resources.setdefault('Кроны', 0)
        self.resources.setdefault('Еда', 0)
        self.resources.setdefault('Население', 0)

        tax_rate = self.unqiue_fraction_tax_rate().get(self.faction, {}).get("tax_rate", 0)
        self.born_peoples = int(self.hospitals * 500)
        self.workers = int(self.factory * 200)

        clear_up_peoples = self.born_peoples - self.workers
        self.resources['Рабочие'] += clear_up_peoples
        self.resources['Кроны'] += int(tax_rate * self.resources['Население'] - self.hospitals * coeffs['money_loss'])

        food_production = int(self.factory * 1000)
        food_consumption = int(self.resources['Население'] * coeffs['food_loss'])
        self.resources['Еда'] += food_production - food_consumption

        if self.resources['Еда'] > 0:
            self.resources['Население'] += clear_up_peoples
        else:
            if self.resources['Население'] > 100:
                loss = int(self.resources['Население'] * 0.45)
            else:
                loss = min(self.resources['Население'], 50)
            self.resources['Население'] -= loss
            self.resources['Рабочие'] = max(0, self.resources['Рабочие'] - loss)

        self.resources = {key: max(0, int(value)) for key, value in self.resources.items()}

        self.save_resources()
        print(f"ИИ {self.faction}: ресурсы обновлены -> {self.resources}")


    def save_resources(self):
        """Записывает текущее состояние ресурсов в файл."""
        try:
            with open(self.resources_path, 'w', encoding='utf-8') as file:
                json.dump(self.resources, file, ensure_ascii=False, indent=4)
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
        pass

    def expand_economy(self):
        """Расширение экономики (например, колонизация или захват территорий)"""
        pass

    def manage_army(self):
        """Управление армией ИИ"""
        pass

    def train_army(self):
        """Тренировка войск"""
        pass
    def attack_enemy(self):
        """Атака на соседнюю фракцию"""
        pass

    def defend_territory(self):
        """Защита территории"""
        #print(f"{self.faction} готовится к защите.")

    def manage_politics(self):
        """Управление дипломатией ИИ"""
        pass

    def form_alliance(self, target):
        """Создание альянса"""
        pass

    def negotiate_peace(self, target):
        """Переговоры о мире"""
        pass

    def betray_ally(self, target):
        """Предательство альянса"""
        pass
