import sqlite3
import random


class AIController:
    def __init__(self, faction, db_path='game_data.db'):
        self.faction = faction
        self.turn = 0
        self.db_connection = sqlite3.connect(db_path)
        self.cursor = self.db_connection.cursor()
        self.resources = {"Кроны": 0, "Сырье": 0, "Рабочие": 0, "Население": 0}
        self.garrison = self.load_garrison()
        self.relations = self.load_relations()
        self.buildings = {}
        self.turn_count = 0
        self.hospitals = 0
        self.factories = 0
        self.taxes = 0
        self.food_info = 0
        self.work_peoples = 0
        self.money_info = 0
        self.born_peoples = 0
        self.money_up = 0
        self.taxes_info = 0
        self.food_peoples = 0
        self.tax_effects = 0
        self.total_consumption = 0
        self.army = self.load_army()
        self.cities = self.load_cities()
        # Инициализация ресурсов по умолчанию
        self.money = 2000
        self.free_peoples = 0
        self.raw_material = 0
        self.population = 100
        self.resources = {
            'Кроны': self.money,
            'Рабочие': self.free_peoples,
            'Сырье': self.raw_material,
            'Население': self.population
        }

    # Методы загрузки данных из БД
    def load_resources(self):
        """
        Загружает текущие ресурсы фракции из таблицы resources.
        """
        try:
            self.cursor.execute('''
                SELECT resource_type, amount
                FROM resources
                WHERE faction = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()



            # Обновление ресурсов на основе данных из базы данных
            for resource_type, amount in rows:
                if resource_type == "Кроны":
                    self.money = amount
                elif resource_type == "Рабочие":
                    self.free_peoples = amount
                elif resource_type == "Сырье":
                    self.raw_material = amount
                elif resource_type == "Население":
                    self.population = amount

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке ресурсов: {e}")

    def load_buildings(self):
        """
        Загружает данные о зданиях для текущей фракции из таблицы buildings.
        """
        try:
            self.cursor.execute('''
                SELECT city_name, building_type, count 
                FROM buildings 
                WHERE faction = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Сброс текущих данных о зданиях
            self.cities_buildings = {}
            total_hospitals = 0
            total_factories = 0

            for row in rows:
                city_name, building_type, count = row
                if city_name not in self.cities_buildings:
                    self.cities_buildings[city_name] = {"Больница": 0, "Фабрика": 0}

                # Обновление данных для конкретного города
                if building_type == "Больница":
                    self.cities_buildings[city_name]["Больница"] += count
                    total_hospitals += count
                elif building_type == "Фабрика":
                    self.cities_buildings[city_name]["Фабрика"] += count
                    total_factories += count

            # Обновление глобальных показателей
            self.hospitals = total_hospitals
            self.factories = total_factories

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке зданий: {e}")

    def load_relations(self):
        """
        Загружает отношения текущей фракции с остальными из базы данных.
        Возвращает словарь, где ключи — названия фракций, а значения — уровни отношений.
        """
        try:
            # Выполняем запрос к таблице relations
            self.cursor.execute('''
                SELECT faction2, relationship
                FROM relations
                WHERE faction1 = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь
            relations = {faction2: relationship for faction2, relationship in rows}
            return relations

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений: {e}")
            return {}

    def load_garrison(self):
        """
        Загружает гарнизон фракции из базы данных.
        Использует JOIN с таблицей units для фильтрации по faction.
        """
        try:
            # SQL-запрос с JOIN для получения гарнизона
            query = """
                SELECT g.city_id, g.unit_name, g.unit_count, u.faction
                FROM garrisons g
                JOIN units u ON g.unit_name = u.unit_name
                WHERE u.faction = ?
            """
            self.cursor.execute(query, (self.faction,))
            rows = self.cursor.fetchall()
            garrison = {}
            for row in rows:
                city_name, unit_name, count, faction = row
                if faction != self.faction:
                    continue  # Пропускаем юниты, не принадлежащие текущей фракции
                if city_name not in garrison:
                    garrison[city_name] = []
                garrison[city_name].append({
                    "unit_name": unit_name,
                    "unit_count": count
                })
            print(f"Гарнизон для фракции {self.faction} успешно загружен: {garrison}")
            return garrison
        except Exception as e:
            print(f"Ошибка при загрузке гарнизона для фракции {self.faction}: {e}")
            return {}

    def load_army(self):
        query = """
            SELECT unit_name, cost_money, cost_time, attack, defense, durability, unit_class 
            FROM units 
            WHERE faction = ?
        """
        self.cursor.execute(query, (self.faction,))
        return {
            row[0]: {  # unit_name
                "cost": {  # Стоимость юнита
                    "money": row[1],  # cost_money
                    "time": row[2]  # cost_time
                },
                "stats": {  # Характеристики юнита
                    "Атака": row[3],
                    "Защита": row[4],
                    "Прочность": row[5],
                    "Класс": row[6]
                }
            } for row in self.cursor.fetchall()
        }

    def load_cities(self):
        """
        Загружает список городов для текущей фракции из таблицы cities.
        Выводит отладочную информацию о загруженных городах.
        """
        try:
            # SQL-запрос для получения списка городов
            query = """
                SELECT id, name 
                FROM cities 
                WHERE faction = ?
            """
            self.cursor.execute(query, (self.faction,))
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь {id: name}
            cities = {row[0]: row[1] for row in rows}

            # Отладочный вывод: информация о загруженных городах
            print(f"Загружены города для фракции '{self.faction}':")
            if cities:
                for city_id, city_name in cities.items():
                    print(f"  ID: {city_id}, Название: {city_name}")
            else:
                print("  Города не найдены.")

            return cities
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке городов для фракции '{self.faction}': {e}")
            return {}

    # Методы сохранения данных в БД
    def save_resources_to_db(self):
        """
        Сохраняет текущие ресурсы фракции в таблицу resources.
        """
        try:
            for resource_type, amount in self.resources.items():
                # Сначала проверяем, существует ли запись
                self.cursor.execute('''
                    SELECT amount
                    FROM resources
                    WHERE faction = ? AND resource_type = ?
                ''', (self.faction, resource_type))
                existing_record = self.cursor.fetchone()

                if existing_record:
                    # Обновляем существующую запись
                    self.cursor.execute('''
                        UPDATE resources
                        SET amount = ?
                        WHERE faction = ? AND resource_type = ?
                    ''', (amount, self.faction, resource_type))
                else:
                    # Создаем новую запись
                    self.cursor.execute('''
                        INSERT INTO resources (faction, resource_type, amount)
                        VALUES (?, ?, ?)
                    ''', (self.faction, resource_type, amount))

            # Сохраняем изменения
            self.db_connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении ресурсов: {e}")

    def save_buildings(self):
        """
        Сохраняет данные о зданиях в базу данных.
        Удаляет старые записи для текущей фракции и добавляет новые.
        """
        try:
            # Удаляем старые записи для текущей фракции
            self.cursor.execute("DELETE FROM buildings WHERE faction = ?", (self.faction,))

            # Вставляем новые записи для каждого города и типа здания
            for city_name, data in self.buildings.items():
                for building_type, count in data["Здания"].items():
                    if count > 0:  # Сохраняем только те здания, количество которых больше 0
                        self.cursor.execute("""
                            INSERT INTO buildings (faction, city_name, building_type, count)
                            VALUES (?, ?, ?, ?)
                        """, (self.faction, city_name, building_type, count))

            # Сохраняем изменения в базе данных
            self.db_connection.commit()
            print("Данные о зданиях успешно сохранены в БД.")
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении данных о зданиях: {e}")

    def save_buildings_to_db(self):
        """
        Сохраняет текущие значения больниц и фабрик в базу данных.
        """
        try:
            # Удаляем старые записи для текущей фракции
            self.cursor.execute("""
                DELETE FROM buildings
                WHERE faction = ?
            """, (self.faction,))

            # Вставляем новые записи
            for city_name, data in self.buildings.items():
                hospital_count = data["Здания"]["Больница"]
                factory_count = data["Здания"]["Фабрика"]

                if hospital_count > 0:
                    self.cursor.execute("""
                        INSERT INTO buildings (faction, city_name, building_type, count)
                        VALUES (?, ?, ?, ?)
                    """, (self.faction, city_name, "Больница", hospital_count))

                if factory_count > 0:
                    self.cursor.execute("""
                        INSERT INTO buildings (faction, city_name, building_type, count)
                        VALUES (?, ?, ?, ?)
                    """, (self.faction, city_name, "Фабрика", factory_count))

            # Сохраняем изменения
            self.db_connection.commit()
            print("Данные о зданиях успешно сохранены в БД.")
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении данных о зданиях: {e}")

    def save_garrison(self):
        """
        Сохраняет гарнизон в базу данных.
        Обновляет существующие записи или создает новые, если их нет, ориентируясь на city_name и unit_name.
        """
        try:
            # Для каждого города обновляем или добавляем записи гарнизона
            for city_name, units in self.garrison.items():
                for unit in units:
                    unit_name = unit['unit_name']
                    unit_count = unit['unit_count']
                    unit_image = self.get_unit_image(unit_name)
                    print(f"  Обработка юнита: {unit_name}, Количество: {unit_count}, Изображение: {unit_image}")

                    # Проверяем, существует ли уже запись для данного city_name и unit_name
                    self.cursor.execute("""
                        SELECT unit_count
                        FROM garrisons
                        WHERE city_id = ? AND unit_name = ?
                    """, (city_name, unit_name))
                    existing_record = self.cursor.fetchone()

                    if existing_record:
                        # Если запись существует, обновляем количество юнитов
                        new_count = existing_record[0] + unit_count
                        self.cursor.execute("""
                            UPDATE garrisons
                            SET unit_count = ?
                            WHERE city_id = ? AND unit_name = ?
                        """, (new_count, city_name, unit_name))
                    else:
                        # Если записи нет, добавляем новую
                        self.cursor.execute("""
                            INSERT INTO garrisons (city_id, unit_name, unit_count, unit_image)
                            VALUES (?, ?, ?, ?)
                        """, (city_name, unit_name, unit_count, unit_image))

            # Сохраняем изменения в базе данных
            self.db_connection.commit()
            print("Гарнизон успешно сохранен в БД.")
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении гарнизона: {e}")

    def manage_buildings(self):
        try:
            crowns = self.resources['Кроны']

            # Бюджет на строительство (90% от текущих крон)
            building_budget = int(crowns * 0.9)

            # Проверяем, достаточно ли средств для начала строительства
            if building_budget < 500:
                print("Недостаточно средств для строительства.")
                return

            # Вычисляем, сколько зданий каждого типа можно построить
            result_buildings = building_budget // 500  # Количество пакетов по 500 крон
            hospitals_to_build = result_buildings
            factories_to_build = result_buildings

            # Строим все больницы сразу
            if hospitals_to_build > 0:
                self.build_in_city('Больница', hospitals_to_build)

            # Строим все фабрики сразу
            if factories_to_build > 0:
                self.build_in_city('Фабрика', factories_to_build)

            # Сохраняем данные
            self.save_all_data()

        except Exception as e:
            print(f"Ошибка в manage_buildings: {e}")

    def build_in_city(self, building_type, count):
        """
        Строительство зданий в городе.
        """
        cost = 300 if building_type == 'Больница' else 200
        total_cost = cost * count

        # Проверяем, достаточно ли крон для строительства
        if self.resources['Кроны'] < total_cost:
            print("Недостаточно средств для строительства.")
            return False

        # Определяем город для строительства
        preferred_cities = {
            "Аркадия": ["Аргенвилль"],
            "Селестия": ["Миреллия"],
            "Хиперион": ["Ауренбург", "Элдирия"],
            "Халидон": ["Эркан"],
            "Этерия": ["Фэйху"]
        }

        target_city = None
        if not hasattr(self, "turn_count"):
            self.turn_count = 0  # Инициализация счетчика ходов

        if self.turn_count == 0:  # Первый ход
            cities_for_faction = preferred_cities.get(self.faction, [])
            if cities_for_faction:
                # Для Хипериона чередуем города между Ауренбургом и Элдирией
                if self.faction == "Хиперион":
                    city_index = (self.hospitals + self.factories) % len(cities_for_faction)
                    target_city = cities_for_faction[city_index]
                else:
                    target_city = cities_for_faction[0]  # Для остальных фракций берем первый город
        else:
            # На последующих ходах выбираем случайный город
            import random
            target_city = random.choice(list(self.cities.values()))

        # Увеличиваем количество зданий в выбранном городе
        self.buildings.setdefault(target_city, {"Здания": {"Больница": 0, "Фабрика": 0}})
        self.buildings[target_city]["Здания"][building_type] += count

        # Обновляем глобальные переменные
        if building_type == 'Больница':
            self.hospitals += count
        elif building_type == 'Фабрика':
            self.factories += count

        # Списываем кроны
        self.resources['Кроны'] -= total_cost

        print(f"Построено {count} {building_type} в городе {target_city}")

        # Увеличиваем счетчик ходов после первого цикла строительства
        if self.turn_count == 0 and self.hospitals + self.factories >= 5:
            self.turn_count += 1

        return True

    def sell_resources(self):
        """
        Продажа сырья на рынке.
        Продается 70% сырья, если его больше 10000.
        """
        if self.resources['Сырье'] > 10000:
            amount_to_sell = int(((self.resources['Сырье'])/10000) * 0.7)  # Продаем 70% сырья
            earned_crowns = int(amount_to_sell * self.raw_material_price)

            # Обновляем ресурсы
            self.resources['Сырье'] -= amount_to_sell
            self.resources['Кроны'] += earned_crowns

            print(f"Продано {amount_to_sell} сырья за {earned_crowns} крон.")
            return True  # Продажа успешна
        else:
            print("Недостаточно сырья для продажи.")
            return False  # Продажа не удалась

    def hire_army(self):
        """
        Найм армии.
        Добавляет новые юниты в гарнизон через метод save_garrison.
        """
        global resource_allocation

        crowns = self.resources['Кроны']
        works = self.resources['Рабочие']

        # Отладочный вывод: текущие ресурсы
        print(f"Текущие кроны: {crowns}, Текущие рабочие: {works}")

        if crowns <= 0 or works <= 0:
            print("Недостаточно средств для найма армии.")
            return

        # Определение стадии игры
        early_game = self.turn < 17  # ранняя игра
        mid_game = 17 <= self.turn <= 30  # Средняя игра
        late_game = self.turn > 30  # Поздняя игра

        # Распределение ресурсов в зависимости от стадии игры
        if early_game:
            resource_allocation = {
                "attack": 0.8,  # 80% на атаку
                "defense": 0.2  # 20% на защиту
            }
        if mid_game:
            resource_allocation = {
                "attack": 0.4,  # 40% на атаку
                "defense": 0.6  # 60% на защиту
            }
        elif late_game:
            resource_allocation = {
                "attack": 0.20,  # 20% на атаку
                "defense": 0.6,  # 60% на защиту
                "middle": 0.10,  # 10% на универсальных юнитов
                "hard_attack": 0.10  # 10% на супер ударных юнитов
            }

        # Списки для найма юнитов по категориям
        hired_units = {
            "attack": {"unit_name": None, "max_units": 0, "best_efficiency": 0},
            "defense": {"unit_name": None, "max_units": 0, "best_efficiency": 0},
            "middle": {"unit_name": None, "max_units": 0, "best_efficiency": 0},
            "hard_attack": {"unit_name": None, "max_units": 0, "best_efficiency": 0}  # Новая категория
        }

        # Проходим по всем доступным юнитам
        for unit_name, unit_data in self.army.items():
            cost_money = unit_data['cost']['money']
            cost_time = unit_data['cost']['time']
            attack = unit_data['stats']['Атака']
            defense = unit_data['stats']['Защита']
            durability = unit_data['stats']['Прочность']

            # Считаем, сколько юнитов можно нанять
            units_by_money = crowns // cost_money
            units_by_works = works // cost_time
            affordable_units = min(units_by_money, units_by_works)

            if affordable_units <= 0:
                continue  # Пропускаем юниты, которых нельзя нанять

            # Рассчитываем эффективность юнита для разных категорий
            efficiency_attack = attack / (cost_money + cost_time)
            efficiency_defense = (defense + durability) / (cost_money + cost_time)
            efficiency_middle = (attack + defense + durability) / (cost_money + cost_time)

            # Выбираем лучшие юниты для каждой категории
            if efficiency_attack > hired_units["attack"]["best_efficiency"]:
                hired_units["attack"] = {
                    "unit_name": unit_name,
                    "max_units": affordable_units,
                    "best_efficiency": efficiency_attack
                }
            if efficiency_defense > hired_units["defense"]["best_efficiency"]:
                hired_units["defense"] = {
                    "unit_name": unit_name,
                    "max_units": affordable_units,
                    "best_efficiency": efficiency_defense
                }
            if late_game and efficiency_middle > hired_units["middle"]["best_efficiency"]:
                hired_units["middle"] = {
                    "unit_name": unit_name,
                    "max_units": affordable_units,
                    "best_efficiency": efficiency_middle
                }

            # Для поздней игры выбираем юниты с максимальной атакой
            if late_game and attack > hired_units["hard_attack"]["best_efficiency"]:
                hired_units["hard_attack"] = {
                    "unit_name": unit_name,
                    "max_units": affordable_units,
                    "best_efficiency": attack  # Учитываем только атаку
                }

        # Расчет количества юнитов для найма в зависимости от распределения ресурсов
        total_units = {}
        for category, allocation in resource_allocation.items():
            if hired_units[category]["unit_name"]:
                max_units = int(hired_units[category]["max_units"] * allocation)
                if max_units > 0:
                    total_units[category] = {
                        "unit_name": hired_units[category]["unit_name"],
                        "max_units": max_units
                    }

        # Если нет подходящих юнитов
        if not total_units:
            print("Недостаточно средств для найма армии.")
            return

        # Найм юнитов и списание ресурсов
        target_city = max(
            self.buildings.items(),
            key=lambda city: sum(city[1]['Здания'].values())
        )[0]
        print(f"Выбран город для найма: {target_city}.")

        new_garrison_entry = {target_city: []}
        for category, unit_info in total_units.items():
            unit_name = unit_info["unit_name"]
            max_units = unit_info["max_units"]
            unit_data = self.army[unit_name]
            cost_money = unit_data['cost']['money']
            cost_time = unit_data['cost']['time']

            # Списываем ресурсы
            total_cost_money = max_units * cost_money
            total_cost_time = max_units * cost_time
            self.resources['Кроны'] -= total_cost_money
            self.resources['Рабочие'] -= total_cost_time

            # Добавляем юниты в гарнизон
            new_garrison_entry[target_city].append({"unit_name": unit_name, "unit_count": max_units})
            print(
                f"Нанято {max_units} юнитов '{unit_name}' за {total_cost_money} крон и {total_cost_time} рабочих в городе {target_city}."
            )

        # Обновляем гарнизон
        self.garrison.update(new_garrison_entry)
        self.save_garrison()
        print("Гарнизон после найма армии:", self.garrison)

    def calculate_and_deduct_consumption(self):
        """
        Метод для расчета потребления сырья гарнизонами текущей фракции
        и вычета суммарного потребления из self.raw_material.
        """
        try:
            # Шаг 1: Выгрузка всех гарнизонов из таблицы garrisons
            self.cursor.execute("""
                SELECT city_id, unit_name, unit_count 
                FROM garrisons
            """)
            garrisons = self.cursor.fetchall()

            # Шаг 2: Для каждого гарнизона находим соответствующий юнит в таблице units
            for garrison in garrisons:
                city_id, unit_name, unit_count = garrison

                # Проверяем, к какой фракции принадлежит юнит
                self.cursor.execute("""
                    SELECT consumption, faction 
                    FROM units 
                    WHERE unit_name = ?
                """, (unit_name,))
                unit_data = self.cursor.fetchone()

                if unit_data:
                    consumption, faction = unit_data

                    # Учитываем только юниты текущей фракции
                    if faction == self.faction:
                        # Расчет потребления для данного типа юнита
                        self.total_consumption = consumption * unit_count

            # Шаг 3: Вычитание общего потребления из денег фракции
            self.raw_material -= self.total_consumption
            print(f"Общее потребление сырья: {self.total_consumption}")
            print(f"Остаток сырья у фракции: {self.raw_material}")

        except Exception as e:
            print(f"Произошла ошибка: {e}")

    def calculate_tax_income(self):
        """
        Рассчитывает налоговый доход на основе населения.
        """
        tax_rate = 0.34  # Базовая налоговая ставка (34%)
        return int(self.resources['Население'] * tax_rate)

    def update_buildings_from_db(self):
        """
        Загружает данные о количестве больниц и фабрик из базы данных.
        """
        try:
            query = """
                SELECT building_type, SUM(count)
                FROM buildings
                WHERE faction = ?
                GROUP BY building_type
            """
            self.cursor.execute(query, (self.faction,))
            rows = self.cursor.fetchall()

            # Обновляем количество зданий
            self.hospitals = next((count for b_type, count in rows if b_type == "Больница"), 0)
            self.factories = next((count for b_type, count in rows if b_type == "Фабрика"), 0)

            print(f"Загружены здания: Больницы={self.hospitals}, Фабрики={self.factories}")
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных о зданиях: {e}")

    def generate_raw_material_price(self):
        """
        Генерирует новую цену на сырье.
        """
        # Простая реализация: случайная цена в диапазоне от 2.0 до 3.0
        self.raw_material_price = round(random.uniform(1200, 41250), 2200)
        print(f"Новая цена на сырье: {self.raw_material_price}")

    def update_trade_resources_from_db(self):
        """
        Обновляет ресурсы на основе торговых соглашений из базы данных.
        Учитывает текущую фракцию как инициатора или целевую фракцию.
        """
        try:
            # Убедитесь, что self.faction — это строка (или одиночное значение)
            if isinstance(self.faction, (list, tuple)):
                raise ValueError("self.faction должен быть строкой, а не коллекцией.")

            # Запрос для получения всех торговых соглашений, где текущая фракция участвует
            query = """
                SELECT initiator, target_faction, initiator_type_resource, target_type_resource,
                       initiator_summ_resource, target_summ_resource
                FROM trade_agreements
                WHERE target_faction = ?
            """
            # Передаем self.faction как одиночное значение
            self.cursor.execute(query, (self.faction,))
            rows = self.cursor.fetchall()

            for row in rows:
                initiator, target_faction, initiator_type_resource, target_type_resource, \
                    initiator_summ_resource, target_summ_resource = row

                # Если текущая фракция является инициатором сделки
                if initiator == self.faction:
                    # Отнимаем ресурс, который отдает инициатор
                    if initiator_type_resource in self.resources:
                        self.resources[initiator_type_resource] -= initiator_summ_resource

                    # Добавляем ресурс, который получает инициатор
                    if target_type_resource in self.resources:
                        self.resources[target_type_resource] += target_summ_resource

                # Если текущая фракция является целевой фракцией
                elif target_faction == self.faction:
                    # Отнимаем ресурс, который отдает целевая фракция
                    if target_type_resource in self.resources:
                        self.resources[target_type_resource] -= target_summ_resource

                    # Добавляем ресурс, который получает целевая фракция
                    if initiator_type_resource in self.resources:
                        self.resources[initiator_type_resource] += initiator_summ_resource

            print(f"Ресурсы из торговых соглашений обновлены: {self.resources}")
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении ресурсов из торговых соглашений: {e}")
        except ValueError as ve:
            print(f"Ошибка в данных: {ve}")

    def load_resources_from_db(self):
        """
        Загружает текущие значения ресурсов из базы данных.
        Обновляет глобальные переменные self.money, self.free_peoples,
        self.raw_material, self.population и словарь self.resources.
        """
        try:
            query = "SELECT resource_type, amount FROM resources WHERE faction = ?"
            self.cursor.execute(query, (self.faction,))
            rows = self.cursor.fetchall()

            # Обновление ресурсов на основе данных из базы данных
            for row in rows:
                resource_type, amount = row
                if resource_type == "Кроны":
                    self.money = amount
                elif resource_type == "Рабочие":
                    self.free_peoples = amount
                elif resource_type == "Сырье":
                    self.raw_material = amount
                elif resource_type == "Население":
                    self.population = amount

            # Обновление словаря self.resources
            self.resources = {
                'Кроны': self.money,
                'Рабочие': self.free_peoples,
                'Сырье': self.raw_material,
                'Население': self.population
            }

            print(f"Ресурсы успешно загружены из БД: {self.resources}")
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке ресурсов из БД: {e}")

    def update_resources(self):
        """
        Обновление текущих ресурсов с учетом данных из базы данных.
        Все расчеты выполняются на основе таблиц в базе данных.
        """
        try:
            self.update_buildings_from_db()

            # Генерируем новую цену на сырье
            self.generate_raw_material_price()

            # Обновляем ресурсы на основе торговых соглашений из таблицы trade_agreements
            self.update_trade_resources_from_db()

            self.process_trade_agreements()

            # Коэффициенты для каждой фракции
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

            # Получение коэффициентов для текущей фракции
            faction = self.faction
            if faction not in faction_coefficients:
                raise ValueError(f"Фракция '{faction}' не найдена.")
            coeffs = faction_coefficients[faction]

            # Обновление ресурсов с учетом коэффициентов
            self.born_peoples = int(self.hospitals * 500)
            self.work_peoples = int(self.factories * 200)
            self.clear_up_peoples = self.born_peoples - self.work_peoples + self.tax_effects

            # Загружаем текущие значения ресурсов из базы данных
            self.load_resources_from_db()

            # Выполняем расчеты
            self.free_peoples += self.clear_up_peoples
            self.money += int(self.calculate_tax_income() - (self.hospitals * coeffs['money_loss']))
            self.money_info = int(self.hospitals * coeffs['money_loss'])
            self.money_up = int(self.calculate_tax_income() - (self.hospitals * coeffs['money_loss']))
            self.taxes_info = int(self.calculate_tax_income())

            # Учитываем, что одна фабрика может прокормить 1000 людей
            self.raw_material += int((self.factories * 1000) - (self.population * coeffs['food_loss']))
            self.food_info = (int((self.factories * 1000) - (self.population * coeffs['food_loss'])) - self.total_consumption)
            self.food_peoples = int(self.population * coeffs['food_loss'])

            # Проверяем, будет ли население увеличиваться
            if self.raw_material > 0:
                self.population += int(self.clear_up_peoples)  # Увеличиваем население только если есть Сырье
            else:
                # Логика убыли населения при недостатке Сырья
                if self.population > 100:
                    loss = int(self.population * 0.45)  # 45% от населения
                    self.population -= loss
                else:
                    loss = min(self.population, 50)  # Обнуление по 50, но не ниже 0
                    self.population -= loss
                self.free_peoples = 0  # Все рабочие обнуляются, так как Сырья нет

            # Проверка, чтобы ресурсы не опускались ниже 0
            self.resources.update({
                "Кроны": max(int(self.money), 0),
                "Рабочие": max(int(self.free_peoples), 0),
                "Сырье": max(int(self.raw_material), 0),
                "Население": max(int(self.population), 0)
            })

            # Потребление армии
            self.calculate_and_deduct_consumption()

            # Сохраняем обновленные ресурсы в базу данных
            self.save_resources_to_db()

            print(f"Ресурсы обновлены: {self.resources}, Больницы: {self.hospitals}, Фабрики: {self.factories}")

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении ресурсов: {e}")

    def save_all_data(self):
        try:
            self.save_resources_to_db()
            self.save_buildings()
            self.save_garrison()
            print("Все данные успешно сохранены в БД")
        except Exception as e:
            print(f"Ошибка при сохранении данных: {e}")

    def get_unit_image(self, unit_name):
        """
        Получает путь к изображению юнита из базы данных.

        Args:
            unit_name (str): Название юнита

        Returns:
            str: Путь к изображению юнита или пустая строка, если не найдено
        """
        try:
            query = """
                SELECT image_path 
                FROM units 
                WHERE faction = ? AND unit_name = ?
            """
            self.cursor.execute(query, (self.faction, unit_name))
            result = self.cursor.fetchone()
            if result:
                return result[0]  # Возвращаем путь к изображению
            else:
                print(f"Предупреждение: Изображение для юнита '{unit_name}' не найдено")
                return ""
        except Exception as e:
            print(f"Ошибка при получении изображения юнита '{unit_name}': {e}")
            return ""

    def process_trade_agreements(self):
        """
        Обрабатывает торговые соглашения для текущей фракции.
        Если текущая фракция является target_faction, анализирует сделку и принимает решение.
        """
        try:
            # Загружаем текущие отношения с другими фракциями
            self.relations = self.load_relations()

            # Запрос для получения всех торговых соглашений, где текущая фракция является целевой
            query = """
                SELECT id, initiator, target_faction, initiator_type_resource, target_type_resource,
                       initiator_summ_resource, target_summ_resource
                FROM trade_agreements
                WHERE target_faction = ?
            """
            self.cursor.execute(query, (self.faction,))
            rows = self.cursor.fetchall()

            for row in rows:
                trade_id, initiator, target_faction, initiator_type_resource, target_type_resource, \
                    initiator_summ_resource, target_summ_resource = row

                # Проверяем уровень отношений с инициатором сделки
                relation_level = int(self.relations.get(initiator, 0))

                # Определяем коэффициент на основе уровня отношений
                if relation_level < 15:
                    print(f"Отказ от сделки с {initiator}. Низкий уровень отношений ({relation_level}).")
                    self.update_agreement_status(trade_id, False)  # Проставляем agree = false
                    continue

                # Проверяем наличие ресурсов у целевой фракции
                has_enough_resources = self.resources.get(target_type_resource, 0) >= target_summ_resource

                if not has_enough_resources:
                    print(f"Отказ от сделки с {initiator}. Недостаточно ресурсов для выполнения сделки.")
                    self.update_agreement_status(trade_id, False)  # Проставляем agree = false
                    continue

                # Рассчитываем соотношение обмена ресурсов
                resource_ratio = target_summ_resource / initiator_summ_resource

                # Определяем коэффициент выгодности сделки на основе отношений
                if relation_level < 25:
                    coefficient = 0.09
                elif 25 <= relation_level < 35:
                    coefficient = 0.2
                elif 35 <= relation_level < 50:
                    coefficient = 0.8
                elif 50 <= relation_level < 60:
                    coefficient = 1.0
                elif 60 <= relation_level < 75:
                    coefficient = 1.4
                elif 75 <= relation_level < 90:
                    coefficient = 2.0
                elif 90 <= relation_level <= 100:
                    coefficient = 3.1
                else:
                    coefficient = 0.0

                # Проверяем, выгодна ли сделка
                if resource_ratio > coefficient:
                    print(
                        f"Отказ от сделки с {initiator}. Не выгодное соотношение ({resource_ratio:.2f} < {coefficient:.2f})."
                    )
                    self.update_agreement_status(trade_id, False)  # Проставляем agree = false
                    continue

                # Если сделка выгодна, выполняем обмен ресурсами
                print(
                    f"Принята сделка с {initiator}. Соотношение: {resource_ratio:.2f}, Коэффициент: {coefficient:.2f}."
                )
                self.execute_trade(initiator, target_faction, initiator_type_resource, target_type_resource,
                                   initiator_summ_resource, target_summ_resource)
                self.update_agreement_status(trade_id, True)  # Проставляем agree = true

        except sqlite3.Error as e:
            print(f"Ошибка при обработке торговых соглашений: {e}")

    def update_agreement_status(self, trade_id, status):
        """
        Обновляет значение agree в таблице trade_agreements.
        :param trade_id: ID торгового соглашения
        :param status: True или False
        """
        try:
            query = """
                UPDATE trade_agreements
                SET agree = ?
                WHERE id = ?
            """
            self.cursor.execute(query, (status, trade_id))
            self.db_connection.commit()
            print(f"Статус сделки ID={trade_id} обновлен: agree={status}")
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении статуса сделки: {e}")

    def return_resource_to_player(self, initiator, resource_type, amount):
        """
        Возвращает ресурсы инициатору сделки в случае отказа.
        """
        try:
            self.cursor.execute("""
                UPDATE resources
                SET amount = amount + ?
                WHERE faction = ? AND resource_type = ?
            """, (amount, initiator, resource_type))
            self.db_connection.commit()
            print(f"Возвращено {amount} {resource_type} фракции {initiator}.")
        except sqlite3.Error as e:
            print(f"Ошибка при возврате ресурсов: {e}")

    def remove_trade_agreement(self, trade_id):
        """
        Удаляет торговое соглашение из базы данных.
        """
        try:
            self.cursor.execute("""
                DELETE FROM trade_agreements
                WHERE id = ?
            """, (trade_id,))
            self.db_connection.commit()
            print(f"Торговое соглашение ID={trade_id} удалено.")
        except sqlite3.Error as e:
            print(f"Ошибка при удалении торгового соглашения: {e}")

    def execute_trade(self, initiator, target_faction, initiator_type_resource, target_type_resource,
                      initiator_summ_resource, target_summ_resource):
        """
        Выполняет обмен ресурсами между фракциями.
        """
        try:
            # Отнимаем ресурсы у инициатора
            self.cursor.execute("""
                UPDATE resources
                SET amount = amount - ?
                WHERE faction = ? AND resource_type = ?
            """, (initiator_summ_resource, initiator, initiator_type_resource))

            # Добавляем ресурсы целевой фракции
            self.cursor.execute("""
                UPDATE resources
                SET amount = amount + ?
                WHERE faction = ? AND resource_type = ?
            """, (target_summ_resource, target_faction, target_type_resource))

            # Добавляем ресурсы целевой фракции инициатору
            self.cursor.execute("""
                UPDATE resources
                SET amount = amount + ?
                WHERE faction = ? AND resource_type = ?
            """, (initiator_summ_resource, target_faction, initiator_type_resource))

            # Отнимаем ресурсы у целевой фракции
            self.cursor.execute("""
                UPDATE resources
                SET amount = amount - ?
                WHERE faction = ? AND resource_type = ?
            """, (target_summ_resource, initiator, target_type_resource))

            self.db_connection.commit()
            print(f"Обмен ресурсами выполнен: {initiator} <-> {target_faction}.")
        except sqlite3.Error as e:
            print(f"Ошибка при выполнении обмена ресурсами: {e}")

    def load_political_system(self):
        """
        Загружает текущую политическую систему фракции из базы данных.
        """
        try:
            query = "SELECT system FROM political_systems WHERE faction = ?"
            self.cursor.execute(query, (self.faction,))
            result = self.cursor.fetchone()
            return result[0] if result else "Капитализм"  # По умолчанию "Капитализм"
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политической системы: {e}")
            return "Капитализм"



    # Основная логика хода ИИ
    def make_turn(self):
        """
        Основная логика хода ИИ фракции.
        """
        print(f'---------ХОДИТ ФРАКЦИЯ: {self.faction}-------------------')
        try:
            # 1. Обновляем ресурсы из базы данных
            self.update_resources()

            # 3. Применяем бонусы от политической системы
            self.apply_political_system_bonus()

            # 4. Изменяем отношения на основе политической системы
            self.update_relations_based_on_political_system()

            # 5. Загружаем данные о зданиях
            self.update_buildings_from_db()

            # 6. Управление строительством (90% крон на строительство)
            self.manage_buildings()

            # 7. Продажа сырья (70% сырья, если его больше 10000)
            resources_sold = self.sell_resources()

            # 8. Найм армии (на оставшиеся деньги после строительства и продажи сырья)
            if resources_sold:
                self.hire_army()

            # 9. Сохраняем все изменения в базу данных
            self.save_all_data()

            # Увеличиваем счетчик ходов
            self.turn += 1
            print(f'-----------КОНЕЦ {self.turn} ХОДА----------------  ФРАКЦИИ', self.faction)
        except Exception as e:
            print(f"Ошибка при выполнении хода: {e}")

    def apply_political_system_bonus(self):
        """
        Применяет бонусы от политической системы.
        """
        system = self.load_political_system()
        if system == "Капитализм":
            crowns_bonus = int(self.money_up * 0.15)
            self.resources['Кроны'] = int(self.resources.get('Кроны', 0)) + crowns_bonus
            print(f"Бонус от капитализма: +{crowns_bonus} Крон")
        elif system == "Коммунизм":
            raw_material_bonus = int(self.food_info * 0.15)
            self.resources['Сырье'] = int(self.resources.get('Сырье', 0)) + raw_material_bonus
            print(f"Бонус от коммунизма: +{raw_material_bonus} Сырья")

    def update_relations_based_on_political_system(self):
        """
        Изменяет отношения на основе политической системы каждые 4 хода.
        """
        if self.turn % 4 != 0:
            return

        current_system = self.load_political_system()
        all_factions = self.load_relations()

        for faction, relation_level in all_factions.items():
            other_system = self.load_political_system_for_faction(faction)

            # Преобразуем relation_level в число
            relation_level = int(relation_level)

            if current_system == other_system:
                new_relation = min(relation_level + 2, 100)
            else:
                new_relation = max(relation_level - 2, 0)

            self.update_relation_in_db(faction, new_relation)

    def load_political_system_for_faction(self, faction):
        """
        Загружает политическую систему указанной фракции.
        """
        try:
            query = "SELECT system FROM political_systems WHERE faction = ?"
            self.cursor.execute(query, (faction,))
            result = self.cursor.fetchone()
            return result[0] if result else "Капитализм"  # По умолчанию "Капитализм"
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политической системы для фракции {faction}: {e}")
            return "Капитализм"

    def update_relation_in_db(self, faction, new_relation):
        """
        Обновляет уровень отношений в базе данных.
        """
        try:
            query = """
                UPDATE relations
                SET relationship = ?
                WHERE faction1 = ? AND faction2 = ?
            """
            self.cursor.execute(query, (new_relation, self.faction, faction))
            self.db_connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении отношений для фракции {faction}: {e}")