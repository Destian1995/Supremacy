from kivy.graphics import Color, Ellipse, Rectangle
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

from game_process import GameScreen
from ui import *
import os
import json
import shutil
# Размеры окна
screen_width, screen_height = 1200, 800


def load_kingdom_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def restore_from_backup():
    # Определяем путь к исходным и резервным файлам
    backup_dir = 'files/config/backup'
    city_file_path = 'files/config/city.json'
    diplomaties_file_path = 'files/config/status/diplomaties.json'

    # Определяем пути для резервных копий
    city_backup_path = os.path.join(backup_dir, 'city_backup.json')
    diplomaties_backup_path = os.path.join(backup_dir, 'diplomaties_backup.json')

    # Проверяем, существуют ли резервные копии
    if os.path.exists(city_backup_path) and os.path.exists(diplomaties_backup_path):
        # Копируем файлы из резервной копии обратно в исходные файлы
        shutil.copy(city_backup_path, city_file_path)
        shutil.copy(diplomaties_backup_path, diplomaties_file_path)
        print("Файлы восстановлены из бэкапа.")
    else:
        print("Резервные копии не найдены. Восстановление невозможно.")


def clear_temp_files():
    temp_files = ['files/config/arms/arms.json',
                  'files/config/resources/cash.json',
                  'files/config/arms/weapons.json',
                  'files/config/arms/coordinates_weapons.json',
                  'files/config/buildings_in_city/arkadia_buildings_city.json',
                  'files/config/buildings_in_city/celestia_buildings_city.json',
                  'files/config/buildings_in_city/eteria_buildings_city.json',
                  #'files/config/buildings_in_city/giperion_buildings_city.json',
                  'files/config/buildings_in_city/halidon_buildings_city.json',]
    for file in temp_files:
        with open(file, 'w', encoding='utf-8') as f:
            f.write('')  # Записываем пустую строку, чтобы очистить файл


class HallOfFameWidget(FloatLayout):
    def __init__(self, **kwargs):
        super(HallOfFameWidget, self).__init__(**kwargs)
        self.add_widget(Image(source='files/menu.jpg', allow_stretch=True, keep_ratio=False))  # Фон зала славы

        # Заголовок
        title = Label(text="[b][color=000000]Зал славы[/color][/b]", font_size='40sp', markup=True,
                      size_hint=(1, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.9})
        self.add_widget(title)

        # Поле для вывода лучших результатов
        self.results_label = Label(text=self.get_top_scores(), font_size='30sp', markup=True, halign="center",
                                   size_hint=(0.8, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5}, color=(0, 0, 0, 5))
        self.add_widget(self.results_label)

        # Кнопка "Назад"
        btn_back = Button(text="Назад", size_hint=(0.3, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.1},
                          background_normal='', background_color=(0, 0, 0, 1))
        btn_back.bind(on_press=self.go_back)
        self.add_widget(btn_back)

    def get_top_scores(self):
        # Заглушка для топ-10 лучших результатов, можно заменить на реальную логику
        top_scores = [
            "1. Игрок1 - 9999 очков",
            "2. Игрок2 - 9500 очков",
            "3. Игрок3 - 9200 очков",
            "4. Игрок4 - 9000 очков",
            "5. Игрок5 - 8900 очков",
            "6. Игрок6 - 8700 очков",
            "7. Игрок7 - 8500 очков",
            "8. Игрок8 - 8300 очков",
            "9. Игрок9 - 8000 очков",
            "10. Игрок10 - 7800 очков",
        ]
        return "\n".join(top_scores)

    def go_back(self, instance):
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(MenuWidget())


