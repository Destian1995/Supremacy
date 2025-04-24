import sqlite3

from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.scrollview import ScrollView


class ResultsGame:
    def __init__(self, game_status, reason):
        self.game_status = game_status  # Статус игры: "win" или "lose"
        self.reason = reason  # Причина завершения игры

    def load_results(self):
        """
        Загрузка результатов игры из базы данных.
        :return: Список результатов.
        """
        conn = sqlite3.connect('game_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM results')
        results = cursor.fetchall()
        conn.close()
        return results

    def calculate_results(self):
        """
        Вычисляет дополнительные показатели на основе данных из таблицы results.
        :return: Список словарей с полными данными, включая вычисленные значения.
        """
        results = self.load_results()

        calculated_results = []
        for row in results:
            (
                id,
                units_combat,
                units_destroyed,
                units_killed,
                army_efficiency_ratio,
                average_deal_ratio,
                average_net_profit_coins,
                average_net_profit_raw,
                economic_efficiency,
                faction,
            ) = row

            # Вычисляем Army_Efficiency_Ratio
            if units_destroyed != 0:
                army_efficiency_ratio = round(units_killed / units_destroyed, 2)
            else:
                army_efficiency_ratio = 0  # Защита от деления на ноль

            # Вычисляем Economic_Efficiency
            economic_efficiency = round(
                average_deal_ratio + (average_net_profit_coins + average_net_profit_raw) / 100000, 2
            )

            # Добавляем все значения в список, включая вычисленные
            calculated_results.append(
                {
                    "id": id,
                    "units_combat": units_combat,
                    "units_destroyed": units_destroyed,
                    "units_killed": units_killed,
                    "army_efficiency_ratio": army_efficiency_ratio,
                    "average_deal_ratio": average_deal_ratio,
                    "average_net_profit_coins": average_net_profit_coins,
                    "average_net_profit_raw": average_net_profit_raw,
                    "economic_efficiency": economic_efficiency,
                    "faction": faction,
                }
            )

        return calculated_results

    def show_results(self, faction_name, status, reason):
        """
        Основной метод для отображения результатов игры.
        :param faction_name: Название фракции.
        :param status: Статус завершения ("win" или "lose").
        :param reason: Причина завершения игры.
        """
        self.game_status = status
        self.reason = reason

        # Вычисляем дополнительные показатели для всех фракций
        calculated_results = self.calculate_results()

        # Формируем заголовок
        if self.game_status == "win":
            title = "Победа!"
            message = f"Фракция '{faction_name}' одержала победу!\nПричина: {reason}\n\n"
        elif self.game_status == "lose":
            title = "Поражение!"
            message = f"Фракция '{faction_name}' потерпела поражение.\nПричина: {reason}\n\n"
        else:
            title = "Результаты игры"
            message = "Неизвестный статус завершения игры.\n\n"

        # Отображаем результаты в графическом интерфейсе
        self.show_results_popup(title, message, calculated_results)

    def show_results_popup(self, title, message, results):
        """
        Создает полноэкранное окно с результатами игры.
        :param title: Заголовок окна.
        :param message: Сообщение с результатами.
        :param results: Список словарей с результатами для всех фракций.
        """
        layout = FloatLayout(size=Window.size)

        # Фоновое оформление
        with layout.canvas.before:
            Color(0.15, 0.15, 0.15, 1)  # Темно-серый фон
            self.rect = Rectangle(pos=layout.pos, size=layout.size)

        # Заголовок
        title_label = Label(
            text=title,
            font_size=Window.width * 0.05,  # Размер шрифта зависит от ширины экрана
            color=(1, 1, 1, 1),  # Белый текст
            pos_hint={"center_x": 0.5, "top": 0.95},
            size_hint=(None, None),
        )

        # ScrollView для таблицы
        scroll_view = ScrollView(
            size_hint=(0.9, 0.7),  # Занимает 90% ширины и 70% высоты экрана
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        # GridLayout для таблицы
        table_layout = GridLayout(
            cols=9,  # Девять столбцов: все параметры
            size_hint_y=None,  # Высота будет зависеть от содержимого
            spacing=Window.width * 0.01,  # Интервал между ячейками (1% ширины экрана)
            padding=Window.width * 0.02,  # Отступы вокруг таблицы (2% ширины экрана)
        )
        table_layout.bind(minimum_height=table_layout.setter("height"))  # Автоматическая высота

        # Заголовки таблицы
        headers = [
            "Фракция",
            "Боевые ед.",
            "Уничтожено",
            "Убито",
            "Рейтинг Армии",
            "Торговый рейтинг",
            "Доход монет",
            "Доход сырья",
            "Рейтинг Экономики"
        ]
        font_size_headers = Window.width * 0.02  # Размер шрифта заголовков
        for header in headers:
            table_layout.add_widget(Label(
                text=header,
                color=(1, 1, 1, 1),
                bold=True,
                font_size=font_size_headers,
                size_hint_y=None,
                height=Window.height * 0.05  # Высота строки заголовков (5% высоты экрана)
            ))

        # Добавляем данные в таблицу
        font_size_data = Window.width * 0.02  # Размер шрифта данных
        row_height = Window.height * 0.04  # Высота строки данных (4% высоты экрана)
        for res in results:
            faction = res["faction"]
            units_combat = res["units_combat"]
            units_destroyed = res["units_destroyed"]
            units_killed = res["units_killed"]
            army_efficiency_ratio = res["army_efficiency_ratio"]
            average_deal_ratio = res["average_deal_ratio"]
            average_net_profit_coins = res["average_net_profit_coins"]
            average_net_profit_raw = res["average_net_profit_raw"]
            economic_efficiency = res["economic_efficiency"]

            # Добавляем значения в таблицу
            for value in [
                faction,
                str(units_combat),
                str(units_destroyed),
                str(units_killed),
                str(army_efficiency_ratio),
                str(average_deal_ratio),
                str(average_net_profit_coins),
                str(average_net_profit_raw),
                str(economic_efficiency)
            ]:
                table_layout.add_widget(Label(
                    text=value,
                    color=(1, 1, 1, 1),
                    font_size=font_size_data,
                    size_hint_y=None,
                    height=row_height
                ))

        # Добавляем таблицу в ScrollView
        scroll_view.add_widget(table_layout)

        # Кнопка "Выход в главное меню"
        main_menu_button = Button(
            text="Выход в главное меню",
            font_size=Window.width * 0.03,  # Размер шрифта кнопки (3% ширины экрана)
            background_color=(0.2, 0.6, 1, 1),  # Синий цвет
            pos_hint={"center_x": 0.3, "y": 0.05},
            size_hint=(0.3, 0.1),
        )
        main_menu_button.bind(on_press=self.exit_to_main_menu)

        # Кнопка "Выход из игры"
        exit_game_button = Button(
            text="Выход из игры",
            font_size=Window.width * 0.03,  # Размер шрифта кнопки (3% ширины экрана)
            background_color=(1, 0.2, 0.2, 1),  # Красный цвет
            pos_hint={"center_x": 0.7, "y": 0.05},
            size_hint=(0.3, 0.1),
        )
        exit_game_button.bind(on_press=self.exit_game)

        # Добавляем виджеты в layout
        layout.add_widget(title_label)
        layout.add_widget(scroll_view)
        layout.add_widget(main_menu_button)
        layout.add_widget(exit_game_button)

        # Создаем полноэкранное окно
        popup = Popup(
            title="",
            content=layout,
            size_hint=(1, 1),
            auto_dismiss=False,
        )

        # Добавляем возможность закрыть окно по нажатию на кнопки
        main_menu_button.bind(on_press=popup.dismiss)
        exit_game_button.bind(on_press=popup.dismiss)

        popup.open()


    def exit_to_main_menu(self, instance):
        """
        Выход в главное меню.
        """
        print("Переход в главное меню...")
        app = App.get_running_app()

        # Очищаем текущие виджеты
        app.root.clear_widgets()

        # Создаем и добавляем виджет главного меню
        from main import MenuWidget  # Импортируем экран главного меню
        app.root.add_widget(MenuWidget())


    def exit_game(self, instance):
        """
        Выход из игры.
        """
        print("Выход из игры...")
        App.get_running_app().stop()  # Завершаем приложение


    def analyze_results(self, faction_name, status, reason):
        """
        Анализирует результаты игры и выполняет дополнительные действия.
        Например, может использоваться для генерации статистики или наград.
        :param faction_name: Название фракции.
        :param status: Статус завершения ("win" или "lose").
        :param reason: Причина завершения игры.
        """
        if status == "win":
            print(f"Анализ победы фракции '{faction_name}': {reason}")
        elif status == "lose":
            print(f"Анализ поражения фракции '{faction_name}': {reason}")