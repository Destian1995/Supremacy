import json
import os
import re
import shutil

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from collections import defaultdict
from ast import literal_eval
import fight

arkadia_file_path = "files/config/manage_ii/arkadia_in_city.json"
celestia_file_path = "files/config/manage_ii/celestia_in_city.json"
eteria_file_path = "files/config/manage_ii/eteria_in_city.json"
giperion_file_path = "files/config/manage_ii/giperion_in_city.json"
halidon_file_path = "files/config/manage_ii/halidon_in_city.json"
all_arms_file_path = "files/config/arms/all_arms.json"

translation_dict = {
    "Аркадия": "arkadia",
    "Селестия": "celestia",
    "Этерия": "eteria",
    "Хиперион": "giperion",
    "Халидон": "halidon",
}


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


def backup_files():
    # Определяем путь к исходным и резервным файлам
    backup_dir = 'files/config/backup'
    city_file_path = 'files/config/city.json'
    diplomaties_file_path = 'files/config/status/diplomaties.json'

    # Проверяем, существует ли директория для резервных копий, если нет - создаем её
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Определяем пути для резервных копий
    city_backup_path = os.path.join(backup_dir, 'city_backup.json')
    diplomaties_backup_path = os.path.join(backup_dir, 'diplomaties_backup.json')

    # Копируем файлы в каталог backup
    shutil.copy(city_file_path, city_backup_path)
    shutil.copy(diplomaties_file_path, diplomaties_backup_path)

    print("Резервные копии файлов сохранены в:", backup_dir)


def merge_army_and_ii_files():
    # Список всех файлов, которые нужно объединить
    file_paths = [
        arkadia_file_path,
        celestia_file_path,
        eteria_file_path,
        giperion_file_path,
        halidon_file_path
    ]

    # Инициализация словаря для хранения объединенных данных
    merged_data = {}

    # Проходим по каждому файлу и загружаем данные
    for file_path in file_paths:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                    # Извлекаем название фракции (имя файла без расширения) для организации данных
                    faction_name = os.path.splitext(os.path.basename(file_path))[0]
                    merged_data[faction_name] = data
                except json.JSONDecodeError:
                    print(f"Файл {file_path} пустой или поврежден.")
        else:
            print(f"Файл {file_path} не найден.")

    # Сохраняем объединенные данные в all_arms.json
    with open(all_arms_file_path, "w", encoding="utf-8") as all_arms_file:
        json.dump(merged_data, all_arms_file, ensure_ascii=False, indent=4)
        print(f"Данные успешно объединены и сохранены в {all_arms_file_path}.")


def transform_filename(file_path):
    # Разбиваем путь на части
    path_parts = file_path.split('/')

    # Преобразуем название города в английский
    for i, part in enumerate(path_parts):
        # Проверяем, если часть пути содержит русское название, заменяем его на английское
        for ru_name, en_name in translation_dict.items():  # Исправлено: используем items()
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)

    # Собираем путь обратно
    return '/'.join(path_parts)