class MapWidget(Widget):
    def __init__(self, selected_kingdom=None, player_kingdom=None, **kwargs):
        super(MapWidget, self).__init__(**kwargs)
        self.touch_start = None  # Стартовая позиция касания
        self.fortress_rectangles = []  # Список для хранения крепостей
        self.current_player_kingdom = player_kingdom  # Текущее королевство игрока
        self.map_pos = self.map_positions_start() # Позиция карты
        print(self.current_player_kingdom)
        # Отрисовка карты
        with self.canvas:
            self.map_image = Rectangle(source='files/map/map.png', pos=self.map_pos, size=(screen_width, screen_height))

        # Отрисовка всех крепостей
        self.draw_fortresses()

    def map_positions_start(self):
        if self.current_player_kingdom == 'Хиперион':
            return [-200, -100]
        elif self.current_player_kingdom == 'Аркадия':
            return [0, -240]
        elif self.current_player_kingdom == 'Селестия':
            return [0, 0]
        elif self.current_player_kingdom == 'Этерия':
            return [-400, -210]
        elif self.current_player_kingdom == 'Халидон':
            return [-360, 0]


    def draw_fortresses(self):
        self.fortress_rectangles.clear()
        self.canvas.clear()

        # Загружаем данные о княжествах
        file_path = os.path.join('files', 'config', 'city.json')
        data = load_kingdom_data(file_path)

        # Отрисовываем фон карты
        with self.canvas:
            self.map_image = Rectangle(source='files/map/map.png', pos=self.map_pos, size=(screen_width, screen_height))

            # Отрисовываем крепости всех княжеств
            for kingdom_name, kingdom_data in data["kingdoms"].items():
                fortress_color = kingdom_data["color"]

                for fortress in kingdom_data["fortresses"]:
                    fort_x, fort_y = fortress["coordinates"]
                    fort_x += self.map_pos[0] - 10
                    fort_y += self.map_pos[1] - 10

                    # Сохраняем прямоугольник и владельца для проверки касания
                    fort_rect = (fort_x, fort_y, 20, 20)
                    self.fortress_rectangles.append((fort_rect, fortress, kingdom_name))

                    # Устанавливаем цвет и рисуем крепость
                    Color(*fortress_color)
                    Ellipse(pos=(fort_x + 10, fort_y + 10), size=(20, 20))

    def check_fortress_click(self, touch):
        # Проверяем, была ли нажата крепость
        for fort_rect, fortress_data, owner in self.fortress_rectangles:
            if (fort_rect[0] <= touch.x <= fort_rect[0] + fort_rect[2] and
                    fort_rect[1] <= touch.y <= fort_rect[1] + fort_rect[3]):
                # Получаем координаты крепости из словаря fortress_data
                fortress_coords = fortress_data["coordinates"]  # Предполагаем, что это ключ "coordinates"
                popup = FortressInfoPopup(kingdom=owner, city_coords=fortress_coords, player_fraction=self.current_player_kingdom)
                popup.open()

                print(f"Крепость {fortress_coords} принадлежит {'вашему' if owner == self.current_player_kingdom else 'чужому'} королевству!")

    def on_touch_down(self, touch):
        # Запоминаем начальную точку касания
        if touch.is_mouse_scrolling:
            return  # Игнорируем скроллинг
        self.touch_start = touch.pos

    def on_touch_move(self, touch):
        # Двигаем карту при перемещении касания
        if self.touch_start:
            dx = touch.x - self.touch_start[0]
            dy = touch.y - self.touch_start[1]
            self.touch_start = touch.pos  # Обновляем точку касания

            # Обновляем позицию карты
            self.map_pos[0] += dx
            self.map_pos[1] += dy
            self.update_map_position()

    def update_map_position(self):
        # Обновляем позицию изображения карты
        self.map_image.pos = self.map_pos

        # Обновляем позиции крепостей
        for index, (fort_rect, fortress_data, owner) in enumerate(self.fortress_rectangles):
            fort_x, fort_y = fortress_data["coordinates"]  # Извлекаем координаты
            fort_x += self.map_pos[0] - 10  # Смещаем по X
            fort_y += self.map_pos[1] - 10  # Смещаем по Y
            self.fortress_rectangles[index] = ((fort_x, fort_y, 20, 20), fortress_data, owner)  # Обновляем прямоугольник

        # Очищаем canvas и снова рисуем карту и крепости
        self.canvas.clear()
        self.draw_map()  # Вызываем отрисовку карты
        self.draw_fortresses()

    def on_touch_up(self, touch):
        # Обрабатываем отпускание касания
        if touch.is_mouse_scrolling:
            return  # Игнорируем скроллинг
        self.check_fortress_click(touch)

    def draw_map(self):
        with self.canvas:
            Rectangle(source='files/map/map.png', pos=self.map_pos, size=(screen_width, screen_height))


# Меню
class MenuWidget(FloatLayout):
    def __init__(self, **kwargs):
        super(MenuWidget, self).__init__(**kwargs)
        self.add_widget(Image(source='files/menu.jpg', allow_stretch=True, keep_ratio=False))  # Фон меню

        # Заголовок
        title = Label(text="[b][color=000000]Превосходство[/color][/b]", font_size='40sp', markup=True,
                      size_hint=(1, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.9})
        self.add_widget(title)

        # Кнопки
        btn_start_game = Button(text="Старт новой игры", size_hint=(0.5, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.7},
                                background_normal='', background_color=(0, 0, 0, 1))
        btn_start_game.bind(on_press=self.start_game)

        btn_load_game = Button(text="Загрузка ранее сохраненной", size_hint=(0.5, 0.1),
                               pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_normal='', background_color=(0, 0, 0, 1))
        btn_load_game.bind(on_press=self.load_game)

        btn_hall_of_fame = Button(text="Зал славы", size_hint=(0.5, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.3},
                                  background_normal='', background_color=(0, 0, 0, 1))
        btn_hall_of_fame.bind(on_press=self.show_hall_of_fame)

        btn_exit = Button(text="Выход", size_hint=(0.5, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.1},
                          background_normal='', background_color=(0, 0, 0, 1))
        btn_exit.bind(on_press=self.exit_game)

        self.add_widget(btn_start_game)
        self.add_widget(btn_load_game)
        self.add_widget(btn_hall_of_fame)
        self.add_widget(btn_exit)

    def start_game(self, instance):
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(KingdomSelectionWidget())

    def load_game(self, instance):
        print("Загрузка игры...")

    def show_hall_of_fame(self, instance):
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(HallOfFameWidget())

    def exit_game(self, instance):
        App.get_running_app().stop()

