import sqlite3

from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.uix.scrollview import ScrollView


def merge_units(army):
    """
    Объединяет юниты одного типа в одну группу.
    :param army: Список юнитов (атакующих или обороняющихся).
    :return: Объединенный список юнитов.
    """
    merged_army = {}
    for unit in army:
        unit_name = unit['unit_name']
        if unit_name not in merged_army:
            merged_army[unit_name] = {
                "unit_name": unit['unit_name'],
                "unit_count": unit['unit_count'],
                "unit_image": unit.get('unit_image', ''),
                "units_stats": unit['units_stats']
            }
        else:
            merged_army[unit_name]['unit_count'] += unit['unit_count']
    return list(merged_army.values())

# Окно отчета боя
def show_battle_report(report_data):
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


def fight(attacking_city, defending_city, defending_army, attacking_army, attacking_fraction, defending_fraction,
          db_connection):
    """
    Основная функция боя между двумя армиями.
    """
    print('attacking_fraction:', attacking_fraction)
    print('defending_fraction:', defending_fraction)

    cursor = db_connection.cursor()
    try:
        # Проверка, что соединение с базой данных активно
        if not db_connection or not cursor:
            raise ValueError("Соединение с базой данных не установлено или курсор недоступен.")

        # SQL-запрос для выборки значения faction
        query = "SELECT faction FROM user_faction"
        cursor.execute(query)

        # Получение первого значения из результата (если оно есть)
        result = cursor.fetchone()
        user_faction = result.get('faction')

    except Exception as e:
        # Выводим подробную информацию об ошибке
        import traceback
        print(f"Ошибка при выгрузке значения faction: {e}")
        traceback.print_exc()  # Печатаем трассировку стека для диагностики
        user_faction = None

    print('-----------------------------------------------------***********--user_faction', user_faction)

    # Исправленная проверка принадлежности фракции
    if user_faction == attacking_fraction or user_faction == defending_fraction:
        user_faction = 1
    else:
        user_faction = 0
    print('-----------------------------------------------------***********--user_faction', user_faction)
    # Объединяем войска одной стороны
    attacking_army = merge_units(attacking_army)
    defending_army = merge_units(defending_army)
    # Сохраняем начальные значения ДО боя
    for unit in attacking_army:
        unit['initial_count'] = unit['unit_count']
    for unit in defending_army:
        unit['initial_count'] = unit['unit_count']

    # Вспомогательная функция для определения приоритета юнита
    def get_unit_priority(unit):
        stats = unit['units_stats']
        attack = int(stats.get('Урон', 0))
        defense = int(stats.get('Защита', 0))
        health = int(stats.get('Живучесть', 0))

        # Приоритет: если урон больше остальных параметров
        if attack > defense and attack > health:
            return 1  # Высший приоритет
        return 0  # Низший приоритет

    # Сортируем армии по классу и внутри класса по приоритету
    attacking_army.sort(
        key=lambda x: (int(x['units_stats']['Класс юнита']), -get_unit_priority(x))
    )
    defending_army.sort(
        key=lambda x: (int(x['units_stats']['Класс юнита']), -get_unit_priority(x))
    )

    # Бой между юнитами
    for attacking_unit in attacking_army:
        for defending_unit in defending_army:
            if int(attacking_unit['unit_count']) > 0 and int(defending_unit['unit_count']) > 0:
                attacking_unit, defending_unit = battle_units(attacking_unit, defending_unit, defending_city, user_faction)

    # Генерация отчета
    report_data = generate_battle_report(attacking_army, defending_army)

    # Обновление гарнизонов в базе данных
    update_garrisons_after_battle(
        winner='attacking' if any(int(u['unit_count']) > 0 for u in attacking_army) else 'defending',
        attacking_city=attacking_city,
        defending_city=defending_city,
        attacking_army=attacking_army,
        defending_army=defending_army,
        attacking_fraction=attacking_fraction,
        defending_fraction=defending_fraction,
        cursor=db_connection.cursor()
    )

    # Показываем отчет
    if user_faction == 1:
        show_battle_report(report_data)


def generate_battle_report(attacking_army, defending_army):
    """
    Генерирует отчет о бое.
    :param attacking_army: Данные об атакующей армии.
    :param defending_army: Данные об обороняющейся армии.
    :return: Отчет о бое (список словарей).
    """
    report_data = []

    def process_army(army, side):
        for unit in army:
            initial_count = unit.get('initial_count', 0)
            final_count = unit['unit_count']
            losses = initial_count - final_count
            report_data.append({
                'unit_name': unit['unit_name'],
                'initial_count': initial_count,
                'final_count': final_count,
                'losses': losses,
                'side': side
            })

    # Обработка армий
    process_army(attacking_army, 'attacking')
    process_army(defending_army, 'defending')

    return report_data