class FortressInfoPopup(Popup):
    def __init__(self, kingdom, city_coords, player_fraction, **kwargs):
        super(FortressInfoPopup, self).__init__(**kwargs)
        self.fraction = kingdom
        self.city_name = ''
        self.city_coords = city_coords
        self.size_hint = (0.8, 0.8)
        self.player_fraction = player_fraction
        self.file_path2 = None
        self.file_path1 = None
        self.garrison = transform_filename(f'files/config/manage_ii/{self.player_fraction}_in_city.json')
        print('Путь garrison', self.garrison)

        # Загрузка данных о городах
        with open('files/config/cities.json', 'r', encoding='utf-8') as file:
            cities_data = json.load(file)["cities"]
            for coords, city_name in cities_data.items():
                try:
                    if literal_eval(coords) == self.city_coords:
                        self.city_name = city_name
                        break
                except Exception as e:
                    print(f"Ошибка при разборе координат: {e}")

        self.title = f"Информация о поселении {self.city_name}"
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        columns_layout = BoxLayout(orientation='horizontal', padding=9, spacing=20)

        troops_column = BoxLayout(orientation='vertical', spacing=10)
        troops_column.add_widget(Label(text="Гарнизон", font_size='20sp', bold=True, size_hint_y=None, height=30))

        self.attacking_units_list = ScrollView(size_hint=(1, 1))
        self.attacking_units_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.attacking_units_box.bind(minimum_height=self.attacking_units_box.setter('height'))
        self.attacking_units_list.add_widget(self.attacking_units_box)
        troops_column.add_widget(self.attacking_units_list)

        columns_layout.add_widget(troops_column)

        buildings_column = BoxLayout(orientation='vertical', spacing=10)
        buildings_column.add_widget(Label(text="Здания", font_size='20sp', bold=True, size_hint_y=None, height=30))

        self.buildings_list = ScrollView(size_hint=(1, 1))
        self.buildings_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.buildings_box.bind(minimum_height=self.buildings_box.setter('height'))
        self.buildings_list.add_widget(self.buildings_box)
        buildings_column.add_widget(self.buildings_list)

        columns_layout.add_widget(buildings_column)
        main_layout.add_widget(columns_layout)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        send_troops_button = Button(text="Ввести войска")
        send_troops_button.bind(on_press=self.introduce_troops)

        strike_weapon_button = Button(text="Нанести удар ДБ оружием")
        strike_weapon_button.bind(on_press=self.strike_with_dbs)

        button_layout.add_widget(send_troops_button)
        button_layout.add_widget(strike_weapon_button)
        main_layout.add_widget(button_layout)

        close_button = Button(text="Закрыть", size_hint_y=None, height=50)
        close_button.bind(on_press=self.dismiss)
        main_layout.add_widget(close_button)

        self.content = main_layout
        self.load_troops(kingdom, self.city_coords)
        self.load_buildings()

    def load_troops(self, kingdom, city_coords):
        # Вызываем функцию
        merge_army_and_ii_files()
        log_file = 'files/config/arms/all_arms.json'  # Загружаем данные из объединенного файла
        attacking_units = self.get_units(log_file, self.city_name)
        for unit in attacking_units:
            unit_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=70)
            unit_image = Image(source=unit['unit_image'], size_hint=(1, 0.7))
            unit_name_label = Label(text=f"{unit['unit_name']} (кол-во: {unit['unit_count']})", size_hint_y=None,
                                    height=30)
            unit_layout.add_widget(unit_image)
            unit_layout.add_widget(unit_name_label)
            self.attacking_units_box.add_widget(unit_layout)

    def get_units(self, log_file, city_name):
        units = []
        try:
            with open(log_file, 'r', encoding='utf-8') as file:
                army_data = json.load(file)
                for army_type in ['arkadia_in_city', 'celestia_in_city', 'halidon_in_city', 'giperion_in_city',
                                  'eteria_in_city']:  # Проверка всех разделов
                    if city_name in army_data.get(army_type, {}):
                        for entry in army_data[army_type][city_name]:
                            for unit in entry.get('units', []):
                                units.append({
                                    'unit_image': unit['unit_image'],
                                    'unit_name': unit['unit_name'],
                                    'unit_count': unit['unit_count']
                                })
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Файл {log_file} не найден или пуст.")
        except Exception as e:
            print(f"Произошла ошибка при загрузке юнитов: {e}")
        return units

    def load_buildings(self):
        buildings = self.get_buildings()
        for building in buildings:
            self.buildings_box.add_widget(Label(text=building))

    def get_buildings(self):
        """Получает количество зданий в указанном городе из JSON-файла."""
        # Формируем путь к файлу зданий фракции
        path_to_buildings = transform_filename(f'files/config/buildings_in_city/{self.fraction}_buildings_city.json')

        # Инициализируем словарь для подсчета зданий
        buildings_count = defaultdict(int)

        # Проверяем, существует ли файл
        if os.path.exists(path_to_buildings):
            try:
                with open(path_to_buildings, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                # Проверяем, есть ли информация о здании для текущего города
                if self.city_name in data:
                    buildings_info = data[self.city_name].get('Здания', {})
                    for building_type, count in buildings_info.items():
                        buildings_count[building_type] = count

            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Ошибка при чтении файла {path_to_buildings}: {e}")

        # Формируем список с информацией о зданиях
        buildings = [f"{building}: {count}" for building, count in buildings_count.items()]

        # Если зданий нет, добавляем пустую строку
        if not buildings:
            buildings.append("")

        return buildings

    def introduce_troops(self, instance):
        # Открытие окна для выбора гарнизона
        garrison_selection_popup = Popup(title="Выберите гарнизон для ввода войск",
                                         size_hint=(0.8, 0.8))

        # Создание макета для выбора гарнизона
        garrison_selection_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Загружаем данные гарнизонов из файла
        with open(self.garrison, 'r', encoding='utf-8') as file:
            try:
                army_data = json.load(file)
            except json.JSONDecodeError:
                print("Файл army_in_city.json пустой или поврежден, загружаем пустые данные.")
                army_data = {}

        # Отображение гарнизонов с информацией о войсках
        for city_name, entries in army_data.items():
            for entry in entries:
                coordinates = entry.get("coordinates", "")
                units_info = "\n".join(
                    [f"{unit['unit_name']} (Кол-во: {unit['unit_count']})" for unit in entry.get("units", [])]
                )  # Информация о каждом типе войск

                # Создаем кнопку с именем гарнизона, координатами и составом войск
                garrison_button = Button(
                    text=f"{city_name} - Войска:\n{units_info}",
                    size_hint_y=None,
                    height=100
                )

                # Привязываем действие к кнопке, чтобы при нажатии вызвать метод передачи войск
                garrison_button.bind(
                    on_press=lambda btn, name=city_name, coords=coordinates: self.choose_garrison(name, coords,
                                                                                                  garrison_selection_popup)
                )

                # Добавляем кнопку в макет
                garrison_selection_layout.add_widget(garrison_button)

        # Кнопка для закрытия окна
        close_button = Button(text="Закрыть", size_hint_y=None, height=50)
        close_button.bind(on_press=garrison_selection_popup.dismiss)
        garrison_selection_layout.add_widget(close_button)

        # Устанавливаем содержимое окна и открываем его
        garrison_selection_popup.content = garrison_selection_layout
        garrison_selection_popup.open()

    def check_city_attack(self):
        fractions = get_faction_of_city(self.city_name)
        flag_path = f'files/config/attack_in_city/{transform_filename(fractions)}_check.txt'
        print('flag_path', flag_path)
        with open(flag_path, 'r',
                  encoding='utf-8') as file:
            status = file.read()
            print('status', status)
            if status == 'True':
                return True
            elif status == 'False':
                return False

    def choose_garrison(self, source_city_name, coordinates, garrison_selection_popup):
        if self.check_city_attack():
            backup_files()  # Делаем бэкап данных
            # Получаем фракции источника и назначения
            source_faction = get_faction_of_city(source_city_name)
            destination_faction = get_faction_of_city(self.city_name)

            # Обработка путей в зависимости от фракций
            if source_faction == self.player_fraction:
                self.file_path1 = self.garrison
                self.file_path2 = transform_filename(f'files/config/manage_ii/{destination_faction}_in_city.json')
            elif destination_faction == self.player_fraction:
                self.file_path1 = transform_filename(f'files/config/manage_ii/{source_faction}_in_city.json')
                self.file_path2 = self.garrison
            else:
                self.file_path1 = transform_filename(f'files/config/manage_ii/{source_faction}_in_city.json')
                self.file_path2 = transform_filename(f'files/config/manage_ii/{destination_faction}_in_city.json')

            if not source_faction:
                print(f"Фракция для города '{source_city_name}' не найдена.")
                return
            if not destination_faction:
                print(f"Фракция для города '{self.city_name}' не найдена.")
                return

            # Если фракции совпадают, объединяем войска
            if source_faction == destination_faction:
                self.update_city_data(source_city_name)
                print(f"Войска из гарнизона '{source_city_name}' объединены с гарнизоном города '{self.city_name}'.")
            else:
                # Проверяем отношения между фракциями
                relationship = self.get_relationship(source_faction, destination_faction)
                if relationship == "война":
                    print(f"Фракции '{source_faction}' и '{destination_faction}' находятся в состоянии войны.")
                    # Загружаем армии
                    attacking_army = self.get_army_from_city(source_city_name)
                    defending_army = self.get_army_from_city(self.city_name)

                    # Печать предупреждений, если одна из армий не найдена
                    if not attacking_army:
                        print(f"Атакующая армия для города '{source_city_name}' не найдена.")
                    if not defending_army:
                        print(f"Армия для города '{self.city_name}' не найдена.")

                    # Передаем данные в модуль боя независимо от наличия армий
                    fight.fight(
                        user_file_path=self.file_path1,
                        ii_file_path=self.file_path2,
                        attacking_city=source_city_name,
                        attacking_fraction=source_faction,
                        defending_fraction=destination_faction,
                        defending_city_coords=self.city_coords,  # Координаты города-защитника
                        defending_city=self.city_name,
                        defending_army=defending_army,
                        attacking_army=attacking_army
                    )
                else:
                    print(
                        f"Фракции '{source_faction}' и '{destination_faction}' находятся в состоянии '{relationship}'. Войска не могут быть введены.")

            # Закрыть всплывающее окно после выполнения выбора
            garrison_selection_popup.dismiss()
            self.dismiss()
        else:
            # Создание и отображение всплывающего окна
            layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            message = Label(text='На этом ходу уже была атака на город.')
            close_button = Button(text='ОК', size_hint=(1, 0.3))

            layout.add_widget(message)
            layout.add_widget(close_button)

            popup = Popup(title='Предупреждение',
                          content=layout,
                          size_hint=(0.6, 0.4),
                          auto_dismiss=False)

            close_button.bind(on_release=popup.dismiss)

            popup.open()
            return

    def get_relationship(self, faction1, faction2):
        try:
            with open('files/config/status/diplomaties.json', 'r', encoding='utf-8') as file:
                diplomacies = json.load(file)
            # Получаем отношения от faction1 к faction2
            relationship = diplomacies.get(faction1, {}).get("отношения", {}).get(faction2, "нейтралитет")
            return relationship
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Ошибка при загрузке diplomacies.json: {e}")
            return "нейтралитет"

    def get_army_from_city(self, city_name):
        log_file = 'files/config/arms/all_arms.json'
        try:
            with open(log_file, 'r', encoding='utf-8') as file:
                army_data = json.load(file)
                for army_type in ['arkadia_in_city', 'celestia_in_city', 'halidon_in_city', 'giperion_in_city',
                                  'eteria_in_city']:  # Проверка всех разделов
                    if city_name in army_data.get(army_type, {}):
                        for entry in army_data[army_type][city_name]:
                            return entry.get('units', [])  # Возвращаем список юнитов
            print(f"Армия для города '{city_name}' не найдена.")
            return None
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Файл {log_file} не найден или пуст.")
            return None
        except Exception as e:
            print(f"Произошла ошибка при загрузке армии из города '{city_name}': {e}")
            return None

    def update_city_data(self, source_city_name):
        try:
            with open(self.garrison, 'r+', encoding='utf-8') as file:
                army_data = json.load(file)

                # Проверка наличия данных о выбранном гарнизоне
                if source_city_name not in army_data:
                    print(f"Гарнизон '{source_city_name}' не существует в данных.")
                    return

                # Получаем войска из выбранного гарнизона
                source_units = army_data[source_city_name][0].get("units", [])

                # Добавляем войска в целевой город
                if self.city_name in army_data:
                    army_data[self.city_name][0].setdefault("units", []).extend(
                        source_units)  # Добавляем юниты в существующий список
                else:
                    army_data[self.city_name] = [{"coordinates": str(self.city_coords), "units": source_units}]

                # Удаляем данные о старом гарнизоне
                del army_data[source_city_name]

                # Записываем обновленные данные в файл
                file.seek(0)
                json.dump(army_data, file, ensure_ascii=False, indent=4)
                file.truncate()  # Удаляем старые данные, если новые короче
        except KeyError as e:
            print(f"Ошибка при обновлении данных о городе: '{e}' не существует в данных.")
        except Exception as e:
            print(f"Ошибка при обновлении данных о городе: {e}")

    # Пример для поиска имени города по координатам
    def get_city_name_by_coordinates(self, coordinates):
        try:
            with open('files/config/cities.json', 'r', encoding='utf-8') as file:
                cities_data = json.load(file)

                for city, data in cities_data.items():
                    if data['coordinates'] == coordinates:
                        return city
        except (FileNotFoundError, json.JSONDecodeError):
            print("Ошибка при загрузке файла cities.json.")

        return None  # Если город не найден

    def strike_with_dbs(self, instance):
        path_to_army_strike = transform_filename(f'files/config/manage_ii/{self.fraction}_in_city.json')
        data = {
            "city_name": self.city_name,
            "coordinates": self.city_coords,
            "path_to_army": path_to_army_strike
        }
        with open('files/config/arms/coordinates_weapons.json', 'w', encoding='utf-8') as file:
            json.dump(data, file)
        print(f"Данные о городе '{self.city_name}' и его координатах {self.city_coords} сохранены в файл.")

        # Закрытие окна после выполнения действия
        self.dismiss()
