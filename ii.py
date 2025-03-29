import random
import os
import sqlite3

from kivy.uix.label import Label
from kivy.uix.popup import Popup


class AIController:
    def __init__(self, faction):
        self.faction = faction
        self.diplomacy_status = {}
        self.economic_params = {}
        self.cities = {}
        self.all_cities = {}
        self.buildings = {}
        self.garrison = {}
        self.army = {}
        self.money = self.resources.get('Кроны', 0)
        self.workers = self.resources.get('Рабочие', 0)
        self.surie = self.resources.get('Сырье', 0)
        self.population = self.resources.get('Население', 0)
        self.hospitals = self.buildings.get('Больницы', 0)
        self.factory = self.buildings.get('Фабрики', 0)
        self.born_peoples = 0
        self.db_connection = sqlite3.connect('game_data.db')
        self.cursor = self.db_connection.cursor()
        self.resources = {}
        self.relations = {}
        self.load_resources_from_db()
        self.load_relations_from_db()
        self.load_data_fractions()  # Это не трогаем.

    def load_all_data(self):
        self.load_city_for_fractions()

    def load_resources_from_db(self):
        query = "SELECT resource_type, amount FROM resources WHERE faction = ?"
        self.cursor.execute(query, (self.faction,))
        for row in self.cursor.fetchall():
            self.resources[row[0]] = row[1]

    def load_relations_from_db(self):
        query = """
            SELECT faction2, relationship 
            FROM relations 
            WHERE faction1 = ?
        """
        self.cursor.execute(query, (self.faction,))
        for row in self.cursor.fetchall():
            self.relations[row[0]] = row[1]

    def load_city_for_fractions(self):
        """
        Загружает данные о городах из БД для текущей фракции
        """
        try:
            # SQL-запрос для получения данных о городах
            query = """
                SELECT id, name, coordinates 
                FROM cities 
                WHERE faction = ?
            """
            self.cursor.execute(query, (self.faction,))
            rows = self.cursor.fetchall()

            # Преобразуем результаты в нужный формат
            self.all_cities = {
                'cities': [
                    {
                        'id': row[0],
                        'name': row[1],
                        'coordinates': row[2]
                    }
                    for row in rows
                ]
            }

            print(f'Загружены города для фракции {self.faction}:', self.all_cities)

        except Exception as e:
            print(f"Ошибка при загрузке городов для фракции {self.faction}: {e}")

    def load_data_fractions(self):
        self.buildings = self.load_data()
        self.garrison = self.load_data()
        self.resources = self.load_data()
        self.army = self.load_data()
        self.cities = self.load_data()

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
        print(f"ИИ {self.faction}: проверка торговли -> Сырье: {self.resources['Сырье']}, Кроны: {self.resources['Кроны']}")
        if self.resources['Сырье'] >= 13000:
            self.resources['Сырье'] -= 10000
            self.resources['Кроны'] += 25000
            print(f"ИИ {self.faction}: торговля выполнена -> -10,000 сырья, +25,000 крон.")
        else:
            print(f"ИИ {self.faction}: недостаточно сырье для торговли.")

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
        self.resources.setdefault('Сырье', 0)
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

        # Производство и потребление Сырье
        food_production = int(self.factory * 1000)
        food_consumption = int(self.resources['Население'] * coeffs['food_loss'])
        self.resources['Сырье'] += food_production - food_consumption

        # Обновление населения
        if self.resources['Сырье'] > 0:
            self.resources['Население'] += clear_up_peoples
        else:
            # Убыль населения из-за нехватки Сырье
            if self.resources['Население'] > 100:
                loss = int(self.resources['Население'] * 0.45)
            else:
                loss = min(self.resources['Население'], 50)
            self.resources['Население'] -= loss
            self.resources['Рабочие'] = max(0, self.resources['Рабочие'] - loss)

        self.check_trade()
        self.load_and_add_resources()

        # Обеспечение положительных значений ресурсов
        self.resources = {key: max(0, int(value)) for key, value in self.resources.items()}

        # Сохранение ресурсов
        self.save_resources()
        print(f"ИИ {self.faction}: ресурсы обновлены -> {self.resources}")

        # Другие обновления
        self.up_resourcess()


    def up_resourcess(self):
        self.money = self.resources['Кроны']
        self.surie = self.resources['Сырье']
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
        scaled_stats = {
            stat: value * max_units if isinstance(value, (int, float)) else value
            for stat, value in unit_data["stats"].items()
        }

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
                    if stat == "Класс юнита":
                        # Для "Класс юнита" значение не изменяется
                        continue
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

    def calculate_profit(self, resource):
        """Рассчитывает чистую прибыль ресурса."""
        if resource == 'Кроны':
            return self.resources['Кроны'] - (self.hospitals * 100)
        elif resource == 'Сырье':
            production = self.factory * 1000
            consumption = self.resources['Население'] * 1.2
            return production - consumption
        elif resource == 'Рабочие':
            return self.resources['Рабочие'] - (self.hospitals * 30)
        else:
            raise ValueError(f"Неизвестный ресурс: {resource}")

    def check_relations(self):
        """Проверяет отношения с другими ИИ."""
        relation_folder = "files/config/status/dipforce/relations.json"

        try:
            with open(relation_folder, 'r', encoding='utf-8') as relation_file:
                content = relation_file.read().strip()
                if not content:
                    print(f"Файл {relation_folder} пуст.")
                    return

                relation_data = json.loads(content)

                # Проверяем, есть ли данные о текущей фракции
                if self.faction in relation_data.get("relations", {}):
                    self.relations = relation_data["relations"][self.faction]
                else:
                    print(f"Данные о фракции {self.faction} отсутствуют в файле.")

        except FileNotFoundError:
            print(f"Файл {relation_folder} не найден.")
        except json.JSONDecodeError:
            print(f"Ошибка при декодировании JSON в файле {relation_folder}.")
        print(f'Отношения:{self.relations}')

    def show_popup(self, title, message):
        """Создает и отображает всплывающее окно с сообщением."""
        popup = Popup(title=title, size_hint=(0.8, 0.4))
        popup.content = Label(text=message, font_size=16)
        popup.open()

    def check_trade(self):
        self.check_relations()
        """Проверяет выгодность торгового соглашения."""
        trade_folder = "files/config/status/trade_dogovor"
        trade_file_path = transform_filename(os.path.join(trade_folder, f"{self.faction}.json")) # Не трогать эту строчку

        # Проверяем, существует ли файл
        if not os.path.exists(trade_file_path):
            print("Ошибка", f"Файл договора {trade_file_path} не найден.")
            return

        try:
            with open(trade_file_path, 'r', encoding='utf-8') as trade_file:
                content = trade_file.read().strip()
                if not content:
                    print("Ошибка", f"Файл {trade_file_path} пуст.")
                    return

                trade_data = json.loads(content)

                # Получаем данные из файла
                target_faction = trade_data.get("initiator")
                initiator_summ_resource = float(trade_data.get("initiator_summ_resource", 0))
                target_summ_resource = float(trade_data.get("target_summ_resource", 0))
                initiator_type_resource = trade_data.get("initiator_type_resource")

                # Проверяем, есть ли данные о целевой фракции в отношениях
                if target_faction not in self.relations:
                    print(f'Список отношений {self.faction}:', self.relations)
                    print("Ошибка", f"Данные о фракции {target_faction} отсутствуют в отношениях.")
                    return

                # Получаем уровень отношений с целевой фракцией
                relation_level = self.relations[target_faction]

                # Определяем коэффициент на основе уровня отношений
                if relation_level < 15:
                    self.show_popup(f"Отказ от {self.faction}", "Как Вы себе представляете сделку между нами? \n Да мы плевать хотели на Ваше предложение!")
                    self.return_resource_to_player(target_faction, initiator_type_resource, initiator_summ_resource)
                    # Очищаем выполненные сделки из торгового файла
                    with open(trade_file_path, 'w', encoding='utf-8') as file:
                        file.write('')
                    return
                elif 15 <= relation_level < 25:
                    coefficient = 0.08
                elif 25 <= relation_level < 35:
                    coefficient = 0.3
                elif 35 <= relation_level < 50:
                    coefficient = 0.8
                elif 50 <= relation_level < 60:
                    coefficient = 1.0
                elif 60 <= relation_level < 75:
                    coefficient = 1.4
                elif 75 <= relation_level < 90:
                    coefficient = 2.0
                elif 90 <= relation_level <= 100:
                    coefficient = 2.9
                else:
                    return

                # Проверяем соотношение сделки
                trade_ratio = target_summ_resource / initiator_summ_resource

                if trade_ratio > 3.0:
                    self.show_popup(f"Отказ от {self.faction}", "Вы слишком многого от нас хотите, сбавьте требования!")
                    self.return_resource_to_player(target_faction, initiator_type_resource, initiator_summ_resource)
                    # Очищаем выполненные сделки из торгового файла
                    with open(trade_file_path, 'w', encoding='utf-8') as file:
                        file.write('')
                    return

                if trade_ratio <= coefficient:
                    self.trade_resources()  # Вызываем функцию для выполнения сделки
                else:
                    self.show_popup(f"Отказ от {self.faction}", f"Для Вас у нас другие условия по сделкам.\nСбавьте требования или ищите другого поставщика.")
                    self.return_resource_to_player(target_faction, initiator_type_resource, initiator_summ_resource)
                    # Очищаем выполненные сделки из торгового файла
                    with open(trade_file_path, 'w', encoding='utf-8') as file:
                        file.write('')
        except Exception as e:
            print("Ошибка", f"Ошибка при обработке файла {trade_file_path}: {e}")



    def trade_resources(self):
        """ИИ обновляет ресурсы с учетом торговых договоров и всегда записывает ресурсы в файл другой стороны сделки."""
        trade_folder = "files/config/status/trade_dogovor"
        trade_file_path = transform_filename(os.path.join(trade_folder, f"{self.faction}.json"))

        if os.path.exists(trade_file_path):
            try:
                with open(trade_file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()
                    if not content:
                        print(f"Файл {trade_file_path} пуст.")
                        return
                    trade_data = json.loads(content)

                if isinstance(trade_data, dict):
                    trade_data = [trade_data]  # Превращаем в список, если это объект

                completed_trades = []  # Список завершенных сделок

                for trade in trade_data:
                    initiator_type_resource = trade["initiator_type_resource"]
                    initiator_summ_resource = int(trade["initiator_summ_resource"])
                    target_type_resource = trade["target_type_resource"]
                    target_summ_resource = int(trade["target_summ_resource"])

                    if trade["initiator"] == self.faction:
                        # ИИ инициатор сделки (отдает ресурс и получает ресурс от target)
                        if initiator_type_resource == "Сырье" and self.surie < initiator_summ_resource:
                            self.return_resource_to_player(trade, initiator_type_resource, initiator_summ_resource)
                            continue
                        if initiator_type_resource == "Кроны" and self.money < initiator_summ_resource:
                            self.return_resource_to_player(trade, initiator_type_resource, initiator_summ_resource)
                            continue
                        if initiator_type_resource == "Рабочие" and self.workers < initiator_summ_resource:
                            self.return_resource_to_player(trade, initiator_type_resource, initiator_summ_resource)
                            continue

                        # Вычитаем ресурс у ИИ
                        if initiator_type_resource == "Сырье":
                            self.resources['Сырье'] -= initiator_summ_resource
                        elif initiator_type_resource == "Кроны":
                            self.resources['Кроны'] -= initiator_summ_resource
                        elif initiator_type_resource == "Рабочие":
                            self.resources['Рабочие'] -= initiator_summ_resource

                        # Записываем переданный ресурс в файл получателя
                        opponent_faction = transform_filename(trade["target_faction"])
                        ally_resource_file = transform_filename(
                            f"files/config/status/trade_dogovor/resources/{opponent_faction}.json")
                        ally_data = {}

                        if os.path.exists(ally_resource_file):
                            with open(ally_resource_file, 'r', encoding='utf-8') as ally_file:
                                content = ally_file.read().strip()
                                if content:
                                    ally_data = json.loads(content)

                        ally_data[initiator_type_resource] = ally_data.get(initiator_type_resource,
                                                                           0) + initiator_summ_resource

                    elif trade["target_faction"] == self.faction:
                        # ИИ получатель сделки (получает ресурс и отдает свой)
                        if target_type_resource == "Сырье" and self.surie < target_summ_resource:
                            self.return_resource_to_player(trade, initiator_type_resource, initiator_summ_resource)
                            self.show_popup(f"У {self.faction} не хватает ресурсов", f"Напишите нам позже с этим предложением, у нас пока нет этих ресурсов.\nСпасибо за понимание!")
                            continue
                        if target_type_resource == "Кроны" and self.money < target_summ_resource:
                            self.return_resource_to_player(trade, initiator_type_resource, initiator_summ_resource)
                            self.show_popup(f"У {self.faction} не хватает ресурсов", f"Напишите нам позже с этим предложением, у нас пока нет этих ресурсов.\nСпасибо за понимание!")
                            continue
                        if target_type_resource == "Рабочие" and self.workers < target_summ_resource:
                            self.return_resource_to_player(trade, initiator_type_resource, initiator_summ_resource)
                            self.show_popup(f"У {self.faction} не хватает ресурсов", f"Напишите нам позже с этим предложением, у нас пока нет этих ресурсов.\nСпасибо за понимание!")
                            continue

                        # ИИ получает ресурс
                        if initiator_type_resource == "Сырье":
                            self.resources['Сырье'] += initiator_summ_resource
                        elif initiator_type_resource == "Кроны":
                            self.resources['Кроны'] += initiator_summ_resource
                        elif initiator_type_resource == "Рабочие":
                            self.resources['Рабочие'] += initiator_summ_resource

                        # ИИ отдает свой ресурс (отдает взамен)
                        if target_type_resource == "Сырье":
                            self.resources['Сырье'] -= target_summ_resource
                        elif target_type_resource == "Кроны":
                            self.resources['Кроны'] -= target_summ_resource
                        elif target_type_resource == "Рабочие":
                            self.resources['Рабочие'] -= target_summ_resource

                        # Записываем переданный ресурс в файл инициатора (отправляем свой ресурс обратно)
                        opponent_faction = transform_filename(trade["initiator"])
                        ally_resource_file = transform_filename(
                            f"files/config/status/trade_dogovor/resources/{opponent_faction}.json")
                        ally_data = {}

                        if os.path.exists(ally_resource_file):
                            with open(ally_resource_file, 'r', encoding='utf-8') as ally_file:
                                content = ally_file.read().strip()
                                if content:
                                    ally_data = json.loads(content)

                        self.show_popup(f"Согласие на сделку от {self.faction}", f"По рукам.\nВысылаю поставку, скоро прибудет.")
                        ally_data[target_type_resource] = ally_data.get(target_type_resource, 0) + target_summ_resource

                    # Записываем обновленный файл ресурсов союзника
                    with open(ally_resource_file, 'w', encoding='utf-8') as ally_file:
                        json.dump(ally_data, ally_file, ensure_ascii=False, indent=4)

                    completed_trades.append(trade)  # Сделка завершена

                # Очищаем выполненные сделки из торгового файла
                with open(trade_file_path, 'w', encoding='utf-8') as file:
                    json.dump([t for t in trade_data if t not in completed_trades], file, ensure_ascii=False, indent=4)

                self.save_resources()  # Сохраняем обновленные ресурсы ИИ

            except json.JSONDecodeError:
                print(f"Ошибка: файл {trade_file_path} содержит некорректный JSON.")
            except Exception as e:
                print(f"Ошибка при обработке торговых соглашений ИИ: {e}")
        else:
            print(f"Файл торговых соглашений для фракции {self.faction} не найден.")

    def return_resource_to_player(self, trade, resource_type, resource_amount):
        """Возвращает ресурс игроку, если у ИИ недостаточно ресурсов для выполнения сделки."""
        # Определяем имя оппонента
        if isinstance(trade, dict):
            opponent_faction = trade["initiator"]
        elif isinstance(trade, str):
            opponent_faction = trade
        else:
            raise ValueError("Параметр 'trade' должен быть либо словарем, либо строкой.")

        # Формируем путь к файлу ресурсов
        ally_resource_file = transform_filename(
            f"files/config/status/trade_dogovor/resources/{opponent_faction}.json"
        )
        print(f'DEBUG: Путь к файлу ресурсов: {ally_resource_file}')

        # Загружаем данные о ресурсах
        ally_data = {}
        if os.path.exists(ally_resource_file):
            with open(ally_resource_file, 'r', encoding='utf-8') as ally_file:
                content = ally_file.read().strip()
                if content:
                    ally_data = json.loads(content)

        # Обновляем количество ресурсов
        ally_data[resource_type] = ally_data.get(resource_type, 0) + resource_amount
        print(f"DEBUG: Возвращаем {resource_amount} {resource_type} игроку {opponent_faction}.")
        print(f"DEBUG: Обновленные данные: {ally_data}")

        # Сохраняем обновленные данные
        with open(ally_resource_file, 'w', encoding='utf-8') as ally_file:
            json.dump(ally_data, ally_file, ensure_ascii=False, indent=4)

        print(f"Ресурс {resource_type} в количестве {resource_amount} возвращен игроку {opponent_faction}.")

    def load_and_add_resources(self):

        try:
            # Проверяем, существует ли файл
            if not os.path.exists(self.resources_file):
                print(f"Файл {self.resources_file} не найден. Пропуск.")
                return

            # Чтение данных из файла
            with open(self.resources_file, 'r', encoding='utf-8') as file:
                content = file.read().strip()

                if not content:
                    print(f"Файл {self.resources_file} пустой. Пропуск.")
                    return

                # Парсим JSON из содержимого файла
                loaded_resources = json.loads(content)

            # Проверяем, что ресурсы являются словарем
            if not isinstance(loaded_resources, dict):
                raise ValueError(f"Формат данных в файле {self.resources_file} некорректен. Ожидался словарь.")

            # Добавляем ресурсы из файла к текущим
            for key, value in loaded_resources.items():
                if key in self.resources and isinstance(value, (int, float)):
                    self.resources[key] += value
                else:
                    print(f"Ресурс '{key}' не найден в текущем списке или имеет некорректное значение.")

            print(f"Ресурсы из файла {self.resources_file} успешно добавлены.")
            print(f"Обновленные ресурсы: {self.resources}")

        except json.JSONDecodeError:
            print(f"Ошибка: Файл {self.resources_file} содержит некорректный JSON.")
        except Exception as e:
            print(f"Произошла ошибка при обработке файла {self.resources_file}: {e}")

    def manage_army(self):
        """Управление армией ИИ"""
        self.build_army()

    def manage_relations(self):
        """Управление отношениями только для фракций, заключивших дипломатическое соглашение"""
        my_fraction = translation_dict.get(self.faction)
        faction_dir_path = os.path.join(self.relations_path, my_fraction)

        if not os.path.exists(faction_dir_path):
            print(f"Путь {faction_dir_path} не существует.")
            return

        relations_data = self.load_relations()

        if self.faction not in relations_data["relations"]:
            print(f"Отношения для фракции {self.faction} не найдены.")
            return

        # Перебираем файлы в директории, обрабатываем только тех, с кем заключены соглашения
        for filename in os.listdir(faction_dir_path):
            if filename.endswith(".json"):
                faction_name_en = filename.replace('.json', '')
                faction_name_ru = reverse_translation_dict.get(faction_name_en, faction_name_en)

                # Проверяем, есть ли дипломатическое соглашение
                if faction_name_ru in relations_data["relations"][self.faction]:
                    current_value_self = relations_data["relations"][self.faction][faction_name_ru]
                    current_value_other = relations_data["relations"][faction_name_ru][self.faction]

                    relations_data["relations"][self.faction][faction_name_ru] = min(current_value_self + 7, 100)
                    relations_data["relations"][faction_name_ru][self.faction] = min(current_value_other + 7, 100)

                # Удаляем обработанный файл (чтобы это изменение было одноразовым)
                os.remove(os.path.join(faction_dir_path, filename))

        # Сохраняем обновленные данные
        self.save_relations(relations_data)

    def load_relations(self):
        """Загружаем текущие отношения из файла relations.json"""
        try:
            with open(self.relations_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Файл relations.json не найден. Создаем новый.")
            return {"relations": {}}

    def save_relations(self, relations_data):
        """Сохраняем обновленные отношения в файл relations.json"""
        try:
            with open(self.relations_file, "w", encoding="utf-8") as f:
                json.dump(relations_data, f, ensure_ascii=False, indent=4)
        except PermissionError:
            print("Ошибка доступа к файлу relations.json. Проверьте права доступа.")


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
        self.manage_relations()
        self.load_all_data()
        self.load_data_fractions()
        # Экономические действия
        self.build_buildings()
        # Военные действия
        self.manage_army()
        # Дипломатические действия
        self.manage_politics()
