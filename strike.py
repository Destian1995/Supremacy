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


def strike_to_city(city_name, weapon_characteristics, path_to_army):
    print('weapon_stats', weapon_characteristics)

    try:
        with open(path_to_army, 'r', encoding='utf-8') as file:
            army_data = json.load(file)
    except Exception as e:
        print(f"Ошибка при загрузке данных армии из файла: {e}")
        return

    city_data = army_data.get(city_name)
    if not city_data:
        print(f"Город '{city_name}' не найден.")
        return

    army_units = []
    for city in city_data:
        army_units.extend(city.get('units', []))

    if not army_units:
        print(f"Армия города '{city_name}' не содержит юнитов.")
        return

    # Вычисление коэффициентов и процентов вклада для каждого юнита
    unit_koefs = {}
    total_health = 0
    total_defense = 0
    total_units = 0

    for unit in army_units:
        unit_health = unit['units_stats']['Живучесть']
        unit_defense = unit['units_stats']['Защита']
        unit_count = unit['unit_count']

        # Коэффициент для юнита: (Живучесть + Защита) / Количество юнитов
        unit_koefs[unit['unit_name']] = (unit_health + unit_defense) / unit_count
        total_health += unit_health * unit_count
        total_defense += unit_defense * unit_count
        total_units += unit_count

    # Рассчитываем процент вклада каждого юнита в общую силу
    unit_percent_contributions = {}
    total_strength = total_health + total_defense
    for unit in army_units:
        unit_health = unit['units_stats']['Живучесть']
        unit_defense = unit['units_stats']['Защита']
        unit_count = unit['unit_count']

        # Процент вклада юнита в общую силу
        unit_strength = (unit_health + unit_defense) * unit_count
        unit_percent_contributions[unit['unit_name']] = unit_strength / total_strength
        print(unit_percent_contributions)

    print('Общая защита: ', total_strength)
    # Наносим урон
    weapon_damage = weapon_characteristics.get('all_damage', 0)
    air_defense_coefficient = weapon_characteristics.get('koef', 1)
    effective_weapon_damage = weapon_damage * air_defense_coefficient

    print(f"До удара: Армия города '{city_name}' содержит {len(army_units)} юнитов.")
    print(f"Эффективный урон от оружия: {effective_weapon_damage}")

    damage_info = []
    surviving_units = []
    destroyed_units_count = 0

    # Наносим урон по объединенным характеристикам
    total_damage = total_strength - effective_weapon_damage
    print('Осталось защиты:', total_damage)

    # Наносим урон по каждому юниту отдельно
    for unit in army_units:
        unit_health = unit['units_stats']['Живучесть']
        unit_defense = unit['units_stats']['Защита']
        unit_count = unit['unit_count']
        unit_koef = unit_koefs.get(unit['unit_name'])
        unit_percent = unit_percent_contributions.get(unit['unit_name'])

        if not unit_koef or not unit_percent:
            print(f"Нет коэффициента или процента для юнита {unit['unit_name']}")
            continue

        # Сохраняем начальное количество юнитов
        initial_unit_count = unit_count

        # Распределяем урон пропорционально проценту вклада юнита в общую силу
        damage_per_unit = effective_weapon_damage * unit_percent  # Распределяем урон по юнитам
        remaining_strength = (unit_health + unit_defense) * unit_count - damage_per_unit

        # Проверяем, уничтожен ли юнит
        if remaining_strength <= 0:
            destroyed_units_count += initial_unit_count  # Добавляем количество уничтоженных юнитов
            unit_info = {
                'unit_name': unit['unit_name'],
                'remaining_units': 0,
                'destroyed': True
            }
            print(f"Юнит {unit['unit_name']} уничтожен.")
        else:
            remaining_units = remaining_strength // (unit_health + unit_defense)  # Пересчитываем остаток
            destroyed_count_for_unit = initial_unit_count - int(remaining_units)
            destroyed_units_count += destroyed_count_for_unit  # Добавляем количество уничтоженных юнитов для этого типа
            unit_info = {
                'unit_name': unit['unit_name'],
                'remaining_units': remaining_units,
                'destroyed': False
            }
            unit['unit_count'] = int(remaining_units)  # Обновляем количество оставшихся юнитов
            surviving_units.append(unit)

        damage_info.append(unit_info)
    fraction = get_faction_of_city(city_name)
    path_to_buildings = transform_filename(f'files/config/buildings_in_city/{fraction}_buildings_city.json',
                                           translation_dict)
    print('100 * effective_weapon_damage//total_strength', 100 * effective_weapon_damage//total_strength)
    f_damage = 100 * effective_weapon_damage//total_strength
    if 5 < f_damage:
        effective_weapon_damage = effective_weapon_damage//f_damage*5
        strike_to_infrastructure(city_name, path_to_buildings, effective_weapon_damage)

    # Обновляем данные армии
    city_data[0]['units'] = surviving_units
    # Сохраняем обновленную армию в исходный файл (например, в giperion_in_city.json)
    path_to_save = transform_filename(path_to_army, translation_dict)  # Преобразуем название города для имени файла

    with open(path_to_save, 'w', encoding='utf-8') as file:
        json.dump(army_data, file, indent=4)
        print('Обновленная армия сохранена в ', path_to_save)

    show_damage_info(damage_info, destroyed_units_count)


# Функция расчета урона по инфраструктуре
def strike_to_infrastructure(city_name, path_to_buildings, effective_weapon_damage):
    print('Начинаем расчет урона по инфраструктуре')

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
    print('Урон остаточный:', effective_weapon_damage)
    # Константа для урона, необходимого для разрушения одного здания
    DAMAGE_PER_BUILDING = 1498500

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
