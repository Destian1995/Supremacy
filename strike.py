import json
import re
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.app import App

translation_dict = {
    "Аркадия": "arkadia",
    "Селестия": "celestia",
    "Этерия": "eteria",
    "Хиперион": "giperion",
    "Халидон": "halidon",
}


def get_army_from_city(city_name):
    log_file = 'files/config/arms/all_arms.json'
    try:
        with open(log_file, 'r', encoding='utf-8') as file:
            army_data = json.load(file)
            for army_type in ['army_in_city', 'arkadia_in_city', 'celestia_in_city', 'halidon_in_city',
                              'giperion_in_city', 'eteria_in_city']:  # Проверка всех разделов
                if city_name in army_data.get(army_type, {}):
                    return army_data[army_type][city_name]  # Возвращаем данные армии города
        print(f"Армия для города '{city_name}' не найдена.")
        return None
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Файл {log_file} не найден или пуст.")
        return None
    except Exception as e:
        print(f"Произошла ошибка при загрузке армии из города '{city_name}': {e}")
        return None


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


def read_infrastructure(city_name, path_to_infrastructure):
    try:
        with open(path_to_infrastructure, 'r', encoding='utf-8') as file:
            infrastructure_data = json.load(file)

        # Ищем данные о зданиях для указанного города
        if city_name in infrastructure_data:
            city_data = infrastructure_data[city_name].get('Здания', {})
            city_buildings = {
                'Больница': city_data.get('Больница', 0),
                'Фабрика': city_data.get('Фабрика', 0)
            }
            return city_buildings
        else:
            print(f"Город '{city_name}' не найден в данных инфраструктуры.")
            return {'Больница': 0, 'Фабрика': 0}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Ошибка при чтении или загрузке данных инфраструктуры: {e}")
        return {'Больница': 0, 'Фабрика': 0}
    except Exception as e:
        print(f"Произошла ошибка при обработке инфраструктуры для города '{city_name}': {e}")
        return {'Больница': 0, 'Фабрика': 0}



def show_damage_info(damage_info, destroyed_units_count):
    content = BoxLayout(orientation='vertical')
    message = f"Информация об уроне по юнитам:\n\n"
    for unit_info in damage_info:
        if unit_info['destroyed']:
            message += f"{unit_info['unit_name']} уничтожен.\n"
        else:
            message += f"{unit_info['unit_name']} осталось единиц: {unit_info['remaining_units']}\n"

    # Добавим количество уничтоженных юнитов
    message += f"Общее количество уничтоженных юнитов: {destroyed_units_count}\n"

    label = Label(text=message, size_hint_y=None, height=400)
    close_button = Button(text="Закрыть", size_hint_y=None, height=50)
    close_button.bind(on_release=lambda instance: popup.dismiss())

    content.add_widget(label)
    content.add_widget(close_button)

    popup = Popup(title="Результат удара", content=content, size_hint=(0.7, 0.7))
    popup.open()


def close_all_open_popups():
    # Закрывает все открытые окна
    for popup in App.get_running_app().root_window.children:
        if isinstance(popup, Popup):
            popup.dismiss()


def strike_to_city(city_name, weapon_characteristics, db_connection):
    """
    Наносит удар по городу с использованием характеристик оружия.
    """
    cursor = db_connection.cursor()

    # Получаем данные об армии города (юниты и их количество)
    cursor.execute('''
        SELECT unit_name, unit_count
        FROM garrisons
        WHERE city_id = ?
    ''', (city_name,))
    army_units = cursor.fetchall()

    if not army_units:
        print(f"Армия города '{city_name}' пуста. Урон наносится по инфраструктуре.")
        strike_to_infrastructure(city_name, weapon_characteristics, db_connection)
        return

    # Загружаем характеристики юнитов из таблицы units
    unit_data = {}
    for unit in army_units:
        unit_name, unit_count = unit
        cursor.execute('''
            SELECT defense, durability
            FROM units
            WHERE unit_name = ?
        ''', (unit_name,))
        result = cursor.fetchone()
        if result:
            defense, durability = result
            unit_data[unit_name] = {
                'count': unit_count,
                'defense': defense,
                'durability': durability
            }

    # Вычисляем общую силу армии (защита + живучесть) * количество юнитов
    total_strength = sum(
        (data['defense'] + data['durability']) * data['count']
        for data in unit_data.values()
    )

    # Наносим урон
    weapon_damage = weapon_characteristics['damage'] * weapon_characteristics['count']
    air_defense_coefficient = weapon_characteristics.get('koef', 1)
    effective_weapon_damage = weapon_damage * air_defense_coefficient

    print(f"Эффективный урон от оружия: {effective_weapon_damage}")
    print(f"Общая защита армии: {total_strength}")

    damage_info = []
    destroyed_units_count = 0

    for unit_name, data in unit_data.items():
        unit_count = data['count']
        unit_strength = (data['defense'] + data['durability']) * unit_count

        # Процент вклада юнита в общую силу
        unit_percent = unit_strength / total_strength
        damage_to_unit = effective_weapon_damage * unit_percent

        remaining_strength = unit_strength - damage_to_unit

        if remaining_strength <= 0:
            destroyed_units_count += unit_count
            damage_info.append({
                'unit_name': unit_name,
                'remaining_units': 0,
                'destroyed': True
            })
            cursor.execute('''
                DELETE FROM garrisons
                WHERE city_id = ? AND unit_name = ?
            ''', (city_name, unit_name))
        else:
            remaining_units = remaining_strength // (data['defense'] + data['durability'])
            destroyed_count_for_unit = unit_count - int(remaining_units)
            destroyed_units_count += destroyed_count_for_unit
            damage_info.append({
                'unit_name': unit_name,
                'remaining_units': int(remaining_units),
                'destroyed': False
            })
            cursor.execute('''
                UPDATE garrisons
                SET unit_count = ?
                WHERE city_id = ? AND unit_name = ?
            ''', (int(remaining_units), city_name, unit_name))

    db_connection.commit()

    # Если урон превышает защиту армии, наносим урон по инфраструктуре
    if effective_weapon_damage > total_strength:
        remaining_damage = effective_weapon_damage - total_strength
        strike_to_infrastructure(city_name, {'damage': remaining_damage}, db_connection)

    show_damage_info(damage_info, destroyed_units_count)


# Функция расчета урона по инфраструктуре
def strike_to_infrastructure(city_name, weapon_characteristics, db_connection):
    """
    Наносит урон по инфраструктуре города.
    """
    cursor = db_connection.cursor()

    # Получаем данные о зданиях города
    cursor.execute('''
        SELECT building_type, count
        FROM buildings
        WHERE city_name = ?
    ''', (city_name,))
    buildings = cursor.fetchall()

    if not buildings:
        print(f"В городе '{city_name}' нет зданий.")
        return

    DAMAGE_PER_BUILDING = 80000
    effective_weapon_damage = weapon_characteristics['damage']

    damage_info = {}

    for building in buildings:
        building_name, building_count = building
        potential_destroyed_buildings = min(building_count, effective_weapon_damage // DAMAGE_PER_BUILDING)

        if potential_destroyed_buildings > 0:
            damage_info[building_name] = potential_destroyed_buildings
            effective_weapon_damage -= potential_destroyed_buildings * DAMAGE_PER_BUILDING

            # Обновляем количество зданий
            new_building_count = building_count - potential_destroyed_buildings
            cursor.execute('''
                UPDATE buildings
                SET count = ?
                WHERE city_name = ? AND building_type = ?
            ''', (new_building_count, city_name, building_name))

    db_connection.commit()

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
