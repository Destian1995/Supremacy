import sqlite3

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.app import App
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.core.window import Window

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

            # Добавляем все значения в список, включая вычисленные
            calculated_results.append(
                {
                    "id": id,
                    "units_combat": units_combat,
                    "units_destroyed": units_destroyed,
                    "units_killed": units_killed,
                    "army_efficiency_ratio": army_efficiency_ratio,
                    "average_deal_ratio": average_deal_ratio,
                    "faction": faction,
                }
            )

        return calculated_results

    def show_results(self, faction_name, status, reason):
        self.game_status = status
        self.reason = reason

        calculated_results = self.calculate_results()

        # Формируем заголовок
        if self.game_status == "win":
            title = "Победа!"
            color = (0, 1, 0, 1)  # Зеленый
            message = f"[b]{faction_name} одержала победу![/b]\n {reason}\n\n"
        elif self.game_status == "lose":
            title = "Поражение!"
            color = (1, 0, 0, 1)  # Красный
            message = f"[b]{faction_name} потерпела поражение.[/b]\n {reason}\n\n"
        else:
            title = "Результаты игры"
            color = (1, 1, 1, 1)
            message = "Неизвестный статус завершения игры.\n\n"

        # Отображаем результаты в графическом интерфейсе
        self.show_results_popup(title, message, calculated_results, color)

    def show_results_popup(self, title, message, results, text_color):
        # Создаем основной контейнер
        layout = FloatLayout()

        # Расчет параметров адаптации
        def adapt_value(base, factor=0.5):
            """Динамический расчет размеров на основе плотности пикселей"""
            dpi = max(Window.width / (Window.width / dp(100)), 1)
            return max(dp(base * factor * (dpi / 160)), dp(base))

        # Стилизация фона
        bg_color = (0.12, 0.12, 0.12, 1)
        radius = [adapt_value(15)] * 4

        # Инициализация фона
        with layout.canvas.before:
            Color(*bg_color)
            self.background_rect = RoundedRectangle(
                pos=layout.pos,
                size=layout.size,
                radius=radius
            )

        # Привязка обновления фона
        def update_bg(instance, value):
            self.background_rect.pos = layout.pos
            self.background_rect.size = layout.size
            self.background_rect.radius = radius

        layout.bind(pos=update_bg, size=update_bg)

        # Сообщение
        message_label = Label(
            text=message,
            color=text_color,
            markup=True,
            font_size=adapt_value(18, 0.6),
            size_hint=(0.9, None),
            height=adapt_value(100),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'top': 0.97},
            text_size=(Window.width * 0.85, None),
            line_height=1.2
        )
        message_label.bind(size=message_label.setter('text_size'))

        # Контейнер для таблицы
        table_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.95, 0.7),
            pos_hint={"center_x": 0.5, "top": 0.75},
            spacing=adapt_value(10)
        )

        # ScrollView
        scroll_view = ScrollView(
            size_hint=(1, 1),
            bar_width=adapt_value(10),
            bar_color=(0.5, 0.5, 0.5, 0.7),
            bar_inactive_color=(0.3, 0.3, 0.3, 0)
        )

        # Таблица
        table_layout = GridLayout(
            cols=6,
            spacing=adapt_value(2),
            size_hint=(1, None),
            padding=adapt_value(5),
            row_default_height=adapt_value(40)
        )
        table_layout.bind(minimum_height=table_layout.setter('height'))

        # Адаптивные размеры
        base_font = adapt_value(14)
        row_height = adapt_value(35)

        # Заголовки таблицы
        headers = ["Фракция", "Ветераны", "Потери", "Уничтожено", "Военный \n рейтинг", "Торговый \n рейтинг"]
        for header in headers:
            lbl = Label(
                text=header,
                color=(1, 1, 1, 1),
                bold=True,
                font_size=base_font,
                size_hint_y=None,
                height=row_height,
                halign='center',
                valign='middle'
            )
            lbl.bind(
                size=lambda instance, _: setattr(instance.bg_rect, 'size', instance.size),
                pos=lambda instance, _: setattr(instance.bg_rect, 'pos', instance.pos)
            )

            with lbl.canvas.before:
                Color(0.15, 0.4, 0.7, 1)
                lbl.bg_rect = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=radius)

            table_layout.add_widget(lbl)

        # Данные таблицы
        for i, res in enumerate(results):
            row_color = (0.14, 0.14, 0.14, 1) if i % 2 == 0 else (0.16, 0.16, 0.16, 1)
            row_data = [
                res["faction"],
                f"{res['units_combat']:,}".replace(',', ' '),
                f"{res['units_destroyed']:,}".replace(',', ' '),
                f"{res['units_killed']:,}".replace(',', ' '),
                f"{res['army_efficiency_ratio']:.2f}",
                f"{res['average_deal_ratio']:.2f}"
            ]

            for value in row_data:
                lbl = Label(
                    text=value,
                    color=(0.92, 0.92, 0.92, 1),
                    font_size=base_font * 0.9,
                    size_hint_y=None,
                    height=row_height,
                    halign='center',
                    valign='middle'
                )
                lbl.bind(
                    size=lambda instance, _: setattr(instance.bg_rect, 'size', instance.size),
                    pos=lambda instance, _: setattr(instance.bg_rect, 'pos', instance.pos)
                )

                with lbl.canvas.before:
                    Color(*row_color)
                    lbl.bg_rect = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=radius)

                table_layout.add_widget(lbl)

        scroll_view.add_widget(table_layout)
        table_container.add_widget(scroll_view)

        # Кнопка выхода
        exit_btn = Button(
            text="ВЕРНУТЬСЯ В МЕНЮ",
            font_size=dp(16) if Window.width < 600 else dp(18),
            size_hint=(0.7, None),
            height=dp(45),
            pos_hint={"center_x": 0.5, "y": 0.02},
            background_color=(0.2, 0.5, 0.8, 1),
            background_normal=''
        )
        exit_btn.bind(on_press=self.exit_to_main_menu)

        # Добавляем элементы
        layout.add_widget(message_label)
        layout.add_widget(table_container)
        layout.add_widget(exit_btn)

        # Создаем попап
        popup = Popup(
            title="",
            content=layout,
            size_hint=(
                min(0.95, Window.width / 1000 + 0.6),
                min(0.95, Window.height / 1000 + 0.6)
            ),
            auto_dismiss=False,
            background=''
        )

        # Функция адаптации
        def adapt_layout(*args):
            table_layout.width = scroll_view.width
            message_label.text_size = (message_label.width * 0.95, None)
            table_layout.row_default_height = adapt_value(40)
            table_layout.spacing = adapt_value(2)
            scroll_view.bar_width = adapt_value(10)

        # Привязка к изменению размеров
        Window.bind(width=lambda *x: adapt_layout(), height=lambda *x: adapt_layout())
        Clock.schedule_once(adapt_layout)

        popup.open()
        self.popup = popup

    def exit_to_main_menu(self, instance):
        self.close_connection()
        app = App.get_running_app()

        # Закрываем все попапы
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()

        # Полная перезагрузка приложения
        app.restart_app()

