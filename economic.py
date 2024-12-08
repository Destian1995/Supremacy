from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.graphics import Color, RoundedRectangle, Line

from kivy.uix.image import Image
import os
import json
import random
import matplotlib.pyplot as plt
import io


# Список доступных зданий с иконками
BUILDINGS = {
    'Больница': 'files/buildings/medic.jpg',
    'Фабрика': 'files/buildings/fabric.jpg',
}

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

def get_faction_of_city(city_name):
    try:
        with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
            diplomacies = json.load(file)
        for faction, data in diplomacies.items():
            if city_name in data.get("города", []):
                return faction
        print(f"Город '{city_name}' не принадлежит ни одной фракции.")
        return None
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при загрузке diplomacies.json: {e}")
        return None


def save_building_change(faction_name, city, building_type, delta):
    """
    Обновляет количество зданий для указанного города в JSON-файле.
    delta — изменение (например, +1 или -1).
    """
    fraction_path = transform_filename(f'files/config/buildings_in_city/{faction_name}_buildings_city.json')

    try:
        # Чтение существующих данных
        with open(fraction_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    # Убедимся, что структура корректна
    if city not in data:
        data[city] = {'Здания': {}}
    if building_type not in data[city]['Здания']:
        data[city]['Здания'][building_type] = 0

    # Обновляем количество зданий
    data[city]['Здания'][building_type] += delta
    if data[city]['Здания'][building_type] < 0:
        data[city]['Здания'][building_type] = 0  # Предотвращаем отрицательные значения

    # Сохраняем изменения
    with open(fraction_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)




class Faction:
    def __init__(self, name):
        self.faction = name
        self.cities = self.load_cities_from_file()
        self.money = 100000
        self.free_peoples = 10000
        self.food = 20000
        self.population = 30
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
        self.clear_up_peoples = 0
        self.food_price_history = []  # История цен на еду
        self.current_food_price = 0  # Текущая цена на еду
        self.current_tax_rate = 0  # Начальная ставка налога — по умолчанию 0%
        self.turns = 0  # Счетчик ходов
        self.tax_set = False  # Флаг, установлен ли налог
        self.custom_tax_rate = 0  # Новый атрибут для хранения пользовательской ставки налога
        self.cities_buildings = {city['name']: {'Больница': 0, 'Фабрика': 0} for city in self.cities}

        self.resources = {
            'Кроны': self.money,
            'Рабочие': self.free_peoples,
            'Еда': self.food,
            'Население': self.population
        }
        self.economic_params = {
            "Аркадия": {"tax_rate": 0.03},
            "Селестия": {"tax_rate": 0.015},
            "Хиперион": {"tax_rate": 0.02},
            "Этерия": {"tax_rate": 0.012},
            "Халидон": {"tax_rate": 0.01},
        }

        self.is_first_run = True  # Флаг для первого запуска
        self.initialize_food_prices()  # Генерация начальной цены на еду

    def load_cities_from_file(self):
        try:
            with open('files/config/city.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            # Проверка на существование фракции в данных
            if self.faction in data['kingdoms']:
                return data['kingdoms'][self.faction]['fortresses']
            else:
                print(f"Фракция {self.faction} не найдена в файле city.json.")
                return []
        except FileNotFoundError:
            print("Файл city.json не найден.")
            return []
        except json.JSONDecodeError:
            print("Ошибка при чтении файла city.json.")
            return []

    def build_factory(self, city):
        """Увеличить количество фабрик в указанном городе."""
        self.cities_buildings[city]['Фабрика'] += 1  # Обновляем локальные данные
        save_building_change(self.faction, city, "Фабрика", 1)  # Передаем изменение
        self.update_buildings()  # Пересчитываем общие показатели


    def build_hospital(self, city):
        """Увеличить количество больниц в указанном городе."""
        self.cities_buildings[city]['Больница'] += 1
        save_building_change(self.faction, city, "Больница", 1)
        self.update_buildings()


    def update_buildings(self):
        """
        Обновляет количество зданий для каждого города фракции по данным из JSON-файла.
        """
        buildings_file = transform_filename(f'files/config/buildings_in_city/{self.faction}_buildings_city.json')

        # Проверяем существование файла
        if os.path.exists(buildings_file):
            try:
                # Чтение данных из файла
                with open(buildings_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                # Обновляем данные зданий для каждого города
                for city, buildings in data.items():
                    if city not in self.cities_buildings:
                        self.cities_buildings[city] = {'Больница': 0, 'Фабрика': 0}

                    # Обновляем данные из файла
                    self.cities_buildings[city]['Больница'] = buildings.get('Здания', {}).get('Больница', 0)
                    self.cities_buildings[city]['Фабрика'] = buildings.get('Здания', {}).get('Фабрика', 0)

                # Пересчитываем общие показатели
                self.hospitals = sum(city['Больница'] for city in self.cities_buildings.values())
                self.factories = sum(city['Фабрика'] for city in self.cities_buildings.values())

            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Ошибка при чтении файла {buildings_file}: {e}")
        else:
            print(f"Файл {buildings_file} не найден!")


    def cash_build(self, money):
        """Списывает деньги, если их хватает, и возвращает True, иначе False."""
        if self.money >= money:
            self.money -= money
            self.save_resources()
            return True
        else:
            return False

    def get_income_per_person(self):
        """Получение дохода с одного человека для данной фракции."""
        if self.tax_set and self.custom_tax_rate is not None:
            return self.custom_tax_rate
        params = self.economic_params[self.faction]
        return params["tax_rate"]

    def calculate_tax_income(self):
        """Расчет дохода от налогов с учетом установленной ставки."""
        if not self.tax_set:
            print("Налог не установлен. Прироста от налогов нет.")
            self.taxes = 0
        else:
            # Используем пользовательскую ставку налога или базовую, если пользовательская не задана
            tax_rate = self.custom_tax_rate if self.custom_tax_rate is not None else self.get_base_tax_rate()
            self.taxes = self.population * tax_rate  # Применяем базовую налоговую ставку
        return self.taxes

    def set_taxes(self, new_tax_rate):
        """Установка нового уровня налогов и обновление ресурсов."""
        self.custom_tax_rate = self.get_base_tax_rate() * new_tax_rate  # Применяем процент к базовой ставке
        self.tax_set = True
        self.calculate_tax_income()

    def tax_effect(self, tax_rate):
        if 50 > tax_rate > 35:
            return -250
        elif 75 > tax_rate >= 50:
            return -8000
        elif 90 > tax_rate >= 75:
            return -22500
        elif tax_rate >= 90:
            return -70000
        elif 15 > tax_rate:
            return 450
        elif 20 > tax_rate:
            return 90
        else:
            return 0

    def apply_tax_effect(self, tax_rate):
        # Рассчитать и применить эффект налогов на население
        effect = self.tax_effect(tax_rate)
        self.tax_effects = effect
        return self.tax_effects

    def calculate_base_tax_rate(self, tax_rate):
        """Формула расчёта базовой налоговой ставки для текущей фракции."""
        params = self.economic_params[self.faction]
        base_tax_rate = params["tax_rate"]  # Базовая ставка налога для текущей фракции

        # Формируем корректировочный коэффициент на основе введённой ставки
        multiplier = tax_rate
        # Возвращаем корректированную налоговую ставку
        return base_tax_rate * multiplier

    def get_base_tax_rate(self):
        """Получение базовой налоговой ставки для текущей фракции."""
        return self.economic_params[self.faction]["tax_rate"]

    def show_popup(self, title, message):
        """Отображает всплывающее окно с сообщением."""
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()

    def save_resources(self):
        """Записывает текущее состояние ресурсов в файл."""
        resources_data = {
            'Кроны': self.money,
            'Рабочие': self.free_peoples,
            'Еда': self.food,
            'Население': self.population
        }

        try:
            with open('files/config/resources/cash.json', 'w') as file:
                json.dump(resources_data, file, ensure_ascii=False, indent=4)  # Запись с индентацией для удобства
        except Exception as e:
            print(f"Ошибка при сохранении ресурсов: {e}")

    def load_resources(self):
        """Загружает состояние ресурсов из файла и обновляет параметры."""
        if os.path.exists('files/config/resources/cash.json'):
            try:
                with open('files/config/resources/cash.json', 'r') as file:
                    resources_data = json.load(file)
                    # Обновляем атрибуты из загруженных данных
                    self.money = resources_data.get('Кроны', 0)
                    self.free_peoples = resources_data.get('Рабочие', 0)
                    self.food = resources_data.get('Еда', 0)
                    self.population = resources_data.get('Население', 0)
            except json.JSONDecodeError:
                print("Ошибка при загрузке ресурсов: файл пуст или повреждён.")
        else:
            print("Файл ресурсов не найден.")

    def update_cash(self):
        self.load_resources()
        self.resources['Кроны'] = self.money
        self.resources['Рабочие'] = self.free_peoples
        self.resources['Еда'] = self.food
        self.save_resources()
        return self.resources

    def buildings_info_fration(self):
        if self.faction == 'Аркадия':
            return 100
        if self.faction == 'Селестия':
            return 200
        if self.faction == 'Хиперион':
            return 200
        if self.faction == 'Этерия':
            return 300
        if self.faction == 'Халидон':
            return 300

    def update_resources(self):
        """Обновление текущих ресурсов, с проверкой на минимальное значение 0 и округлением до целых чисел."""
        self.update_buildings()

        # Генерация новой цены на еду
        self.generate_food_price()

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
        self.free_peoples += self.clear_up_peoples
        self.money += int(self.calculate_tax_income() - (self.hospitals * coeffs['money_loss']))
        self.money_info = int(self.hospitals * coeffs['money_loss'])
        self.money_up = int(self.calculate_tax_income() - (self.hospitals * coeffs['money_loss']))
        self.taxes_info = int(self.calculate_tax_income())

        # Учитываем, что одна фабрика может прокормить 1000 людей
        self.food += int((self.factories * 1000) - (self.population * coeffs['food_loss']))
        self.food_info = int((self.factories * 1000) - (self.population * coeffs['food_loss']))
        self.food_peoples = int(self.population * coeffs['food_loss'])

        # Проверяем, будет ли население увеличиваться
        if self.food > 0:
            self.population += int(self.clear_up_peoples)  # Увеличиваем население только если есть еда
        else:
            # Логика убыли населения при недостатке еды
            if self.population > 100:
                loss = int(self.population * 0.45)  # 45% от населения
                self.population -= loss
            else:
                loss = min(self.population, 50)  # Обнуление по 50, но не ниже 0
                self.population -= loss
            self.free_peoples = 0  # Все рабочие обнуляются, так как еды нет

        # Проверка, чтобы ресурсы не опускались ниже 0
        self.resources.update({
            "Кроны": max(int(self.money), 0),
            "Рабочие": max(int(self.free_peoples), 0),
            "Еда": max(int(self.food), 0),
            "Население": max(int(self.population), 0)
        })
        self.save_resources()
        print(f"Ресурсы обновлены: {self.resources}, Больницы: {self.hospitals}, Фабрики: {self.factories}")

    def get_resources(self):
        """Получение текущих ресурсов"""
        return self.resources

    def end_game(self):
        if self.population == 0:
            return False

    def initialize_food_prices(self):
        """Инициализация истории цен на еду"""
        for _ in range(25):  # Генерируем 15 случайных цен
            self.generate_food_price()

    def generate_food_price(self):
        """Генерация случайной цены на еду"""
        if self.turns == 0:  # Если это первый ход
            self.current_food_price = random.randint(3000, 47000)
            self.food_price_history.append(self.current_food_price)
        else:
            # Генерация новой цены на основе текущей
            self.current_food_price = self.food_price_history[-1] + random.randint(-2000, 2000)
            self.current_food_price = max(3000, min(47000, self.current_food_price))  # Ограничиваем диапазон
            self.food_price_history.append(self.current_food_price)

        # Ограничение длины истории цен до 25 элементов
        if len(self.food_price_history) > 25:
            self.food_price_history.pop(0)

        self.turns += 1

    def trade_food(self, action):
        """Торговля едой"""
        if action == 'buy':  # Покупка еды
            if self.money >= self.current_food_price:
                self.money -= self.current_food_price
                self.food += 10000
                self.save_resources()
                return True  # Операция успешна
            else:
                show_message("Недостаточно денег", "У вас недостаточно денег для покупки 10000 единиц еды.")
        elif action == 'sell':  # Продажа еды
            if self.food >= 10000:
                self.money += self.current_food_price
                self.food -= 10000
                self.save_resources()
                return True  # Операция успешна
            else:
                show_message("Недостаточно еды", "У вас недостаточно еды для продажи 10000 единиц.")
        return False  # Операция не удалась

    def plot_food_price(self):
        """Генерация графика цен на еду с темным фоном и зеленым графиком"""
        plt.figure(figsize=(10, 5))

        # Устанавливаем темный фон
        plt.style.use('dark_background')

        # Генерируем график с зеленым цветом
        plt.plot(self.food_price_history, marker='o', color='green', label='Историческая цена')

        # Отмечаем текущую цену на графике
        plt.axhline(y=self.current_food_price, color='red', linestyle='--', label='Текущая цена')

        plt.title('История цен на еду за 10000 единиц (бушель)', color='white')  # Заголовок белого цвета
        plt.xlabel('Ходы', color='white')  # Подпись оси X белого цвета
        plt.ylabel('Цена за бушель (кроны)', color='white')  # Подпись оси Y белого цвета
        plt.grid(color='gray')  # Цвет сетки серый для контраста
        plt.legend()  # Показываем легенду графика

        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='black')  # Задаем черный фон для сохраненного изображения
        plt.close()
        buf.seek(0)
        return buf.getvalue()


def show_message(title, message):
    layout = BoxLayout(orientation='vertical', padding=10)
    label = Label(text=message, size_hint=(1, 0.8))
    close_btn = Button(text="Закрыть", size_hint=(1, 0.2))

    layout.add_widget(label)
    layout.add_widget(close_btn)

    popup = Popup(title=title, content=layout, size_hint=(0.6, 0.4))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()


# Логика для отображения сообщения об ошибке средств
def show_error_message(message):
    error_popup = Popup(title="Ошибка", content=Label(text=message), size_hint=(0.5, 0.5))
    error_popup.open()


def build_structure(building, city, faction, quantity, on_complete):
    if building == "Здания" or city == "Города":
        show_error_message("Выберите здание для постройки и город!")
        return

    # Проверяем, что количество зданий больше 0
    if quantity <= 0:
        show_error_message("Количество зданий должно быть больше 0!")
        return

    # Ищем город в списке городов фракции
    city_found = next((c for c in faction.cities if c.get('name') == city), None)

    if city_found is None:
        show_error_message("Выбранный город не найден!")
        return

    # Определяем стоимость постройки
    building_cost = 200 if building == "Фабрика" else 300 if building == "Больница" else None
    if building_cost is None:
        show_error_message("Неизвестный тип здания!")
        return

    total_cost = building_cost * quantity

    # Проверяем, хватает ли денег на постройку всех зданий
    if not faction.cash_build(total_cost):
        show_error_message(f"Недостаточно денег для постройки {quantity} зданий! \nСтоимость: {total_cost} крон")
        return

    # Строим здания
    for _ in range(quantity):
        if building == "Фабрика":
            faction.build_factory(city_found['name'])  # Передаем имя города
        elif building == "Больница":
            faction.build_hospital(city_found['name'])  # Передаем имя города

    # Выполняем функцию завершения постройки
    if on_complete:
        Clock.schedule_once(on_complete, 0.5)  # Задержка 0.5 секунды для отображения сообщений


def open_build_popup(faction):
    def rebuild_popup(*args):
        build_popup.dismiss()
        open_build_popup(faction)

    faction.cities = faction.load_cities_from_file()
    build_popup = Popup(
        title="Состояние государства",
        size_hint=(0.8, 0.8),
        background_color=(0.1, 0.1, 0.1, 1),  # Темный фон окна
        title_color=(1, 1, 1, 1),  # Белый цвет заголовка
    )

    main_layout = FloatLayout()

    # Информационный блок
    stats_box = BoxLayout(
        orientation='vertical',
        size_hint=(1, 0.65),
        pos_hint={'x': 0, 'y': 0.3},
        padding=[20, 20, 20, 20],
        spacing=10,
    )

    stats_info = (
        f"[b]1 больница (за ход):[/b] +500 рабочих / -{faction.buildings_info_fration()} крон\n"
        f"[b]1 фабрика (за ход):[/b] +1000 еды / -200 рабочих\n"
        f"[size=20][b]Статистика:[/b][/size]\n"
        f"Количество больниц: {faction.hospitals}\n"
        f"Количество фабрик: {faction.factories}\n"
        f"Количество рабочих на фабриках: {faction.work_peoples}\n"
        f"Чистый численности рабочих: {faction.clear_up_peoples}\n"
        f"Потребление денег больницами: {faction.money_info}\n"
        f"Чистое производство еды: {faction.food_info}\n"
        f"Чистый прирост денег: {faction.money_up}\n"
        f"Доход от налогов: {faction.taxes_info}\n"
        f"Эффект от налогов (Изменение рабочих): {faction.apply_tax_effect(int(faction.current_tax_rate[:-1])) if faction.tax_set else 'Налог не установлен'}\n"
    )

    stats_label = Label(
        text=stats_info,
        markup=True,  # Используем разметку Kivy для форматирования текста
        color=(1, 1, 1, 1),  # Белый текст
        halign="left",
        valign="top",
        size_hint=(1, None),
        height=300,
    )
    stats_box.add_widget(stats_label)

    with stats_box.canvas.before:
        Color(0.2, 0.2, 0.2, 1)  # Серый фон
        RoundedRectangle(size=stats_box.size, pos=stats_box.pos, radius=[10])

    main_layout.add_widget(stats_box)

    # Блок выбора зданий
    building_box = BoxLayout(
        orientation='vertical',
        size_hint=(0.3, 0.2),
        pos_hint={'x': 0.02, 'y': 0.05},
        spacing=10,
    )
    building_main_button = Button(
        text="Выберите здание",
        size_hint=(1, None),
        height=44,
        background_color=(0.3, 0.4, 0.9, 1),
    )
    building_dropdown = DropDown(auto_dismiss=False)

    for building, icon in BUILDINGS.items():
        btn = Button(
            text=building,
            size_hint_y=None,
            height=44,
            background_color=(0.4, 0.5, 1, 1),
        )
        btn.bind(on_release=lambda btn: building_dropdown.select(btn.text))
        building_dropdown.add_widget(btn)

    building_main_button.bind(on_release=building_dropdown.open)
    building_dropdown.bind(on_select=lambda instance, x: setattr(building_main_button, 'text', x))

    building_box.add_widget(Label(text="Здания:", size_hint=(1, None), height=30, color=(1, 1, 1, 1)))
    building_box.add_widget(building_main_button)
    main_layout.add_widget(building_box)

    # Блок выбора города
    city_box = BoxLayout(
        orientation='vertical',
        size_hint=(0.3, 0.2),
        pos_hint={'x': 0.32, 'y': 0.05},
        spacing=10,
    )
    city_main_button = Button(
        text="Выберите город",
        size_hint=(1, None),
        height=44,
        background_color=(0.3, 0.8, 0.4, 1),
    )
    city_dropdown = DropDown(auto_dismiss=False)

    for city in faction.cities:
        city_text = city.get('name', 'Неизвестный город')
        btn = Button(
            text=city_text,
            size_hint_y=None,
            height=44,
            background_color=(0.4, 0.9, 0.5, 1),
        )
        btn.bind(on_release=lambda btn: city_dropdown.select(btn.text))
        city_dropdown.add_widget(btn)

    city_main_button.bind(on_release=city_dropdown.open)
    city_dropdown.bind(on_select=lambda instance, x: setattr(city_main_button, 'text', x))

    city_box.add_widget(Label(text="Города:", size_hint=(1, None), height=30, color=(1, 1, 1, 1)))
    city_box.add_widget(city_main_button)
    main_layout.add_widget(city_box)

    # Поле для ввода количества зданий
    quantity_input = TextInput(
        text="1",  # По умолчанию 1 здание
        size_hint=(0.07, None),
        height=44,
        input_filter="int",  # Разрешаем ввод только целых чисел
        multiline=False,
        pos_hint={'x': 0.62, 'y': 0.05},  # Разместим рядом с кнопкой "Построить"
    )
    main_layout.add_widget(quantity_input)

    # Обновленная кнопка "Построить"
    button_box = BoxLayout(
        orientation='vertical',
        size_hint=(0.3, 0.2),
        pos_hint={'x': 0.69, 'y': 0.05},
        spacing=10,
    )
    build_button = Button(
        text="Построить",
        size_hint=(1, None),
        height=44,
        background_color=(1, 0.4, 0.4, 1),
    )
    build_button.bind(on_release=lambda x: build_structure(
        building_main_button.text,
        city_main_button.text,
        faction,
        int(quantity_input.text),  # Получаем количество зданий из поля
        rebuild_popup
    ))
    button_box.add_widget(build_button)
    main_layout.add_widget(button_box)

    build_popup.content = main_layout
    build_popup.open()





#---------------------------------------------------------------

def open_trade_popup(game_instance):
    """Открытие окна торговли с графиком цен"""

    trade_layout = BoxLayout(orientation='vertical', padding=10)

    # Генерация и сохранение графика как изображения на основе текущей цены
    plot_data = game_instance.plot_food_price()  # Передаем текущую цену
    with open('food_price.png', 'wb') as f:
        f.write(plot_data)  # Сохранение изображения

    img = Image(source='food_price.png', size_hint_y=None, height=400)

    # Кнопки для покупки и продажи
    button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
    buy_btn = Button(text="Купить 10000 еды", size_hint_x=0.5)
    sell_btn = Button(text="Продать 10000 еды", size_hint_x=0.5)
    button_layout.add_widget(buy_btn)
    button_layout.add_widget(sell_btn)

    trade_layout.add_widget(img)  # Добавляем изображение графика в основной контейнер
    trade_layout.add_widget(button_layout)  # Добавляем кнопки в основной контейнер

    trade_popup = Popup(title="Торговля", content=trade_layout, size_hint=(0.8, 0.8))

    # Обработка покупки еды
    buy_btn.bind(on_press=lambda x: handle_trade(game_instance, 'buy', trade_popup))
    # Обработка продажи еды
    sell_btn.bind(on_press=lambda x: handle_trade(game_instance, 'sell', trade_popup))

    trade_popup.open()

    # Обновление графика при закрытии попапа
    trade_popup.bind(on_dismiss=lambda instance: update_food_price_graph(game_instance, img))


def handle_trade(game_instance, action, trade_popup):
    """Обработка торговли (покупка/продажа еды)"""
    result = game_instance.trade_food(action)
    if result is not None:  # Если торговля прошла успешно
        show_message("Успех", f"{'Куплено' if action == 'buy' else 'Продано'} 10000 единиц еды.")
    else:  # Если была ошибка
        show_message("Ошибка", "Не удалось завершить операцию.")
    trade_popup.dismiss()  # Закрываем попап после операции


def update_food_price_graph(game_instance, img):
    """Обновление графика цен на еду"""
    plot_data = game_instance.plot_food_price()  # Генерируем новое изображение графика
    with open('food_price.png', 'wb') as f:
        f.write(plot_data)  # Сохраняем изображение
    img.source = 'food_price.png'  # Обновляем источник изображения
    img.reload()  # Перезагружаем изображение для обновления отображения


def open_tax_popup(faction):
    """Открытие попапа для выбора ставки налога через выпадающий список"""

    tax_popup = Popup(title="Управление налогами", size_hint=(0.8, 0.4), background_color=(0.1, 0.1, 0.1, 1))

    main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

    # Устанавливаем начальное значение для налоговой ставки
    current_tax_rate = '0%' if not faction.tax_set else f"{faction.current_tax_rate}"  # Значение по умолчанию, если налог не установлен

    # Создание кастомного выпадающего списка для выбора налоговой ставки
    tax_spinner = Spinner(
        text=current_tax_rate,  # Устанавливаем текущее значение
        values=('0%', '5%', '15%', '25%', '35%', '50%', '65%', '75%', '85%', '95%', '100%'),  # Добавляем '0%'
        size_hint=(0.8, None),
        height=44,
        background_normal='',  # Убираем стандартный фон
        background_color=(0.3, 0.5, 0.7, 1),
        color=(1, 1, 1, 1),
        font_size=20,
        border=(5, 5, 5, 5),
        padding=(10, 10)
    )

    # Кастомизация стрелки
    class CustomArrow(ButtonBehavior, Image):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.source = 'path_to_custom_arrow_image.png'  # Замените на путь к вашему изображению стрелки
            self.size_hint = (None, None)
            self.size = (40, 40)

    # Элемент для стрелки
    custom_arrow = CustomArrow()
    tax_spinner.add_widget(custom_arrow)  # Добавление кастомной стрелки в Spinner

    # Метка для текущей ставки налога
    tax_label = Label(
        text=f"Текущая ставка налога: {tax_spinner.text}",
        color=(1, 1, 1, 1),
        font_size=18,
        size_hint=(1, None),
        height=40,
    )

    def update_tax_rate(spinner, text):
        """Функция для обновления ставки налога при выборе из списка"""
        tax_label.text = f"Текущая ставка налога: {text}"  # Обновляем текст метки при выборе
        tax_rate = int(text[:-1])  # Убираем '%' и приводим к числу
        faction.set_taxes(tax_rate)  # Устанавливаем ставку налога
        faction.apply_tax_effect(tax_rate)  # Считаем отрицательный эффект

    tax_spinner.bind(text=update_tax_rate)

    # Кнопка для подтверждения нового налога
    set_tax_button = Button(
        text="Установить уровень налогов",
        size_hint_y=None,
        height=50,
        background_color=(0.4, 0.6, 0.2, 1),
        color=(1, 1, 1, 1),
        font_size=18,
        border=(10, 10, 10, 10),
        background_normal='',
    )

    def set_tax(instance):
        """Установить новый уровень налогов и закрыть попап"""
        faction.current_tax_rate = tax_spinner.text  # Обновляем текущее значение налога в faction
        tax_popup.dismiss()

    set_tax_button.bind(on_press=set_tax)

    # Добавляем элементы в layout
    main_layout.add_widget(tax_label)
    main_layout.add_widget(tax_spinner)
    main_layout.add_widget(set_tax_button)

    # Добавление стилизации фона и округленных углов
    with main_layout.canvas.before:
        Color(0.2, 0.2, 0.2, 1)  # Цвет фона
        RoundedRectangle(size=main_layout.size, pos=main_layout.pos, radius=[15])

    tax_popup.content = main_layout
    tax_popup.open()


def start_economy_mode(faction, game_area):
    """Инициализация экономического режима для выбранной фракции"""

    # Кнопки для управления экономикой
    economy_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), pos_hint={'x': 0, 'y': 0})

    build_btn = Button(text="Состояние государства", size_hint_x=0.33, size_hint_y=None, height=50)
    trade_btn = Button(text="Торговля", size_hint_x=0.33, size_hint_y=None, height=50)
    tax_btn = Button(text="Управление налогами", size_hint_x=0.33, size_hint_y=None, height=50)

    economy_layout.add_widget(build_btn)
    economy_layout.add_widget(trade_btn)
    economy_layout.add_widget(tax_btn)

    # Добавляем layout с кнопками в нижнюю часть экрана
    game_area.add_widget(economy_layout)

    # Привязываем кнопку "Построить здание" к функции открытия попапа
    build_btn.bind(on_press=lambda x: open_build_popup(faction))
    tax_btn.bind(on_press=lambda x: open_tax_popup(faction))
    trade_btn.bind(on_press=lambda x: open_trade_popup(faction))
