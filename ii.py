import sqlite3
import random


class AIController:
    def __init__(self, faction, db_path='game_data.db'):
        self.faction = faction
        self.db_connection = sqlite3.connect(db_path)
        self.cursor = self.db_connection.cursor()
        self.resources = {"Кроны": 0, "Сырье": 0, "Рабочие": 0, "Население": 0}
        self.garrison = self.load_garrison()
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
            SELECT unit_name, cost_money, attack, defense, durability, unit_class 
            FROM units 
            WHERE faction = ?
        """
        self.cursor.execute(query, (self.faction,))
        return {
            row[0]: {
                "cost": row[1],
                "stats": {
                    "Атака": row[2],
                    "Защита": row[3],
                    "Прочность": row[4],
                    "Класс": row[5]
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
                print(f"Обработка гарнизона для города {city_name}: {units}")
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
                        print(
                            f"  Обновление записи: city_id={city_name}, unit_name={unit_name}, новое количество={new_count}")
                        self.cursor.execute("""
                            UPDATE garrisons
                            SET unit_count = ?
                            WHERE city_id = ? AND unit_name = ?
                        """, (new_count, city_name, unit_name))
                    else:
                        # Если записи нет, добавляем новую
                        print(
                            f"  Добавление новой записи: city_id={city_name}, unit_name={unit_name}, unit_count={unit_count}")
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
            building_budget = int(crowns * 0.9)

            # Проверяем, достаточно ли бюджета
            if building_budget < 500:
                print("Недостаточно средств для строительства.")
                return

            # Строим здания пакетами
            while building_budget >= 1200:
                if not self.build_in_city('Больница', 2):
                    break
                building_budget -= 600

                if not self.build_in_city('Фабрика', 3):
                    break
                building_budget -= 600

            # Строим оставшиеся здания
            while building_budget >= 200:
                if building_budget >= 300:
                    if not self.build_in_city('Больница', 1):
                        break
                    building_budget -= 300
                elif building_budget >= 200:
                    if not self.build_in_city('Фабрика', 1):
                        break
                    building_budget -= 200

            # Сохраняем данные
            self.save_all_data()

        except Exception as e:
            print(f"Ошибка в manage_buildings: {e}")

    def build_in_city(self, building_type, count):
        """
        Строительство зданий в городе.
        Первый ход: строит 2 больницы и 3 фабрики в предопределенных городах.
        Последующие ходы: строит здания в случайных городах.
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
        crowns = self.resources['Кроны']

        # Отладочный вывод: текущие кроны
        print(f"Текущие кроны: {crowns}")

        if crowns <= 0:
            print("Недостаточно средств для найма армии.")
            return

        best_unit = None
        max_units = 0

        # Находим лучший юнит для найма
        for unit_name, unit_data in self.army.items():
            unit_cost = unit_data['cost']
            possible_units = crowns // unit_cost
            if possible_units > max_units:
                max_units = possible_units
                best_unit = (unit_name, unit_data)

        if not best_unit:
            print("Недостаточно средств для найма армии.")
            return

        unit_name, unit_data = best_unit
        total_cost = max_units * unit_data['cost']

        # Списываем ресурсы
        self.resources['Кроны'] -= total_cost

        # Находим город с наибольшим количеством зданий
        target_city = max(self.buildings.items(), key=lambda city: sum(city[1]['Здания'].values()))[0]
        print(f"Выбран город для найма: {target_city}.")

        # Добавляем юниты в гарнизон через метод save_garrison
        new_garrison_entry = {
            target_city: [{"unit_name": unit_name, "unit_count": max_units}]
        }
        self.garrison.update(new_garrison_entry)
        print("Гарнизон после найма армии:", self.garrison)

        self.save_garrison()
        print(f"Нанято {max_units} юнитов '{unit_name}' за {total_cost} крон в городе {target_city}.")

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
            # Запрос для получения всех торговых соглашений, где текущая фракция участвует
            query = """
                SELECT initiator, target_faction, initiator_type_resource, target_type_resource,
                       initiator_summ_resource, target_summ_resource
                FROM trade_agreements
                WHERE initiator = ? OR target_faction = ?
            """
            self.cursor.execute(query, (self.faction, self.faction))
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
            self.food_info = int((self.factories * 1000) - (self.population * coeffs['food_loss']))
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

    # Основная логика хода ИИ
    def make_turn(self):
        """
        Основная логика хода ИИ фракции.
        """
        try:
            # 1. Обновляем ресурсы из базы данных
            self.update_resources()

            # 2. Загружаем данные о зданиях
            self.update_buildings_from_db()

            # 3. Управление строительством (90% крон на строительство)
            self.manage_buildings()

            # 4. Продажа сырья (70% сырья, если его больше 10000)
            resources_sold = self.sell_resources()

            # 5. Найм армии (на оставшиеся деньги после строительства и продажи сырья)
            if resources_sold:
                self.hire_army()

            # 6. Сохраняем все изменения в базу данных
            self.save_all_data()

        except Exception as e:
            print(f"Ошибка при выполнении хода: {e}")