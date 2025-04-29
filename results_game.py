import sqlite3

from kivy.clock import Clock
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
        return results

    def close_connection(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

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

        with layout.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.rect = Rectangle(pos=layout.pos, size=layout.size)

        title_label = Label(
            text=title,
            font_size=Window.width * 0.05,
            color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "top": 0.95},
            size_hint=(None, None),
        )

        scroll_view = ScrollView(
            size_hint=(0.9, 0.7),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        # Исправлено: 7 столбцов вместо 9
        table_layout = GridLayout(
            cols=7,
            size_hint_y=None,
            spacing=Window.width * 0.01,
            padding=Window.width * 0.02,
        )
        table_layout.bind(minimum_height=table_layout.setter("height"))

        headers = [
            "Фракция",
            "Ветераны",
            "Потери",
            "Уничтожено",
            "Рейтинг Армии",
            "Торговый рейтинг",
            "Рейтинг Экономики"
        ]

        font_size_headers = Window.width * 0.02
        for header in headers:
            table_layout.add_widget(Label(
                text=header,
                color=(1, 1, 1, 1),
                bold=True,
                font_size=font_size_headers,
                size_hint_y=None,
                height=Window.height * 0.05
            ))

        font_size_data = Window.width * 0.02
        row_height = Window.height * 0.04

        for res in results:
            # Отбираем только нужные поля
            row_data = [
                res["faction"],
                str(res["units_combat"]),
                str(res["units_destroyed"]),
                str(res["units_killed"]),
                str(res["army_efficiency_ratio"]),
                str(res["average_deal_ratio"]),
                str(res["economic_efficiency"])
            ]

            for value in row_data:
                table_layout.add_widget(Label(
                    text=value,
                    color=(1, 1, 1, 1),
                    font_size=font_size_data,
                    size_hint_y=None,
                    height=row_height
                ))

        scroll_view.add_widget(table_layout)

        main_menu_button = Button(
            text="Выход в главное меню",
            font_size=Window.width * 0.03,
            background_color=(0.2, 0.6, 1, 1),
            pos_hint={"center_x": 0.3, "y": 0.05},
            size_hint=(0.3, 0.1),
        )
        main_menu_button.bind(on_press=self.exit_to_main_menu)

        layout.add_widget(title_label)
        layout.add_widget(scroll_view)
        layout.add_widget(main_menu_button)


        popup = Popup(
            title="",
            content=layout,
            size_hint=(1, 1),
            auto_dismiss=False,
        )

        main_menu_button.bind(on_press=popup.dismiss)
        self.popup = popup  # Сохраняем ссылку на попап
        popup.open()

    def exit_to_main_menu(self, instance):
        self.close_connection()
        app = App.get_running_app()

        # Закрываем все попапы
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()

        # Полная перезагрузка приложения
        app.restart_app()

        # Принудительная очистка виджетов
        app.root.clear_widgets()
        Clock.schedule_once(lambda dt: app.show_main_menu(), 0.1)


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