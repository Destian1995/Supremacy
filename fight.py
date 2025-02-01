import math
import json
import os
import shutil

from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.app import App
from kivy.uix.scrollview import ScrollView
from kivy.uix.treeview import TreeView, TreeViewLabel

# временные массивы для армий
defence_units = []
attack_units = []

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


def check_attack_city(defending_city):
    fractions = get_faction_of_city(defending_city)
    with open(f'files/config/attack_in_city/{transform_filename(fractions)}_check.txt', 'w', encoding='utf-8') as file:
        file.write(f"False")


# Функция для сохранения данных в файл
def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def update_army_file(file_path, city_name, updated_units):
    # Загружаем данные из файла
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Проверяем, есть ли город в данных
    if city_name in data:
        # Обновляем информацию о юнитах города
        for city_info in data[city_name]:
            city_info['units'] = updated_units

    # Перезаписываем файл с обновленными данными
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# Функция для записи данных в файл
def save_report_to_file(report_data, file_path='files/config/reports/report_fight.json'):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)


# Функция для пересчета характеристик юнита
def update_unit_stats(unit, new_count):
    original_count = unit['unit_count']
    if original_count > 0:
        for stat, value in unit['units_stats'].items():
            if stat != "Класс юнита":
                # Пересчитываем значение на единицу юнита и умножаем на новое количество
                value_per_unit = value / original_count
                unit['units_stats'][stat] = math.floor(value_per_unit * new_count)
    unit['unit_count'] = new_count


def update_diplomacy_data(attacking_fraction, defending_fraction, city_name):
    try:
        with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
            diplomacies = json.load(file)

        # Проверяем и удаляем город из защитников
        if city_name in diplomacies[defending_fraction]["города"]:
            diplomacies[defending_fraction]["города"].remove(city_name)
            print(f"{city_name} удален из списка защитников в дипломатии.")

        # Добавляем город к атакующим
        if city_name not in diplomacies[attacking_fraction]["города"]:
            diplomacies[attacking_fraction]["города"].append(city_name)
            print(f"{city_name} добавлен в список атакующих фракций в дипломатии.")

        # Сохраняем обновленные данные
        with open('files/config/status/diplomaties.json', 'w', encoding='utf-8') as file:
            json.dump(diplomacies, file, ensure_ascii=False, indent=4)
    except KeyError as e:
        print(f"Ошибка: указана несуществующая фракция - {e}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при работе с файлом дипломатии: {e}")


