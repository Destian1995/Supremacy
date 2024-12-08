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
    print(f"Original path: {file_path}")
    path_parts = file_path.split('/')
    for i, part in enumerate(path_parts):
        for ru_name, en_name in translation_dict.items():
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)
    transformed_path = '/'.join(path_parts)
    print(f"Transformed path: {transformed_path}")
    return transformed_path


class AIController:
    def __init__(self, faction):
        self.faction = faction
        self.diplomacy_status = {}
        self.economic_params = {}
        self.buildings_path = transform_filename(f'files/config/buildings_in_city/{self.faction}_buildings_city.json')
        self.garrison_path = transform_filename(f'files/config/manage_ii/{self.faction}_in_city.json')
        self.resources_path = transform_filename(f'files/config/manage_ii/resources/{self.faction}_resources.json')
        self.army_path = transform_filename(f'files/config/units/{self.faction}.json')
        self.cities_path = transform_filename(f'files/config/manage_ii/list_cities/{self.faction}.json')
        self.cities = {}
        self.all_cities = {}
        self.buildings = {}
        self.garrison = {}
        self.resources = {}
        self.army = {}
        self.money = self.resources.get('Кроны', 0)
        self.workers = self.resources.get('Рабочие', 0)
        self.food = self.resources.get('Еда', 0)
        self.population = self.resources.get('Население', 0)
        self.hospitals = self.buildings.get('Больницы', 0)
        self.factory = self.buildings.get('Фабрики', 0)
        self.born_peoples = 0
        self.load_data_fractions()  # Это не трогаем.

    def load_all_data(self):
        self.load_city_for_fractions()

    def load_city_for_fractions(self):
        with open('files/config/cities.json', 'r', encoding='utf-8') as file:
            all_city = json.load(file)

        print('all_city', all_city)
        self.all_cities = all_city

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
        self.buildings = self.load_data(self.buildings_path)
        self.garrison = self.load_data(self.garrison_path)
        self.resources = self.load_data(self.resources_path)
        self.army = self.load_data(self.army_path)
        self.cities = self.load_data(self.cities_path)

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
        for city, data in self.buildings.items():
            hospital_count += data.get("Здания", {}).get("Больница", 0)
        return hospital_count

    def get_factory_count(self):
        """Получить общее количество фабрик в зданиях."""
        factory_count = 0
        for city, data in self.buildings.items():
            factory_count += data.get("Здания", {}).get("Фабрика", 0)
        return factory_count

    def build_buildings(self):
        """Построить экономические объекты"""

        def update_buildings(city, hospital_incr, factory_incr, coordinates):
            """Обновление данных о зданиях и координатах в указанном городе"""
            try:
                with open(self.buildings_path, 'r', encoding='utf-8') as file:
                    buildings_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                buildings_data = {}

            if city not in buildings_data:
                buildings_data[city] = {
                    "Здания": {"Больница": 0, "Фабрика": 0},
                    "Координаты": coordinates,
                }

            buildings_data[city]["Здания"]["Больница"] += hospital_incr
            buildings_data[city]["Здания"]["Фабрика"] += factory_incr

            with open(self.buildings_path, 'w', encoding='utf-8') as file:
                json.dump(buildings_data, file, ensure_ascii=False, indent=4)

        def get_city_coordinates(city_name):
            """Получить координаты города по его названию"""
            for city in self.all_cities['cities']:
                if city['name'].strip().lower() == city_name.strip().lower():
                    print(f"Город {city_name} найден в all_cities.")
                    return city['coordinates']
            print(f"Город {city_name} не найден в all_cities.")
            return None

        def build_resources(cost, hospital_incr, factory_incr):
            """Основная логика строительства"""
            self.resources['Кроны'] -= cost
            self.factory += factory_incr
            self.hospitals += hospital_incr

            with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
                diplomaties = json.load(file)
            if self.faction in diplomaties:
                cities = diplomaties[self.faction].get('города', [])
                if not cities:
                    print("Нет доступных городов для фракции:", self.faction)
                    return

                chosen_city = random.choice(cities)
                city_coordinates = get_city_coordinates(chosen_city)

                if city_coordinates is None:
                    print(f"Координаты для города {chosen_city} не найдены.")
                    return

                update_buildings(chosen_city, hospital_incr, factory_incr, city_coordinates)
                print(f"Построены здания в городе {chosen_city} фракции {self.faction}.")
                print(f'переданные координаты {city_coordinates}')
            else:
                print("Фракция не найдена в конфигурации:", self.faction)

        if self.resources['Кроны'] >= 50000:
            build_resources(cost=35000, hospital_incr=50, factory_incr=100)
        elif self.resources['Кроны'] >= 1000:
            build_resources(cost=700, hospital_incr=1, factory_incr=2)

    def trade_resource(self):
        print(f"ИИ {self.faction}: проверка торговли -> Еда: {self.resources['Еда']}, Кроны: {self.resources['Кроны']}")
        if self.resources['Еда'] >= 14000:
            self.resources['Еда'] -= 10000
            self.resources['Кроны'] += 30000
            print(f"ИИ {self.faction}: торговля выполнена -> -10,000 еды, +30,000 крон.")
        else:
            print(f"ИИ {self.faction}: недостаточно еды для торговли.")

    def update_resources(self):
        """Обновление ресурсов для ИИ."""
        faction_coefficients = {
            'Аркадия': {'free_peoples_gain': 190, 'free_peoples_loss': 30, 'money_loss': 100, 'food_gain': 600,
                        'food_loss': 1.4},
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

        tax_rate = 0.35  # Базовая налоговая ставка (35%)
        self.born_peoples = int(self.hospitals * 500)
        self.workers = int(self.factory * 200)

        # Расчет прироста населения
        clear_up_peoples = self.born_peoples - self.workers
        self.resources['Рабочие'] += clear_up_peoples

        # Налоги: доход от населения с учетом ставки
        tax_income = int(tax_rate * self.resources['Население'])
        self.resources['Кроны'] += tax_income - self.hospitals * coeffs['money_loss']

        # Производство и потребление еды
        food_production = int(self.factory * 1000)
        food_consumption = int(self.resources['Население'] * coeffs['food_loss'])
        self.resources['Еда'] += food_production - food_consumption

        # Обновление населения
        if self.resources['Еда'] > 0:
            self.resources['Население'] += clear_up_peoples
        else:
            # Убыль населения из-за нехватки еды
            if self.resources['Население'] > 100:
                loss = int(self.resources['Население'] * 0.45)
            else:
                loss = min(self.resources['Население'], 50)
            self.resources['Население'] -= loss
            self.resources['Рабочие'] = max(0, self.resources['Рабочие'] - loss)
        self.trade_resource()

        # Обеспечение положительных значений ресурсов
        self.resources = {key: max(0, int(value)) for key, value in self.resources.items()}

        # Сохранение ресурсов
        self.save_resources()
        print(f"ИИ {self.faction}: ресурсы обновлены -> {self.resources}")

        # Другие обновления
        self.up_resourcess()

    def up_resourcess(self):
        self.money = self.resources['Кроны']
        self.food = self.resources['Еда']
        self.population = self.resources['Население']
        self.workers = self.resources['Рабочие']
        print('Общее число зданий:', self.hospitals, self.factory, 'фракции:', self.faction)

    def save_resources(self):
        """Записывает текущее состояние ресурсов в файл."""
        try:
            with open(self.resources_path, 'w', encoding='utf-8') as file:
                json.dump(self.resources, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при сохранении ресурсов: {e}")

    def diplomacy_status_update(self):
        # Загрузка данных из файла
        with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Проверка наличия текущей фракции в данных и обновление отношений
        if self.faction in data:
            self.diplomacy_status = data[self.faction]["отношения"]
        else:
            print(f"Фракция {self.faction} не найдена в файле diplomaties.json.")
            self.diplomacy_status = {}

    def build_army(self):
        # Проверка наличия доступных юнитов в армии
        if not self.army:
            print(f"ИИ {self.faction}: отсутствуют доступные юниты для найма.")
            return False

        # Проверка на минимальное количество ресурсов для найма
        if self.resources.get('Кроны', 0) < 30000 and self.resources.get('Рабочие', 0) < 2000:
            print('Не хватает ресурсов')
            return False

        # Определение оптимального юнита по защите и возможному количеству найма
        best_unit = max(
            self.army.items(),
            key=lambda unit: (
                    min(
                        self.resources['Кроны'] // unit[1]['cost'][0],  # Максимально доступное количество по Кронам
                        self.resources['Рабочие'] // unit[1]['cost'][1]  # Максимально доступное количество по Рабочим
                    ) * unit[1]['stats']['Защита']  # Умножаем на защиту юнита
            )
        )

        unit_name, unit_data = best_unit
        unit_cost_crowns, unit_cost_workers = unit_data['cost']

        # Рассчитываем максимальное количество юнитов для найма
        max_units = min(
            self.resources['Кроны'] // unit_cost_crowns,
            self.resources['Рабочие'] // unit_cost_workers
        )

        if max_units == 0:
            print(f"ИИ {self.faction}: недостаточно средств для найма {unit_name}.")
            return False

        # Списание ресурсов
        total_crowns = unit_cost_crowns * max_units
        total_workers = unit_cost_workers * max_units
        self.resources['Кроны'] -= total_crowns
        self.resources['Рабочие'] -= total_workers

        # Проверка наличия зданий для выбора города
        if not self.buildings:
            print(f"ИИ {self.faction}: нет данных о зданиях.")
            return False

        # Определяем город с наибольшим количеством зданий
        target_city = max(
            self.buildings.items(),
            key=lambda city: sum(city[1]['Здания'].values())
        )[0]

        # Получаем координаты города из словаря self.all_cities
        city_coordinates = self.buildings.get(target_city, {}).get("Координаты")

        if city_coordinates is None:
            print(f"ИИ {self.faction}: Не найдены координаты для города {target_city}.")
            return False

        # Масштабируем характеристики юнита на количество
        scaled_stats = {stat: value * max_units for stat, value in unit_data["stats"].items() if
                        isinstance(value, (int, float))}

        # Формируем запись юнита
        unit_record = {
            "unit_image": unit_data["image"],
            "unit_name": unit_name,
            "unit_count": max_units,
            "units_stats": scaled_stats
        }

        # Загрузка текущих данных гарнизона
        garrison_data = self.load_data(self.garrison_path)

        # Проверяем, есть ли город в данных гарнизона
        if target_city in garrison_data:
            city_garrison = garrison_data[target_city][0]
            existing_unit = next(
                (unit for unit in city_garrison["units"] if unit["unit_name"] == unit_name),
                None
            )
            if existing_unit:
                # Если юнит уже есть, увеличиваем его количество и характеристики
                existing_count = existing_unit["unit_count"]
                new_count = existing_count + max_units

                # Обновление характеристик с учетом нового количества
                for stat, value in scaled_stats.items():
                    existing_value = existing_unit["units_stats"].get(stat, 0)
                    existing_unit["units_stats"][stat] = existing_value + value

                # Обновляем общее количество юнитов
                existing_unit["unit_count"] = new_count
            else:
                # Если юнит не найден, добавляем новый
                city_garrison["units"].append(unit_record)
        else:
            # Если города нет, создаем новую запись
            garrison_data[target_city] = [
                {
                    "coordinates": city_coordinates,
                    "units": [unit_record]
                }
            ]

        # Сохранение обновленных данных гарнизона
        self.save_data(self.garrison_path, garrison_data)

        # Сохранение обновленных данных ресурсов
        self.save_data(self.resources_path, self.resources)

        print(f"ИИ {self.faction}: нанято {max_units} юнитов '{unit_name}' и отправлено в город {target_city}.")
        return True

    @staticmethod
    def save_data(file_path, data):
        """
        Сохраняет данные в указанный JSON-файл.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(f"Данные успешно сохранены в {file_path}.")
        except Exception as e:
            print(f"Ошибка сохранения данных в {file_path}: {e}")

    def trade_resources(self):
        """Торговля ресурсами с другими фракциями"""
        pass

    def expand_economy(self):
        """Расширение экономики (например, колонизация или захват территорий)"""
        pass

    def manage_army(self):
        """Управление армией ИИ"""
        self.build_army()

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

    def make_turn(self):
        """Обработка хода ИИ фракции"""
        #print(f"ИИ {self.faction} делает ход...")
        self.update_resources()
        self.load_all_data()
        self.load_data_fractions()
        # Экономические действия
        self.build_buildings()
        # Военные действия
        self.manage_army()
        # Дипломатические действия
        self.manage_politics()
