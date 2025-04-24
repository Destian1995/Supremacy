import os

from kivy.animation import Animation
from kivy.app import App
from kivy.graphics import Line
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel
import random
from game_process import GameScreen
from ui import *
import ast
import logging
import sqlite3
from kivy.clock import Clock
# Размеры окна
screen_width, screen_height = 1200, 800

def save_last_clicked_city(city_name: str):
    conn = sqlite3.connect('game_data.db')
    cur = conn.cursor()
    # если строки ещё нет, вставим, иначе перепишем
    cur.execute(
        "INSERT OR REPLACE INTO last_click (id, city_name) VALUES (1, ?)",
        (city_name,)
    )
    conn.commit()
    conn.close()

def load_cities_from_db(selected_kingdom):
    """
    Функция загружает данные о городах для выбранного княжества из таблицы city.

    :param selected_kingdom: Название выбранного княжества.
    :return: Список словарей с данными о городах.
    """
    # Подключение к базе данных
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()

    try:
        # Запрос к таблице city для получения данных по выбранному княжеству
        query = """
        SELECT id, kingdom, color, fortress_name, coordinates
        FROM city
        WHERE kingdom = ?
        """
        cursor.execute(query, (selected_kingdom,))
        rows = cursor.fetchall()

        # Преобразование данных в список словарей
        cities = []
        for row in rows:
            city_data = {
                'id': row[0],
                'kingdom': row[1],
                'color': row[2],
                'fortress_name': row[3],
                'coordinates': row[4]  # Предполагается, что координаты хранятся как строка "x,y"
            }
            cities.append(city_data)

        return cities

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
        return []

    finally:
        # Закрытие соединения с базой данных
        conn.close()


def restore_from_backup():
    """
    Загрузка данных из стандартных таблиц (default) в рабочие таблицы.
    Используется при запуске новой игры для восстановления начального состояния.
    """
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Подключение к базе данных
    conn = None
    try:
        conn = sqlite3.connect('game_data.db')
        cursor = conn.cursor()

        # Список таблиц для восстановления
        tables_to_restore = [
            ("city_default", "city"),
            ("diplomacies_default", "diplomacies"),
            ("relations_default", "relations"),
            ("resources_default", "resources"),
            ("cities_default", "cities"),
            ("units_default", "units")
        ]

        # Проверяем существование всех стандартных таблиц
        all_tables_exist = True
        for default_table, _ in tables_to_restore:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (default_table,))
            if not cursor.fetchone():
                logging.error(f"Таблица {default_table} не найдена в базе данных.")
                all_tables_exist = False

        if not all_tables_exist:
            logging.error("Не все стандартные таблицы найдены. Восстановление невозможно.")
            return

        # Начало транзакции
        cursor.execute("BEGIN TRANSACTION")

        # Восстанавливаем данные из стандартных таблиц в рабочие
        for default_table, working_table in tables_to_restore:
            try:
                # Проверяем, есть ли данные в стандартной таблице
                cursor.execute(f"SELECT COUNT(*) FROM {default_table}")
                if cursor.fetchone()[0] == 0:
                    logging.warning(f"Стандартная таблица {default_table} пуста. Пропускаем восстановление.")
                    continue

                # Очищаем рабочую таблицу
                cursor.execute(f"DELETE FROM {working_table}")

                # Копируем данные из стандартной таблицы в рабочую
                cursor.execute(f'''
                    INSERT INTO {working_table}
                    SELECT * FROM {default_table}
                ''')
                logging.info(f"Данные успешно восстановлены из таблицы {default_table} в таблицу {working_table}.")
            except Exception as e:
                logging.error(f"Ошибка при восстановлении таблицы {working_table}: {e}")
                conn.rollback()  # Откатываем транзакцию в случае ошибки
                return

        # Фиксируем изменения
        conn.commit()
        logging.info("Все данные успешно восстановлены из стандартных таблиц.")

    except sqlite3.Error as e:
        logging.error(f"Ошибка при работе с базой данных: {e}")
        if conn:
            conn.rollback()  # Откатываем транзакцию в случае ошибки
    finally:
        if conn:
            conn.close()