def update_city_data(attacking_fraction, defending_fraction, city_name):
    fraction_def = transform_filename(defending_fraction)
    fraction_off = transform_filename(attacking_fraction)

    # Открываем файл city.json для чтения и записи
    with open('files/config/city.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    city_data = None  # Данные города, которые нужно перенести

    # Удаляем город из защитника
    for kingdom, details in data['kingdoms'].items():
        if kingdom == defending_fraction:
            city_to_remove = next(
                (city for city in details['fortresses'] if city['name'] == city_name), None
            )
            if city_to_remove:
                city_data = city_to_remove
                details['fortresses'].remove(city_to_remove)
                print(f"{city_name} удален из {defending_fraction}.")
                break

    # Если город найден, добавляем его к атакующей фракции
    if city_data:
        data['kingdoms'][attacking_fraction]['fortresses'].append(city_data)
        print(f"{city_name} добавлен в {attacking_fraction}.")
    else:
        print(f"Город {city_name} не найден в {defending_fraction}.")
        return

    # Сохраняем изменения в city.json
    with open('files/config/city.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    # Перемещение зданий
    defending_buildings_file = f'files/config/buildings_in_city/{fraction_def}_buildings_city.json'
    attacking_buildings_file = f'files/config/buildings_in_city/{fraction_off}_buildings_city.json'

    # Читаем данные из файла защитника
    if os.path.exists(defending_buildings_file):
        try:
            with open(defending_buildings_file, 'r', encoding='utf-8') as file:
                defending_buildings_data = json.load(file) or {}
        except json.JSONDecodeError:
            print(f"Ошибка чтения файла {defending_buildings_file}. Файл может быть поврежден.")
            defending_buildings_data = {}
    else:
        defending_buildings_data = {}

    # Читаем данные из файла атакующего
    if os.path.exists(attacking_buildings_file):
        try:
            with open(attacking_buildings_file, 'r', encoding='utf-8') as file:
                attacking_buildings_data = json.load(file) or {}
        except json.JSONDecodeError:
            print(f"Ошибка чтения файла {attacking_buildings_file}. Файл может быть поврежден.")
            attacking_buildings_data = {}
    else:
        attacking_buildings_data = {}

    # Переносим здания города
    if city_name in defending_buildings_data:
        buildings_to_move = defending_buildings_data.pop(city_name)

        # Добавляем здания в файл атакующей фракции
        if city_name in attacking_buildings_data:
            for building, count in buildings_to_move["Здания"].items():
                attacking_buildings_data[city_name]["Здания"][building] = (
                        attacking_buildings_data[city_name]["Здания"].get(building, 0) + count
                )
        else:
            attacking_buildings_data[city_name] = buildings_to_move

        # Сохраняем обновления
        with open(defending_buildings_file, 'w', encoding='utf-8') as file:
            json.dump(defending_buildings_data, file, ensure_ascii=False, indent=4)

        with open(attacking_buildings_file, 'w', encoding='utf-8') as file:
            json.dump(attacking_buildings_data, file, ensure_ascii=False, indent=4)

        print(f"Здания города {city_name} перенесены из {fraction_def} в {fraction_off}.")
    else:
        print(f"Город {city_name} отсутствует в файле зданий для {fraction_def}.")

    # Обновляем данные дипломатии
    update_diplomacy_data(attacking_fraction, defending_fraction, city_name)



def not_found_def_army(attacking_army, ii_file_path, user_file_path, attacking_city, attacking_fraction,
                       defending_fraction, defending_city, defending_city_coords):
    print(f"В городе {defending_city} нет защитной армии. Атакующие занимают город без боя.")

    # Проверяем, существует ли файл и если он пустой, присваиваем пустой словарь
    if os.path.exists(user_file_path) and os.path.getsize(user_file_path) > 0:
        with open(user_file_path, 'r', encoding='utf-8') as f:
            attacking_data = json.load(f)
    else:
        attacking_data = {}

    if os.path.exists(ii_file_path) and os.path.getsize(ii_file_path) > 0:
        with open(ii_file_path, 'r', encoding='utf-8') as f:
            defending_data = json.load(f)
    else:
        defending_data = {}

    # Удаление города из данных защитников
    if defending_city in defending_data:
        del defending_data[defending_city]

    # Очистка гарнизона атакующего города
    if attacking_city in attacking_data:
        attacking_data[attacking_city] = []  # Полная очистка гарнизона

    # Добавление атакующих юнитов в занятый город
    if defending_city not in attacking_data:
        attacking_data[defending_city] = []

    attacking_data[defending_city].append({
        "coordinates": str(defending_city_coords),
        "units": attacking_army
    })

    # Сохранение данных в файлы
    save_json(user_file_path, attacking_data)
    save_json(ii_file_path, defending_data)

    # Обновляем данные о захваченном городе
    update_city_data(attacking_fraction, defending_fraction, defending_city)

    print(f"Атакующие успешно заняли город {defending_city}.")
    return  # Завершение функции, так как бой не нужен

# Окно отчета боя
def show_battle_report(report_data):
    'Тут все работает нормально больше ничего не трогаем'
    print('================================================================')
    print('report_data', report_data)
    print('================================================================')
    content = BoxLayout(orientation='vertical')

    # Создаем ScrollView для отображения таблиц
    scroll_view = ScrollView()

    # Создаем основной GridLayout для размещения таблиц
    main_layout = BoxLayout(orientation='vertical', size_hint_y=None)
    main_layout.bind(minimum_height=main_layout.setter('height'))

    # Функция для создания таблицы с данными
    def create_battle_table(side_data, title):
        grid_layout = GridLayout(cols=4, size_hint_y=None)
        grid_layout.bind(minimum_height=grid_layout.setter('height'))

        # Заголовки таблицы
        grid_layout.add_widget(Label(text="Тип Юнита", bold=True))
        grid_layout.add_widget(Label(text="На начало боя", bold=True))
        grid_layout.add_widget(Label(text="Потери", bold=True))
        grid_layout.add_widget(Label(text="Осталось юнитов", bold=True))

        # Заполнение данных
        for unit_data in side_data:
            grid_layout.add_widget(Label(text=unit_data['unit_name']))
            grid_layout.add_widget(Label(text=str(unit_data["initial_count"])))
            grid_layout.add_widget(Label(text=str(unit_data["losses"])))
            grid_layout.add_widget(Label(text=str(unit_data["final_count"])))

        return grid_layout

    # Разделение данных по сторонам (атакующие и обороняющиеся)
    attacking_data = [item for item in report_data if item['side'] == 'attacking']
    defending_data = [item for item in report_data if item['side'] == 'defending']

    # Создаем таблицы для атакующих и обороняющихся
    attacking_table = create_battle_table(attacking_data, "атакующей стороны")
    defending_table = create_battle_table(defending_data, "обороняющейся стороны")

    # Добавляем таблицы в основной layout
    main_layout.add_widget(attacking_table)
    main_layout.add_widget(defending_table)

    # Добавляем основной layout в ScrollView
    scroll_view.add_widget(main_layout)
    content.add_widget(scroll_view)

    # Вычисление общих потерь
    total_attacking_losses = sum(item['losses'] for item in attacking_data)
    total_defending_losses = sum(item['losses'] for item in defending_data)

    # Добавляем раздел для итоговых потерь
    totals_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=100)
    totals_layout.add_widget(Label(text="Общие потери:", bold=True, size_hint_y=None, height=30))

    # Потери атакующей стороны
    totals_layout.add_widget(
        Label(text=f"Для атакующей стороны: {total_attacking_losses}", size_hint_y=None, height=30))

    # Потери обороняющейся стороны
    totals_layout.add_widget(
        Label(text=f"Для обороняющейся стороны: {total_defending_losses}", size_hint_y=None, height=30))

    # Добавляем итоговый блок в content
    content.add_widget(totals_layout)

    # Кнопка для закрытия окна
    close_button = Button(text="Закрыть", size_hint_y=None, height=50)
    close_button.bind(on_release=lambda instance: popup.dismiss())
    content.add_widget(close_button)

    # Открытие всплывающего окна
    popup = Popup(title="Итоги боя", content=content, size_hint=(0.7, 0.7))
    popup.open()


def fight(ii_file_path, user_file_path, attacking_city, defending_city_coords, defending_city, defending_army,
          attacking_army, attacking_fraction, defending_fraction):
    global remaining_attacker_units, remaining_defender_units, report_check, full_report_data
    check_attack_city(defending_city)
    all_damage = sum(damage['units_stats']['Урон'] for damage in attacking_army)

    damage_to_infrastructure(defending_city, all_damage)
    print('defending_army', defending_army)
    # Проверка, если в городе отсутствует защитная армия
    if not defending_army:
        not_found_def_army(attacking_army, ii_file_path, user_file_path, attacking_city, attacking_fraction,
                           defending_fraction, defending_city, defending_city_coords)
        return

    # Коэффициенты для классов юнитов
    class_coefficients = {
        '1': 1.1,  # Пехота
        '2': 1.4,  # Бронетехника
        '3': 1.9,  # Артиллерия
        '4': 2.8  # Авиация
    }

    # Вычисление коэффициентов и процентов вклада для каждого юнита в атакующей армии
    unit_koefs_attack = {}
    total_damage = 0
    total_units = 0
    damage_info = []
    surviving_units_def = []

    for unit in attacking_army:
        unit_damage = unit['units_stats']['Урон']
        unit_count = unit['unit_count']
        unit_type = unit['units_stats']['Класс юнита']
        coefficient = class_coefficients.get(unit_type)

        # Коэффициент для юнита: Урон / Количество юнитов
        unit_koefs_attack[unit['unit_name']] = unit_damage / unit_count
        total_damage += unit_damage * unit_count * coefficient
        total_units += unit_count
    print('unit_koefs_attack', unit_koefs_attack)
    # Рассчитываем процент вклада каждого юнита в общую силу атаки
    unit_percent_contributions_attack = {}
    for unit in attacking_army:
        unit_damage = unit['units_stats']['Урон']
        unit_count = unit['unit_count']
        unit_type = unit['units_stats']['Класс юнита']
        coefficient = class_coefficients.get(unit_type)

        # Процент вклада юнита в общую силу атаки
        unit_strength = unit_damage * unit_count * coefficient
        unit_percent_contributions_attack[unit['unit_name']] = unit_strength / total_damage

    print('Процент атаки юнитов', unit_percent_contributions_attack)
    print('Общая сила атаки', total_damage)
    # Вычисление коэффициентов и процентов вклада для каждого юнита
    unit_koefs_def = {}
    total_health = 0
    total_defense = 0
    total_units = 0
    damage_info = []
    surviving_units_attack = []
    destroyed_units_count = 0

    for unit in defending_army:
        unit_health = unit['units_stats']['Живучесть']
        unit_defense = unit['units_stats']['Защита']
        unit_count = unit['unit_count']

        # Коэффициент для юнита: (Живучесть + Защита) / Количество юнитов
        unit_koefs_def[unit['unit_name']] = (unit_health + unit_defense) / unit_count
        total_health += unit_health * unit_count
        total_defense += unit_defense * unit_count
        total_units += unit_count

    # Рассчитываем процент вклада каждого юнита в общую силу
    unit_percent_contributions_defense = {}
    total_strength = total_health + total_defense
    for unit in defending_army:
        unit_health = unit['units_stats']['Живучесть']
        unit_defense = unit['units_stats']['Защита']
        unit_count = unit['unit_count']

        # Процент вклада юнита в общую силу
        unit_strength = (unit_health + unit_defense) * unit_count
        unit_percent_contributions_defense[unit['unit_name']] = unit_strength / total_strength
        print(unit_percent_contributions_defense)

    print('Общая защита защитной армии:', total_defense)
    attacking_data = json.load(open(user_file_path, 'r', encoding='utf-8'))
    defending_data = json.load(open(ii_file_path, 'r', encoding='utf-8'))
    print('defe', defending_data)
    # Вычисление максимальной и минимальной величины урона и защиты и НАНОСИМ УРОН
    effective_army_damage = total_damage - total_defense
    print('Эффективный чистый урон', effective_army_damage)
    # Наносим урон по каждому юниту отдельно
    # ЗАЩИТА ПОБЕДИЛА
    if total_damage < total_defense:
        # Наносим урон по каждому юниту отдельно
        # Удаление старых данных о городе защиты
        if defending_city in defending_data:
            del defending_data[defending_city]
            print(f"Город {defending_city} удален из защитников.")

        for unit in defending_army:
            unit_health = unit['units_stats']['Живучесть']
            unit_defense = unit['units_stats']['Защита']
            unit_count = unit['unit_count']
            unit_name = unit['unit_name']
            unit_koef = unit_koefs_def.get(unit['unit_name'])
            unit_percent = unit_percent_contributions_defense.get(unit['unit_name'])

            if not unit_koef or not unit_percent:
                print(f"Нет коэффициента или процента для юнита {unit['unit_name']}")
                continue

            # Сохраняем начальное количество юнитов
            initial_unit_count = unit_count

            # Распределяем урон пропорционально проценту вклада юнита в общую силу
            damage_per_unit = total_damage * unit_percent  # Распределяем урон по юнитам
            remaining_strength = (unit_health + unit_defense) * unit_count - damage_per_unit

            remaining_units = int(remaining_strength // (unit_health + unit_defense))  # Пересчитываем остаток
            # Пересчитываем остаток
            if remaining_units < 0:
                remaining_units = 0
            print('remaining_units', remaining_units)
            destroyed_count_for_unit = initial_unit_count - remaining_units
            unit_info = calculate_losses(unit_name, starting_army=initial_unit_count, final_army=remaining_units,
                                         destroyed_count_for_unit=destroyed_count_for_unit, side='defending')
            unit['unit_count'] = remaining_units  # Обновляем количество оставшихся юнитов
            surviving_units_def += unit_info

            # Очистка гарнизона атакующего города
            if attacking_city in attacking_data:
                attacking_data[attacking_city] = []  # Полная очистка гарнизона

            # Если город защиты не существует в данных защиты, создаем его
            if defending_city not in defending_data:
                defending_data[defending_city] = []

            update_unit_stats(unit, remaining_units)
            # Добавляем новый защитный юнит
            city_coords = str(defending_city_coords)
            # Убедитесь, что attacking_data не пустой
            if defending_data[defending_city]:
                for entry in defending_data[defending_city]:
                    if entry['coordinates'] == city_coords:
                        entry['units'].append(unit)
            else:
                # Добавляем новые данные для города
                defending_data[defending_city].append({
                    "coordinates": city_coords,
                    "units": [unit]  # Для каждого города защита или атака должна добавлять актуальные войска
                })

        # Удаляем атакующих после битвы
        for unit in attacking_army:
            unit_count = unit['unit_count']
            unit_name = unit['unit_name']
            unit_info = calculate_losses(unit_name, unit_count, final_army=0, destroyed_count_for_unit=unit_count,
                                         side='attacking')
            surviving_units_attack += unit_info

    elif total_damage > total_defense:
        # Логика для победы армии атаки
        # Удаление старых данных о городе защиты
        if defending_city in defending_data:
            del defending_data[defending_city]
            print(f"Город {defending_city} удален из защитников.")

        for unit in attacking_army:
            unit_damage = unit['units_stats']['Урон']
            unit_count = unit['unit_count']
            unit_koef = unit_koefs_attack.get(unit['unit_name'])
            unit_name = unit['unit_name']
            unit_percent = unit_percent_contributions_attack.get(unit['unit_name'])

            if not unit_koef or not unit_percent:
                print(f"Нет коэффициента или процента для юнита {unit['unit_name']}")
                continue

            # Сохраняем начальное количество юнитов
            initial_unit_count = unit_count

            # Распределяем урон пропорционально проценту вклада юнита в общую силу
            damage_per_unit = effective_army_damage * unit_percent  # Распределяем урон по юнитам
            remaining_strength = unit_damage * unit_count - damage_per_unit
            remaining_units = int(remaining_strength // unit_damage)
            # Пересчитываем остаток
            if remaining_units < 0:
                remaining_units = 0
            destroyed_count_for_unit = initial_unit_count - remaining_units
            unit_info = calculate_losses(unit_name, starting_army=initial_unit_count, final_army=remaining_units,
                                         destroyed_count_for_unit=destroyed_count_for_unit, side='attacking')
            surviving_units_attack += unit_info

            # Очистка гарнизона атакующего города
            if attacking_city in attacking_data:
                attacking_data[attacking_city] = []  # Полная очистка гарнизона

            # Если атакующий город не существует в данных, создаем его
            if defending_city not in attacking_data:
                attacking_data[defending_city] = []
            update_unit_stats(unit, remaining_units)
            print('Осталось', unit, destroyed_count_for_unit)
            print('Обновление', update_unit_stats)
            print('str(defending_city_coords)',str(defending_city_coords))
            # Добавляем новый атакующий юнит
            city_coords = str(defending_city_coords)

            # Убедитесь, что attacking_data не пустой
            if attacking_data[defending_city]:
                for entry in attacking_data[defending_city]:
                    if entry['coordinates'] == city_coords:
                        entry['units'].append(unit)
            else:
                # Добавляем новые данные для города
                attacking_data[defending_city].append({
                    "coordinates": city_coords,
                    "units": [unit]  # Для каждого города защита или атака должна добавлять актуальные войска
                })
            update_city_data(attacking_fraction, defending_fraction, defending_city)

        # Удаляем всех защитников после битвы
        for unit in defending_army:
            unit_count = unit['unit_count']
            unit_name = unit['unit_name']
            unit_info = calculate_losses(unit_name, unit_count, final_army=0,
                                         destroyed_count_for_unit=unit_count,
                                         side='defending')
            surviving_units_def += unit_info

    # Сохраняем обновленные данные в файлы
    save_json(user_file_path, attacking_data)
    save_json(ii_file_path, defending_data)
    surviving_units = surviving_units_attack + surviving_units_def
    show_battle_report(surviving_units)


# Тут все ок не трогаем
def calculate_losses(unit_name, starting_army, final_army, destroyed_count_for_unit, side):
    losses_report = [{
        'unit_name': unit_name,
        'initial_count': starting_army,
        'final_count': final_army,
        'losses': destroyed_count_for_unit,
        'side': side
    }]

    return losses_report


def damage_to_infrastructure(city_name, all_damage):
    print('Начинаем расчет урона по инфраструктуре')
    fraction = get_faction_of_city(city_name)
    path_to_buildings = transform_filename(f'files/config/buildings_in_city/{fraction}_buildings_city.json')
    # Чтение данных о зданиях
    try:
        with open(path_to_buildings, 'r', encoding='utf-8') as file:
            all_data = json.load(file)

        if city_name not in all_data:
            print(f"Город '{city_name}' не найден в файле.")
            return

        city_data = all_data[city_name].get('Здания', {})
    except Exception as e:
        print(f"Ошибка при чтении данных инфраструктуры: {e}")
        return

    print(f"Данные инфраструктуры до удара: {city_data}")

    effective_weapon_damage = all_damage
    print(f"Эффективный урон по инфраструктуре: {effective_weapon_damage}")

    # Константа для урона, необходимого для разрушения одного здания
    DAMAGE_PER_BUILDING = 578797

    # Подсчет общего числа зданий
    total_buildings = sum(city_data.values())
    if total_buildings == 0:
        print("В городе нет зданий для нанесения урона.")
        return

    # Сколько зданий может быть разрушено этим уроном
    potential_destroyed_buildings = int(effective_weapon_damage // DAMAGE_PER_BUILDING)
    print(f"Максимально возможное количество разрушенных зданий: {potential_destroyed_buildings}")

    # Уничтожаем здания, начиная с больниц и фабрик
    damage_info = {}
    for building in ['Больница', 'Фабрика']:
        if building in city_data and city_data[building] > 0:
            count = city_data[building]
            if potential_destroyed_buildings >= count:
                # Уничтожаем все здания этого типа
                damage_info[building] = count
                city_data[building] = 0
                potential_destroyed_buildings -= count
            else:
                # Уничтожаем часть зданий
                damage_info[building] = potential_destroyed_buildings
                city_data[building] -= potential_destroyed_buildings
                potential_destroyed_buildings = 0

            if potential_destroyed_buildings == 0:
                break

    print(f"Данные инфраструктуры после удара: {city_data}")

    # Сохранение обновленной инфраструктуры в файл
    try:
        all_data[city_name]['Здания'] = city_data
        with open(path_to_buildings, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)
        print('Обновленная инфраструктура сохранена.')
    except Exception as e:
        print(f"Ошибка при сохранении данных инфраструктуры: {e}")

    # Показать информацию об уроне
    show_damage_info_infrastructure(damage_info)


def show_damage_info_infrastructure(damage_info):
    content = BoxLayout(orientation='vertical')
    message = "Информация об уроне по инфраструктуре:\n\n"
    for building, destroyed_count in damage_info.items():
        message += f"{building.capitalize()}, уничтожено зданий: {destroyed_count}\n"

    label = Label(text=message, size_hint_y=None, height=400)
    close_button = Button(text="Закрыть", size_hint_y=None, height=50)
    close_button.bind(on_release=lambda instance: popup.dismiss())

    content.add_widget(label)
    content.add_widget(close_button)

    popup = Popup(title="Результат удара по инфраструктуре", content=content, size_hint=(0.7, 0.7))
    popup.open()
