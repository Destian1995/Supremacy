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


def transform_filename(file_path, translation_dict):
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


# Функция для сохранения данных в файл
def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
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
    with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
        diplomacies = json.load(file)

    city_moved = False  # Флаг для отслеживания перемещения города

    for kingdom, data in diplomacies.items():
        if city_name in data["города"]:
            # Удаляем город из защитников
            if kingdom == defending_fraction:
                data["города"].remove(city_name)
                print(f"{city_name} удален из списка защитников в дипломатии.")
                city_moved = True

        # Добавляем город в список атакующей фракции
        if kingdom == attacking_fraction and city_moved:
            if city_name not in data["города"]:
                data["города"].append(city_name)
                print(f"{city_name} добавлен в список атакующих фракций в дипломатии.")

    with open('files/config/status/diplomaties.json', 'w', encoding='utf-8') as file:
        json.dump(diplomacies, file, ensure_ascii=False, indent=4)


def update_city_data(attacking_fraction, defending_fraction, city_name, city_coords):
    # Открываем файл city.json для чтения и записи
    with open('files/config/city.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    city_data = None  # Переменная для хранения данных города

    # Проходим по всем фракциям и удаляем город из защитника
    for kingdom, details in data['kingdoms'].items():
        for city in details['fortresses']:
            if city['name'] == city_name and kingdom == defending_fraction:
                city_data = city  # Сохраняем город для переноса
                details['fortresses'].remove(city)
                print(f"{city_name} удален из {defending_fraction}.")
                break
        if city_data:
            break

    # Добавляем город в атакующую фракцию, если он был найден
    if city_data:
        data['kingdoms'][attacking_fraction]['fortresses'].append(city_data)
        print(f"{city_name} добавлен в {attacking_fraction}.")

    # Сохраняем изменения обратно в файл
    with open('files/config/city.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    # Обновляем дипломатию
    update_diplomacy_data(attacking_fraction, defending_fraction, city_name)


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
        grid_layout.add_widget(Label(text="Осталось юнитов", bold=True))
        grid_layout.add_widget(Label(text="Потери", bold=True))

        # Заполнение данных
        for unit_data in side_data:
            grid_layout.add_widget(Label(text=unit_data['unit_name']))
            grid_layout.add_widget(Label(text=str(unit_data["initial_count"])))
            grid_layout.add_widget(Label(text=str(unit_data["final_count"])))
            grid_layout.add_widget(Label(text=str(unit_data["losses"])))

        return grid_layout

    # Разделение данных по сторонам (атакующие и обороняющиеся)
    attacking_data = [item for item in report_data if item['side'] == 'attacking']
    defending_data = [item for item in report_data if item['side'] == 'defending']

    # Создаем таблицы для атакующих и обороняющихся
    attacking_table = create_battle_table(attacking_data, "атакующей стороны")
    defending_table = create_battle_table(defending_data, "обороняющейся стороны")

    # Добавляем таблицы в основной layout
    main_layout.add_widget(Label(text="Отчет о потере войск", bold=True, size_hint_y=None, height=40))
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
    popup = Popup(title="Отчет о потере войск", content=content, size_hint=(0.7, 0.7))
    popup.open()


# Функция для боя
def fight(ii_file_path, user_file_path, attacking_city, defending_city_coords, defending_city,
          attacking_city_coords, defending_army, attacking_army, attacking_fraction, defending_fraction):
    global remaining_attacker_units, remaining_defender_units

    starting_attacking_army = [
        {
            "user_name": unit['unit_name'],
            "user_count": unit['unit_count'],
            "side": "attacking"
        }
        for unit in attacking_army
    ]  # Новый словарь для дальнейших расчетов потерь
    starting_defending_army = [
        {
            "user_name": unit['unit_name'],
            "user_count": unit['unit_count'],
            "side": "defending"
        }
        for unit in defending_army
    ] # Новый словарь для дальнейших расчетов потерь
    print('starting_attacking_army', starting_attacking_army)
    print('starting_defending_army', starting_defending_army)

    print('attacking_army ', attacking_army)
    print('defending_army ', defending_army)
    all_damage = 0
    for damage in attacking_army:
        all_damage += damage['units_stats']['Урон']

    print('Общий урон армии атаки:', all_damage)
    damage_to_infrastructure(defending_city, all_damage)
    # Проверка, если в городе отсутствует защитная армия
    if not defending_army:
        print(f"В городе {defending_city} нет защитной армии. Атакующие занимают город без боя.")

        # Загрузка данных атакующего и защитника
        attacking_data = json.load(open(user_file_path, 'r', encoding='utf-8'))
        defending_data = json.load(open(ii_file_path, 'r', encoding='utf-8'))

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
        update_city_data(attacking_fraction, defending_fraction, defending_city, defending_city_coords)

        print(f"Атакующие успешно заняли город {defending_city}.")
        return  # Завершение функции, так как бой не нужен

    at_count = len(attacking_army)
    def_count = len(defending_army)

    if 0 < at_count != def_count > 0:
        if at_count > def_count:
            last_unit = attacking_army[-1]  # Получаем последнее значение
            attack_units.append(last_unit)  # Добавляем его в массив
            print("Последний юнит атакующих добавлен в массив:", attack_units)
        elif at_count < def_count:
            last_unit = defending_army[-1]  # Получаем последнее значение
            defence_units.append(last_unit)  # Добавляем его в массив
            print("Последний юнит обороняющих добавлен в массив:", defence_units)

    print("Начало боя между городами.")
    print(f"Атакующий город: {attacking_city}, координаты: {attacking_city_coords}")
    print(f"Защитник: {defending_city}, координаты: {defending_city_coords}")

    while attacking_army or defending_army:
        # Проверяем, если есть юниты в атакующей армии
        if attacking_army:
            attacker_unit = attacking_army.pop(0)
        else:
            attacker_unit = {'unit_image': '', 'unit_name': '', 'unit_count': 1,
                             'units_stats': {'Урон': 0, 'Защита': 0, 'Живучесть': 0, 'Класс юнита': '1'}}

        # Проверяем, если есть юниты в обороняющей армии
        if defending_army:
            defender_unit = defending_army.pop(0)
        else:
            defender_unit = {'unit_image': '', 'unit_name': '', 'unit_count': 1,
                             'units_stats': {'Урон': 0, 'Защита': 0, 'Живучесть': 0, 'Класс юнита': '1'}}

        # Если есть оба юнита, начинаем бой
        if attacker_unit and defender_unit:
            print(f"Начинаем бой с юнитами: {attacker_unit['unit_name']} и {defender_unit['unit_name']}")
            remaining_attacker_units, remaining_defender_units = recursive_fight(attacker_unit, defender_unit)

            # Обновляем данные атакующих
            if remaining_attacker_units > 0:
                update_unit_stats(attacker_unit, remaining_attacker_units)
                attack_units.append(attacker_unit)
                print(f'Оставшиеся юниты в массиве атаки: {attack_units}')
                print(f'Обновляем данные по атаке: {attacker_unit}')
            else:
                print(f"Юнит {attacker_unit['unit_name']} уничтожен и будет удален из временного массива.")
                if attacker_unit in attack_units:
                    attack_units.remove(attacker_unit)

            # Обновляем данные защитников
            if remaining_defender_units > 0:
                update_unit_stats(defender_unit, remaining_defender_units)
                defence_units.append(defender_unit)
                print(f'Оставшиеся юниты в массиве защиты: {defence_units}')
                print(f"Обновляем данные по обороне: {defender_unit}")
            else:
                print(f"Юнит {defender_unit['unit_name']} уничтожен и будет удален из временного массива.")
                if defender_unit in defence_units:
                    defence_units.remove(defender_unit)


        # Если нет пары для атакующего юнита, добавляем его в файл
        elif attacker_unit:
            print(f"Юнит {attacker_unit['unit_name']} не имеет пары, добавляем в файл.")
            # Добавляем атакующего юнита в файл
            attacking_data = json.load(open(user_file_path, 'r', encoding='utf-8'))
            if attacking_city not in attacking_data:
                attacking_data[attacking_city] = []
            attacking_data[attacking_city].append({
                "coordinates": str(attacking_city_coords),
                "units": [attacker_unit]
            })
            save_json(user_file_path, attacking_data)
            print(f"Атакующий юнит {attacker_unit['unit_name']} добавлен в файл.")

        # Если нет пары для защитного юнита, добавляем его в файл
        elif defender_unit:
            print(f"Юнит {defender_unit['unit_name']} не имеет пары, добавляем в файл.")
            # Добавляем защитного юнита в файл
            defending_data = json.load(open(ii_file_path, 'r', encoding='utf-8'))
            if defending_city not in defending_data:
                defending_data[defending_city] = []
            defending_data[defending_city].append({
                "coordinates": str(defending_city_coords),
                "units": [defender_unit]
            })
            save_json(ii_file_path, defending_data)
            print(f"Защитный юнит {defender_unit['unit_name']} добавлен в файл.")

        # Если есть только один юнит в армии, а другой был уничтожен
        ldef = len(defence_units)
        latack = len(attack_units)

        if ldef > 0 and latack > 0 and (len(attacking_army) == 0 or len(defending_army) == 0):
            # Вызов функции, передаем текущие данные
            fight(ii_file_path, user_file_path, attacking_city, defending_city_coords, defending_city,
                  attacking_city_coords, defence_units, attack_units, attacking_fraction, defending_fraction)

        print('Юнитов в защите', ldef)
        print('Юнитов в атаке', latack)

        # Обработка результата боя
        if remaining_attacker_units > 0 and remaining_defender_units == 0:
            attacking_data = json.load(open(user_file_path, 'r', encoding='utf-8'))
            print(f"Attacking data: {attacking_data}")

            defending_data = json.load(open(ii_file_path, 'r', encoding='utf-8'))
            print(f"Defending data: {defending_data}")

            # Очистка гарнизона атакующего города
            if attacking_city in attacking_data:
                attacking_data[attacking_city] = []  # Полная очистка гарнизона

            # Удаление старых данных о городе защиты
            if defending_city in defending_data:
                del defending_data[defending_city]
                print(f"Город {defending_city} удален из защитников.")

            # Если атакующий город не существует в данных, создаем его
            if defending_city not in attacking_data:
                attacking_data[defending_city] = []

            # Удаление старых данных об атакующих юнитах
            attacking_data[defending_city] = [
                u for u in attacking_data[defending_city]
                if not any(unit["unit_name"] == attacker_unit["unit_name"] for unit in u["units"])]

            # Добавляем новый атакующий юнит
            attacking_data[defending_city].append({
                "coordinates": str(defending_city_coords),
                "units": [attacker_unit]
            })

            # Сохраняем обновленные данные в файлы
            save_json(user_file_path, attacking_data)
            save_json(ii_file_path, defending_data)
            # Обновляем данные о захваченном городе
            update_city_data(attacking_fraction, defending_fraction, defending_city, defending_city_coords)
            print(f"Атакующие заняли город {defending_city}, данные обновлены.")
        else:
            print(f"Все юниты уничтожены, бой завершен.")

        if remaining_defender_units > 0 and remaining_attacker_units == 0:
            user_data = json.load(open(user_file_path, 'r', encoding='utf-8'))
            ii_data = json.load(open(ii_file_path, 'r', encoding='utf-8'))

            # Очистка гарнизона атакующего города
            if attacking_city in user_data:
                user_data[attacking_city] = []  # Полная очистка гарнизона

            # Удаление старых данных о городе защиты из данных атакующих
            if defending_city in user_data:
                del user_data[defending_city]
                print(f"Город {defending_city} удален из данных атакующих.")

            # Если город защиты не существует в данных защиты, создаем его
            if defending_city not in ii_data:
                ii_data[defending_city] = []

            # Удаление старых данных об защитных юнитах в городе защиты
            ii_data[defending_city] = [
                u for u in ii_data[defending_city]
                if not any(unit["unit_name"] == defender_unit["unit_name"] for unit in u["units"])
            ]

            # Добавляем новый защитный юнит
            ii_data[defending_city].append({
                "coordinates": str(defending_city_coords),
                "units": [defender_unit]
            })
            # Сохраняем обновленные данные в файлы
            save_json(user_file_path, user_data)
            save_json(ii_file_path, ii_data)

            print(f"Город {defending_city} успешно защищен, данные обновлены.")
        else:
            print(f"Все защитные юниты уничтожены, бой завершен.")
    # Собираем данные для отчета об атакующих
    attacking_report = []
    for unit in attack_units:
        attacking_report.append({
            'side': 'attacking',
            'unit_name': unit['unit_name'],
            'initial_count': unit['unit_count'],
            'final_count': unit['remaining_count'],  # предполагается, что 'remaining_count' обновляется после боя
            'losses': unit['unit_count'] - unit['remaining_count']
        })

    # Собираем данные для отчета об обороняющихся
    defending_report = []
    for unit in defence_units:
        defending_report.append({
            'side': 'defending',
            'unit_name': unit['unit_name'],
            'initial_count': unit['unit_count'],
            'final_count': unit['remaining_count'],  # предполагается, что 'remaining_count' обновляется после боя
            'losses': unit['unit_count'] - unit['remaining_count']
        })

    if not attack_units or not defence_units:
        # Объединяем данные для передачи в отчет (уже собраны ранее)
        full_report_data = attacking_report + defending_report
        print('full_report_data', full_report_data)
        # Проверяем, чтобы функция вызвалась один раз после завершения боя
        if full_report_data:
            show_battle_report(full_report_data)


# Рекурсивная функция боя
def recursive_fight(attacker_unit, defender_unit):
    print(f"Начинаем бой с юнитами: {attacker_unit['unit_name']} и {defender_unit['unit_name']}")

    # Параметры для расчета
    attacker_damage = attacker_unit['units_stats']['Урон']
    defender_damage = defender_unit['units_stats']['Защита']
    defender_health = defender_unit['units_stats']['Живучесть']

    defender_alls = defender_health + defender_damage
    attacker_alls = attacker_damage

    koef_attack = attacker_alls / attacker_unit['unit_count']
    koef_defense = defender_alls / defender_unit['unit_count']

    print(f"Начальные параметры атакующих: урон {attacker_damage}")
    print(f"Начальные параметры защитников: здоровье {defender_health}, защита {defender_damage}")
    print(f'Полученные коэфы атак: {koef_attack}')
    print(f'Полученные коэфы дэфа: {koef_defense}')

    while attacker_alls > 0 and defender_alls > 0:
        if attacker_alls >= defender_alls:
            defender_alls -= attacker_alls
            print(f"Осталось сил у атакующей стороны {defender_alls * (-1)}")
            if defender_alls <= 0:
                print("Защитники побеждены!")
                break  # Защитники побеждены
            attacker_alls -= defender_alls
            print(f"Осталось сил у защищающей стороны {attacker_alls * (-1)}")
        else:
            attacker_alls -= defender_alls
            print(f"Осталось сил у защищающей стороны {attacker_alls * (-1)}")
            if attacker_alls <= 0:
                print("Атакующие побеждены!")
                break  # Атакующие побеждены
            defender_alls -= attacker_alls
            print(f"Осталось сил у атакующей стороны {defender_alls * (-1)}")

    if koef_attack == 0 or koef_defense == 0:
        return 0, 0
    else:
        return max(0, math.floor(defender_alls * (-1) / koef_attack)), max(0, math.floor(
            attacker_alls * (-1) / koef_defense))


def damage_to_infrastructure(city_name, all_damage):
    print('Начинаем расчет урона по инфраструктуре')
    fraction = get_faction_of_city(city_name)
    path_to_buildings = transform_filename(f'files/config/buildings_in_city/{fraction}_buildings_city.json',
                                           translation_dict)
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