def clear_tables(conn):
    """
    Очищает данные из указанных таблиц базы данных.
    :param conn: Подключение к базе данных SQLite.
    """
    tables_to_clear = [
        "buildings",
        "city",
        "diplomacies",
        "garrisons",
        "resources",
        "trade_agreements",
        "weapons",
        "turn",
        "armies",
        "political_systems",
        "karma",
        "user_faction",
        "units",
        "experience",
        "queries",
        "results"
    ]

    cursor = conn.cursor()

    try:
        for table in tables_to_clear:
            # Используем TRUNCATE или DELETE для очистки таблицы
            cursor.execute(f"DELETE FROM {table};")
            print(f"Таблица '{table}' успешно очищена.")

        # Фиксируем изменения
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при очистке таблиц: {e}")
        conn.rollback()  # Откат изменений в случае ошибки


class HallOfFameWidget(FloatLayout):
    def __init__(self, **kwargs):
        super(HallOfFameWidget, self).__init__(**kwargs)
        self.add_widget(Image(source='files/slava.jpg', allow_stretch=True, keep_ratio=False))  # Фон зала славы

        # Заголовок
        title = Label(text="[b][color=000000]Зал славы[/color][/b]", font_size='40sp', markup=True,
                      size_hint=(1, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.9})
        self.add_widget(title)

        # Поле для вывода лучших результатов
        self.results_label = Label(text=self.get_top_scores(), font_size='30sp', markup=True, halign="center",
                                   size_hint=(0.8, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                   color=(0, 0, 0, 5))
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
        self.conn = sqlite3.connect('game_data.db', check_same_thread=False)
        self.fortress_rectangles = []  # Список для хранения крепостей
        self.current_player_kingdom = player_kingdom  # Текущее королевство игрока
        self.map_pos = self.map_positions_start()  # Позиция карты
        print(self.current_player_kingdom)
        # Отрисовка карты
        with self.canvas:
            self.map_image = Rectangle(source='files/map/map.png', pos=self.map_pos, size=(screen_width, screen_height))
        # Отрисовка всех крепостей
        self.draw_fortresses()
        Clock.schedule_interval(lambda dt: self.update_cities(), 1)

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

        # Отрисовываем фон карты
        with self.canvas:
            self.map_image = Rectangle(
                source='files/map/map.png',
                pos=self.map_pos,
                size=(screen_width, screen_height)
            )

            # Словарь для соответствия фракций и изображений
            faction_images = {
                'Хиперион': 'files/buildings/giperion.png',
                'Аркадия': 'files/buildings/arkadia.png',
                'Селестия': 'files/buildings/celestia.png',
                'Этерия': 'files/buildings/eteria.png',
                'Халидон': 'files/buildings/halidon.png'
            }

            # Запрашиваем данные о городах из базы данных
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT fortress_name, kingdom, coordinates 
                    FROM city
                """)
                fortresses_data = cursor.fetchall()
            except sqlite3.Error as e:
                print(f"Ошибка при загрузке данных о городах: {e}")
                return

            # Проверяем, есть ли данные
            if not fortresses_data:
                print("Нет данных о городах в базе данных.")
                return

            # Отрисовываем крепости всех фракций
            for fortress_name, kingdom, coords_str in fortresses_data:
                try:
                    coords = ast.literal_eval(coords_str)
                    if len(coords) != 2:
                        raise ValueError("Неверный формат координат")
                    fort_x, fort_y = coords
                except (ValueError, SyntaxError) as e:
                    print(f"Ошибка при разборе координат города '{fortress_name}': {e}")
                    continue

                # Сдвигаем изображение только для отрисовки
                drawn_x = fort_x + self.map_pos[0] + 4
                drawn_y = fort_y + self.map_pos[1] + 2

                # Получаем путь к изображению для текущей фракции
                image_path = faction_images.get(kingdom, 'files/buildings/default.png')
                if not os.path.exists(image_path):
                    image_path = 'files/buildings/default.png'

                # Сохраняем прямоугольник, имя и владельца для проверки касания
                fort_rect = (drawn_x, drawn_y, 40, 40)
                self.fortress_rectangles.append((
                    fort_rect,
                    {"coordinates": (fort_x, fort_y), "name": fortress_name},
                    kingdom
                ))

                # Рисуем изображение крепости
                Rectangle(source=image_path, pos=(drawn_x, drawn_y), size=(40, 40))

                # Добавляем название города под значком
                display_name = (fortress_name[:20] + "...") if len(fortress_name) > 20 else fortress_name
                label = CoreLabel(text=display_name, font_size=12, color=(0, 0, 0, 1))
                label.refresh()
                text_texture = label.texture
                text_width, text_height = text_texture.size

                text_x = drawn_x + (40 - text_width) / 2
                text_y = drawn_y - text_height - 5

                Color(1, 1, 1, 1)
                Rectangle(texture=text_texture, pos=(text_x, text_y), size=(text_width, text_height))

    def check_fortress_click(self, touch):
        # Проверяем, была ли нажата крепость
        for fort_rect, fortress_data, owner in self.fortress_rectangles:
            x, y, w, h = fort_rect
            if x <= touch.x <= x + w and y <= touch.y <= y + h:
                # Сохраняем последний клик
                save_last_clicked_city(fortress_data["name"])

                # Открываем окно с информацией
                popup = FortressInfoPopup(
                    kingdom=owner,
                    city_coords=fortress_data["coordinates"],
                    player_fraction=self.current_player_kingdom
                )
                popup.open()
                print(
                    f"Крепость {fortress_data['coordinates']} "
                    f"принадлежит {'вашему' if owner == self.current_player_kingdom else 'чужому'} королевству!"
                )
                break

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
        # Очищаем canvas и снова рисуем карту и крепости
        self.canvas.clear()
        self.draw_fortresses()

    def update_cities(self):
        self.canvas.clear()
        self.draw_fortresses()

    def on_touch_up(self, touch):
        # Обрабатываем отпускание касания
        if touch.is_mouse_scrolling:
            return  # Игнорируем скроллинг
        self.check_fortress_click(touch)


class MenuWidget(FloatLayout):
    def __init__(self, **kwargs):
        super(MenuWidget, self).__init__(**kwargs)

        # Список с именами файлов картинок
        menu_images = ['files/menu/1.jpg', 'files/menu/2.jpg', 'files/menu/3.jpg', 'files/menu/4.jpg',
                       'files/menu/5.jpg']

        # Выбираем случайное изображение
        random_image = random.choice(menu_images)

        # Загружаем выбранное случайное изображение как фон
        self.add_widget(Image(source=random_image, allow_stretch=True, keep_ratio=False))  # Фон меню

        # Заголовок
        title = Label(text="[b][color=000000]Превосходство[/color][/b]", font_size='40sp', markup=True,
                      size_hint=(1, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.9})
        self.add_widget(title)

        # Кнопки
        btn_start_game = Button(text="Старт новой игры", size_hint=(0.5, 0.1),
                                pos_hint={'center_x': 0.5, 'center_y': 0.7},
                                background_normal='', background_color=(0, 0, 0, 1))
        btn_start_game.bind(on_press=self.start_game)

        btn_load_game = Button(text="Загрузка ранее сохраненной", size_hint=(0.5, 0.1),
                               pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_normal='',
                               background_color=(0, 0, 0, 1))
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

        # Подключение к базе данных и загрузка данных о княжествах
        self.conn = sqlite3.connect('game_data.db', check_same_thread=False)
        self.kingdom_data = self.load_kingdoms_from_db()

        # Фон выбора княжества с размытием
        self.add_widget(Image(source='files/choice.jpg', allow_stretch=True, keep_ratio=False))

        # Заголовок "Выберите сторону" над изображением советника
        self.select_side_label = Label(
            text="Выберите сторону",
            font_size='30sp',
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.75, 'center_y': 0.85},
            color=(1, 1, 1, 1),  # Белый текст
            outline_color=(0, 0, 0, 1),
            outline_width=2,
            markup=True
        )
        self.add_widget(self.select_side_label)

        # Надпись с названием фракции (изначально пустая)
        self.faction_label = Label(
            text="",
            font_size='24sp',
            size_hint=(None, None),
            size=(300, 100),
            pos_hint={'center_x': 0.75, 'center_y': 0.30},
            color=(1, 1, 1, 1),  # Белый текст
            outline_color=(0, 0, 0, 1),
            outline_width=2,
            markup=True,
            halign="center",
            valign="middle"
        )
        self.faction_label.bind(size=self.faction_label.setter('text_size'))  # Для переноса текста
        self.add_widget(self.faction_label)

        # Панель для кнопок выбора княжеств
        self.kingdom_buttons = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint=(0.4, 0.5),
            pos_hint={'center_x': 0.4, 'center_y': 0.5},
            padding=[10, 10, 10, 10]
        )

        # Создание кнопок для каждого княжества с анимацией
        for kingdom in self.kingdom_data.keys():
            btn = Button(
                text=kingdom,
                size_hint=(1, None),
                height=60,
                background_normal='',
                background_color=(0.1, 0.5, 0.9, 1),  # Синий цвет кнопок
                color=(1, 1, 1, 1),  # Белый цвет текста
                border=(20, 20, 20, 20)
            )
            btn.bind(on_press=self.select_kingdom)
            # Анимация при наведении
            btn.bind(on_enter=lambda x: Animation(background_color=(0.2, 0.6, 1, 1), duration=0.2).start(x))
            btn.bind(on_leave=lambda x: Animation(background_color=(0.1, 0.5, 0.9, 1), duration=0.2).start(x))
            self.kingdom_buttons.add_widget(btn)

        self.add_widget(self.kingdom_buttons)

        # Изображение советника
        self.advisor_image = Image(
            source='files/null.png',
            size_hint=(0.3, 0.3),
            pos_hint={'center_x': 0.75, 'center_y': 0.65}
        )
        self.add_widget(self.advisor_image)

        # Кнопка для начала игры с анимацией
        self.start_game_button = Button(
            text="Начать игру",
            size_hint=(0.4, None),
            height=60,
            pos_hint={'center_x': 0.8, 'center_y': 0.10},
            background_normal='',
            background_color=(0.1, 0.5, 0.9, 1),
            color=(1, 1, 1, 1),  # Белый цвет текста
            border=(20, 20, 20, 20)
        )
        self.start_game_button.bind(on_press=self.start_game)
        # Анимация при наведении
        self.start_game_button.bind(
            on_enter=lambda x: Animation(background_color=(0.2, 0.6, 1, 1), duration=0.2).start(x))
        self.start_game_button.bind(
            on_leave=lambda x: Animation(background_color=(0.1, 0.5, 0.9, 1), duration=0.2).start(x))
        self.add_widget(self.start_game_button)

    def load_kingdoms_from_db(self):
        """Загружает данные о княжествах из базы данных."""
        kingdoms = {}
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT kingdom, fortress_name, coordinates, color
                FROM city_default
            """)
            rows = cursor.fetchall()
            for row in rows:
                kingdom, fortress_name, coordinates, color = row
                if kingdom not in kingdoms:
                    kingdoms[kingdom] = {
                        "fortresses": [],
                        "color": color
                    }
                kingdoms[kingdom]["fortresses"].append({
                    "name": fortress_name,
                    "coordinates": coordinates
                })
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных из базы данных: {e}")
        return kingdoms

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
        app.selected_kingdom = kingdom_name

        english_name = kingdom_rename.get(kingdom_name, kingdom_name).lower()
        advisor_image_path = f'files/sov/sov_{english_name}.jpg'
        self.advisor_image.source = advisor_image_path
        self.advisor_image.reload()

        # Обновляем текст для надписи с названием фракции
        faction_info_text = self.get_kingdom_info(kingdom_name)
        self.faction_label.text = f"[b]{kingdom_name}[/b]\n\n{faction_info_text}"

    def get_kingdom_info(self, kingdom):
        info = {
            "Аркадия": "Доход крон: 10\nДоход сырья: 5\nАрмия: 9\n",
            "Селестия": "Доход крон: 8\nДоход сырья: 6\nАрмия: 7\n",
            "Хиперион": "Доход крон: 7\nДоход сырья: 7\nАрмия: 10\n",
            "Халидон": "Доход крон: 4\nДоход сырья: 10\nАрмия: 6\n",
            "Этерия": "Доход крон: 6\nДоход сырья: 8\nАрмия: 8\n"
        }
        return info.get(kingdom, "")

    def start_game(self, instance):
        # Очистка старых данных из БД
        # housekeeping()
        app = App.get_running_app()
        selected_kingdom = app.selected_kingdom
        if selected_kingdom is None:
            print("Фракция не выбрана. Пожалуйста, выберите фракцию перед началом игры.")
            return

        if selected_kingdom is None:
            print("Фракция не выбрана. Пожалуйста, выберите фракцию перед началом игры.")
            return

        # Загружаем данные из базы данных
        cities = load_cities_from_db(selected_kingdom)

        if not cities:
            print("Для выбранного княжества не найдено городов.")
            return

        # Очистка временных таблиц
        # Подключение к базе данных
        conn = sqlite3.connect('game_data.db')
        clear_tables(conn)
        # Закрытие соединения
        conn.close()

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
    def __init__(self, **kwargs):
        super(EmpireApp, self).__init__(**kwargs)
        self.selected_kingdom = None  # Атрибут для хранения выбранного королевства

    def build(self):
        return MenuWidget()  # Возвращаем виджет главного меню


if __name__ == '__main__':
    EmpireApp().run()  # Запуск приложения