# Виджет выбора княжества
class KingdomSelectionWidget(FloatLayout):
    def __init__(self, **kwargs):
        super(KingdomSelectionWidget, self).__init__(**kwargs)
        # Загрузка данных о княжествах из JSON
        with open('files/config/city.json', 'r', encoding='utf-8') as f:
            self.kingdom_data = json.load(f)["kingdoms"]

        # Фон выбора княжества с размытием
        self.add_widget(Image(source='files/menu.jpg', allow_stretch=True, keep_ratio=False))

        # Заголовок с тенью
        self.kingdom_label = Label(
            text="Выберите сторону",
            font_size='40sp',
            size_hint=(1, 0.2),
            pos_hint={'center_x': 0.5, 'center_y': 0.85},
            color=(0.2, 0.2, 0.2, 1),
            outline_color=(0, 0, 0, 1),
            outline_width=2
        )
        self.add_widget(self.kingdom_label)

        # Панель для кнопок выбора княжеств
        self.kingdom_buttons = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint=(0.4, 0.5),
            pos_hint={'center_x': 0.4, 'center_y': 0.5},
            padding=[10, 10, 10, 10]
        )

        # Создание кнопок для каждого княжества с черным текстом
        for kingdom in self.kingdom_data.keys():
            btn = Button(
                text=kingdom,
                size_hint=(1, None),
                height=50,
                background_normal='',
                background_color=(0.96, 0.89, 0.76, 1),  # Бежевый цвет кнопок
                color=(0, 0, 0, 1),  # Черный цвет текста
                border=(20, 20, 20, 20)
            )
            btn.bind(on_press=self.select_kingdom)
            # Более светлый оттенок при наведении
            btn.bind(on_enter=lambda x: setattr(btn, 'background_color', (0.98, 0.92, 0.8, 1)))
            btn.bind(on_leave=lambda x: setattr(btn, 'background_color', (0.96, 0.89, 0.76, 1)))
            self.kingdom_buttons.add_widget(btn)

        self.add_widget(self.kingdom_buttons)

        # Изображение советника
        self.advisor_image = Image(
            source='files/null.png',
            size_hint=(0.3, 0.3),
            pos_hint={'center_x': 0.75, 'center_y': 0.65}
        )
        self.add_widget(self.advisor_image)

        # Панель вкладок
        self.tabs_panel = TabbedPanel(size_hint=(0.35, 0.3), pos_hint={'center_x': 0.8, 'center_y': 0.35})

        # Вкладка с информацией о княжестве
        self.info_tab = TabbedPanelItem(text="Инфо")
        self.info_tab.background_color = (0.6, 0.8, 1, 1)  # Светло-синий фон вкладки
        self.info_tab.color = (0, 0, 0, 1)  # Черный цвет текста

        self.info_text_box = TextInput(
            text="",
            background_color=(0.96, 0.89, 0.76, 1),  # Бежевый цвет фона
            foreground_color=(0, 0, 0, 1),  # Черный цвет текста
            readonly=True,
            multiline=True,
            size_hint_y=None,
            height=150,
            padding=[10, 10, 10, 10]
        )
        self.info_tab.add_widget(self.info_text_box)
        self.tabs_panel.add_widget(self.info_tab)

        # Вкладка с городами
        self.cities_tab = TabbedPanelItem(text="Города")
        self.cities_tab.background_color = (0.6, 0.8, 1, 1)  # Светло-синий фон вкладки
        self.cities_tab.color = (0, 0, 0, 1)  # Черный цвет текста

        self.cities_text_box = TextInput(
            text="",
            background_color=(0.96, 0.89, 0.76, 1),  # Бежевый цвет фона
            foreground_color=(0, 0, 0, 1),  # Черный цвет текста
            readonly=True,
            multiline=True,
            size_hint_y=None,
            height=150,
            padding=[10, 10, 10, 10]
        )
        self.cities_tab.add_widget(self.cities_text_box)
        self.tabs_panel.add_widget(self.cities_tab)

        # Устанавливаем вкладку "Инфо" как активную
        self.tabs_panel.default_tab = self.info_tab
        self.add_widget(self.tabs_panel)

        # Стилизация кнопок вкладок
        for tab in self.tabs_panel.tab_list:
            tab.bind(on_enter=lambda x: setattr(tab, 'background_color', (0.7, 0.85, 1, 1)))  # Более яркий оттенок при наведении
            tab.bind(on_leave=lambda x: setattr(tab, 'background_color', (0.6, 0.8, 1, 1)))  # Вернуться к оригинальному цвету
            tab.size_hint_y = None
            tab.height = 50  # Высота кнопок
            tab.background_normal = ''  # Убираем стандартный фон кнопок
            tab.background_color = (0.6, 0.8, 1, 1)  # Светло-синий цвет кнопок

        # Кнопка для начала игры с черным текстом
        self.start_game_button = Button(
            text="Начать игру",
            size_hint=(0.4, None),
            height=60,
            pos_hint={'center_x': 0.8, 'center_y': 0.10},
            background_normal='',
            background_color=(0.96, 0.89, 0.76, 1),
            color=(0, 0, 0, 1),  # Черный цвет текста
            border=(20, 20, 20, 20)
        )
        self.start_game_button.bind(on_press=self.start_game)
        # Более светлый оттенок при наведении
        self.start_game_button.bind(
            on_enter=lambda x: setattr(self.start_game_button, 'background_color', (0.98, 0.92, 0.8, 1)))
        self.start_game_button.bind(
            on_leave=lambda x: setattr(self.start_game_button, 'background_color', (0.96, 0.89, 0.76, 1)))
        self.add_widget(self.start_game_button)

    def select_kingdom(self, instance):
        """Метод для обработки выбора княжества"""
        kingdom_rename = {
            "Аркадия": "arkadia",
            "Селестия": "celestia",
            "Этерия": "eteria",
            "Хиперион": "giperion",
            "Халидон": "halidon"
        }
        kingdom_name = instance.text
        kingdom_info = self.kingdom_data[kingdom_name]

        # Устанавливаем выбранное княжество в атрибут приложения
        app = App.get_running_app()
        app.selected_kingdom = kingdom_name  # Сохраняем выбранное княжество

        english_name = kingdom_rename.get(kingdom_name, kingdom_name).lower()
        advisor_image_path = f'files/sov/sov_{english_name}.jpg'
        self.advisor_image.source = advisor_image_path
        self.advisor_image.reload()

        # Обновляем текст для вкладки "Инфо"
        kingdom_info_text = self.get_kingdom_info(kingdom_name)
        self.info_text_box.text = kingdom_info_text

        # Обновляем текст для вкладки "Города"
        fortresses_info = "\n".join([f"{fort['name']}: {fort['coordinates']}" for fort in kingdom_info["fortresses"]])
        self.cities_text_box.text = f"Города:\n{fortresses_info}"

    def get_kingdom_info(self, kingdom):
        info = {
            "Аркадия": "Аркадия - северное княжество.\nЭкономика: 8\nАрмия: 9\nДипломатия: 4\n",
            "Селестия": "Селестия - юго-западное княжество.\nЭкономика: 8\nАрмия: 7\nДипломатия: 6\n",
            "Хиперион": "Хиперион - средиземная империя.\nЭкономика: 9\nАрмия: 10\nДипломатия: 2\n",
            "Халидон": "Халидон - юго-восточное княжество.\nЭкономика: 7\nАрмия: 5\nДипломатия: 9\n",
            "Этерия": "Этерия - восточное княжество.\nЭкономика: 7\nАрмия: 8\nДипломатия: 6\n"
        }
        return info.get(kingdom, "")

    def start_game(self, instance):
        app = App.get_running_app()
        selected_kingdom = app.selected_kingdom
        if selected_kingdom is None:
            print("Фракция не выбрана. Пожалуйста, выберите фракцию перед началом игры.")
            return

        # Загружаем данные из файла
        file_path = os.path.join('files', 'config', 'city.json')
        data = load_kingdom_data(file_path)

        # Получаем города и крепости для выбранного княжества
        cities = data['kingdoms'][selected_kingdom]['fortresses']
        # Очистка временных файлов
        clear_temp_files()
        # Загрузка дампа дефолтных файлов.
        restore_from_backup()
        # Передаем выбранное княжество на новый экран игры
        game_screen = GameScreen(selected_kingdom, cities)
        app.root.clear_widgets()
        app.root.add_widget(MapWidget(selected_kingdom=selected_kingdom,
                                      player_kingdom=selected_kingdom))  # Передаем выбранное княжество
        app.root.add_widget(game_screen)


# Основное приложение
class EmpireApp(App):
    def build(self):
        return MenuWidget()


class Main(App):
    def __init__(self, **kwargs):
        super(EmpireApp, self).__init__(**kwargs)# Запуск приложения
        self.selected_kingdom = None  # Инициализация атрибутаif __name__ == '__main__':
    EmpireApp().run()