def calculate_army_power(army):
    """
    Рассчитывает общую силу армии.
    :param army: Список юнитов в армии.
    :return: Общая сила армии (float).
    """
    total_power = 0
    for unit in army:
        unit_damage = unit['units_stats']['Урон']
        unit_count = unit['unit_count']
        total_power += unit_damage * unit_count
    return total_power


def calculate_unit_power(unit, is_attacking):
    """
    Рассчитывает силу одного юнита.
    :param unit: Данные о юните (словарь с характеристиками).
    :param is_attacking: True, если юнит атакующий; False, если защитный.
    :return: Сила юнита (float).
    """
    class_coefficients = {
        '1': 1.3,
        '2': 1.7,
        '3': 2.0,
        '4': 3.0
    }

    unit_class = unit['units_stats']['Класс юнита']
    coefficient = class_coefficients.get(unit_class, 1.0)

    if is_attacking:
        # Для атакующих юнитов
        attack = unit['units_stats']['Урон']
        return attack * coefficient
    else:
        # Для защитных юнитов
        durability = unit['units_stats']['Живучесть']
        defense = unit['units_stats']['Защита']
        return durability + defense


def battle_units(attacking_unit, defending_unit, city, user_faction):
    """
    Осуществляет бой между двумя юнитами.
    :param city:
    :param attacking_unit: Атакующий юнит.
    :param defending_unit: Защитный юнит.
    :return: Обновленные данные об атакующем и защитном юнитах после боя.
    """
    # Расчет силы атакующего юнита
    attack_points = calculate_unit_power(attacking_unit, is_attacking=True)
    total_attack_power = attack_points * attacking_unit['unit_count']

    # Расчет силы защитного юнита
    defense_points = calculate_unit_power(defending_unit, is_attacking=False)
    total_defense_power = defense_points * defending_unit['unit_count']

    damage_to_infrastructure(total_attack_power, city, user_faction)

    # Определение победителя раунда
    if total_attack_power > total_defense_power:
        # Атакующий побеждает
        remaining_power = total_attack_power - total_defense_power
        remaining_attackers = max(int(remaining_power / attack_points), 0)
        remaining_defenders = 0
    else:
        # Защитный побеждает
        remaining_power = total_defense_power - total_attack_power
        remaining_defenders = max(int(remaining_power / defense_points), 0)
        remaining_attackers = 0

    # Обновляем количество юнитов
    attacking_unit['unit_count'] = remaining_attackers
    defending_unit['unit_count'] = remaining_defenders

    return attacking_unit, defending_unit

def update_garrisons_after_battle(winner, attacking_city, defending_city,
                                  attacking_army, defending_army,
                                  attacking_fraction, defending_fraction, cursor):
    """
    Обновляет гарнизоны после боя.
    """
    try:
        with cursor.connection:
            if winner == 'attacking':
                # Если победила атакующая сторона
                # Удаляем гарнизон обороняющейся стороны
                cursor.execute("""
                    DELETE FROM garrisons WHERE city_id = ?
                """, (defending_city,))

                # Перемещаем оставшиеся атакующие войска в захваченный город
                for unit in attacking_army:
                    if unit['unit_count'] > 0:
                        cursor.execute("""
                            INSERT INTO garrisons (city_id, unit_name, unit_count, unit_image)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(city_id, unit_name) DO UPDATE SET
                            unit_count = excluded.unit_count,
                            unit_image = excluded.unit_image
                        """, (
                            defending_city,
                            unit['unit_name'],
                            unit['unit_count'],
                            unit.get('unit_image', '')
                        ))

                # Обновляем принадлежность города
                cursor.execute("""
                    UPDATE city SET kingdom = ? WHERE fortress_name = ?
                """, (attacking_fraction, defending_city))
                # Обновляем принадлежность города
                cursor.execute("""
                    UPDATE cities SET faction = ? WHERE name = ?
                """, (attacking_fraction, defending_city))
                # Уцелевшие здания переходят под контроль захватчика
                cursor.execute("""
                    UPDATE buildings
                    SET faction = ?
                    WHERE city_name = ?
                """, (attacking_fraction, defending_city))

            else:
                # Если победила обороняющаяся сторона
                # Восстанавливаем оставшийся гарнизон обороняющейся стороны
                for unit in defending_army:
                    if unit['unit_count'] > 0:
                        cursor.execute("""
                            INSERT INTO garrisons (city_id, unit_name, unit_count, unit_image)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(city_id, unit_name) DO UPDATE SET
                            unit_count = excluded.unit_count,
                            unit_image = excluded.unit_image
                        """, (
                            defending_city,
                            unit['unit_name'],
                            unit['unit_count'],
                            unit.get('unit_image', '')
                        ))

            # Обновляем гарнизон атакующего города
            original_counts = {}
            # Сначала получаем текущие количества юнитов в атакующем городе
            cursor.execute("""
                SELECT unit_name, unit_count FROM garrisons WHERE city_id = ?
            """, (attacking_city,))
            for row in cursor.fetchall():
                original_counts[row['unit_name']] = row['unit_count']

            for unit in attacking_army:
                remaining_in_source = original_counts.get(unit['unit_name'], 0) - unit['initial_count']
                if remaining_in_source > 0:
                    # Обновляем количество, если остались юниты
                    cursor.execute("""
                        UPDATE garrisons 
                        SET unit_count = ? 
                        WHERE city_id = ? AND unit_name = ?
                    """, (remaining_in_source, attacking_city, unit['unit_name']))
                else:
                    # Удаляем юнит полностью, если не осталось
                    cursor.execute("""
                        DELETE FROM garrisons 
                        WHERE city_id = ? AND unit_name = ?
                    """, (attacking_city, unit['unit_name']))

    except sqlite3.Error as e:
        print(f"Ошибка при обновлении гарнизонов: {e}")




#------------------------------------

def damage_to_infrastructure(all_damage, city_name, user_faction):
    """
    Вычисляет урон по инфраструктуре города и обновляет данные в базе данных.

    :param all_damage: Общий урон, который нужно нанести.
    :param city_name: Название города, по которому наносится урон.
    """
    global conn, damage_info
    print('Начинаем расчет урона по инфраструктуре')

    # Константа для урона, необходимого для разрушения одного здания
    DAMAGE_PER_BUILDING = 45900

    # Подключение к базе данных
    try:
        conn = sqlite3.connect('game_data.db')  # Замените 'game_data.db' на путь к вашей БД
        cursor = conn.cursor()

        # Загрузка данных о зданиях для указанного города
        cursor.execute('''
            SELECT building_type, count 
            FROM buildings 
            WHERE city_name = ? AND count > 0
        ''', (city_name,))
        rows = cursor.fetchall()

        # Преобразование данных в словарь
        city_data = {}
        for row in rows:
            building_type, count = row
            city_data[building_type] = count

        if not city_data:
            print(f"Город '{city_name}' не найден в базе данных или в нем нет зданий.")
            return

        print(f"Данные инфраструктуры до удара: {city_data}")

        effective_weapon_damage = all_damage
        print(f"Эффективный урон по инфраструктуре: {effective_weapon_damage}")

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
        priority_buildings = ['Больница', 'Фабрика']  # Приоритетные типы зданий для уничтожения

        for building in priority_buildings:
            if building in city_data and city_data[building] > 0:
                count = city_data[building]
                if potential_destroyed_buildings >= count:
                    # Уничтожаем все здания этого типа
                    damage_info[building] = count
                    city_data[building] = 0
                    potential_destroyed_buildings -= count

                    # Обновляем данные в базе данных
                    cursor.execute('''
                        UPDATE buildings 
                        SET count = 0 
                        WHERE city_name = ? AND building_type = ?
                    ''', (city_name, building))
                else:
                    # Уничтожаем часть зданий
                    damage_info[building] = potential_destroyed_buildings
                    city_data[building] -= potential_destroyed_buildings

                    # Обновляем данные в базе данных
                    cursor.execute('''
                        UPDATE buildings 
                        SET count = count - ? 
                        WHERE city_name = ? AND building_type = ?
                    ''', (potential_destroyed_buildings, city_name, building))

                    potential_destroyed_buildings = 0

                if potential_destroyed_buildings == 0:
                    break

        print(f"Данные инфраструктуры после удара: {city_data}")

        # Сохраняем изменения в базе данных
        conn.commit()
        print('Обновленная инфраструктура сохранена.')

    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        conn.close()

    if user_faction == 1:
        # Показать информацию об уроне
        show_damage_info_infrastructure(damage_info)


def show_damage_info_infrastructure(damage_info):
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.popup import Popup

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