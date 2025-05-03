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
            message = f"{faction_name} одержала победу!\nПричина: {reason}\n\n"
        elif self.game_status == "lose":
            title = "Поражение!"
            message = f"{faction_name} потерпела поражение.\nПричина: {reason}\n\n"
        else:
            title = "Результаты игры"
            message = "Неизвестный статус завершения игры.\n\n"

        # Отображаем результаты в графическом интерфейсе
        self.show_results_popup(title, message, calculated_results)

    def show_results_popup(self, title, message, results):
        # Создаем основной контейнер
        layout = FloatLayout()

        # Стилизация фона
        bg_color = (0.12, 0.12, 0.12, 1)
        radius = [dp(15)]

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

        layout.bind(pos=update_bg, size=update_bg)

        # Создаем контейнер для сообщения и таблицы
        main_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.95, 0.85),
            pos_hint={"center_x": 0.5, "top": 0.9},
            spacing=dp(10)
        )

        # Добавляем сообщение
        message_label = Label(
            text=message,
            color=(0.9, 0.9, 0.9, 1),
            font_size=dp(16) if Window.width < 600 else dp(18),
            size_hint_y=None,
            height=dp(100) if Window.height < 800 else dp(120),
            halign='left',
            valign='top',
            text_size=(Window.width * 0.9, None)
        )
        message_label.bind(size=message_label.setter('text_size'))
        main_box.add_widget(message_label)

        # Создание ScrollView
        scroll_view = ScrollView(
            size_hint=(0.95, 0.72),
            pos_hint={"center_x": 0.5, "top": 0.82},
            bar_width=dp(10),
            bar_color=(0.5, 0.5, 0.5, 0.7),
            bar_inactive_color=(0.3, 0.3, 0.3, 0),
            effect_cls='ScrollEffect'
        )

        # Создание таблицы
        table_layout = GridLayout(
            cols=6,
            spacing=dp(1.5),
            size_hint_y=None,
            padding=dp(10))
        table_layout.bind(minimum_height=table_layout.setter('height'))

        # Адаптивные размеры

        def get_sizes():
            return (
                dp(16) if Window.width < 600 else dp(18),
                dp(14) if Window.width < 600 else dp(16),
                dp(45) if Window.height < 800 else dp(50)
            )

        # Заголовки таблицы
        headers = ["Фракция", "Ветераны", "Потери", "Уничтожено", "Военный рейтинг", "Торговый рейтинг"]
        font_header, _, row_h = get_sizes()

        for header in headers:
            lbl = Label(
                text=header,
                color=(1, 1, 1, 1),
                bold=True,
                font_size=font_header,
                size_hint_y=None,
                height=row_h,
                halign='center',
                valign='middle'
            )
            lbl.bind(size=lbl.setter('text_size'))

            # Фон заголовка с явной привязкой
            with lbl.canvas.before:
                Color(0.15, 0.4, 0.7, 1)
                bg = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=radius)

            # Сохраняем ссылку на фон
            lbl.bg_rect = bg
            lbl.bind(
                pos=lambda instance, _: setattr(instance.bg_rect, 'pos', instance.pos),
                size=lambda instance, _: setattr(instance.bg_rect, 'size', instance.size)
            )
            table_layout.add_widget(lbl)

        # Данные таблицы
        even_color = (0.14, 0.14, 0.14, 1)
        odd_color = (0.16, 0.16, 0.16, 1)
        _, font_data, row_h = get_sizes()

        for i, res in enumerate(results):
            row_color = even_color if i % 2 == 0 else odd_color
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
                    font_size=font_data,
                    size_hint_y=None,
                    height=row_h,
                    halign='center',
                    valign='middle'
                )
                lbl.bind(size=lbl.setter('text_size'))

                # Фон строки с явной привязкой
                with lbl.canvas.before:
                    Color(*row_color)
                    bg = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=radius)

                # Сохраняем ссылку на фон
                lbl.bg_rect = bg
                lbl.bind(
                    pos=lambda instance, _: setattr(instance.bg_rect, 'pos', instance.pos),
                    size=lambda instance, _: setattr(instance.bg_rect, 'size', instance.size)
                )
                table_layout.add_widget(lbl)

        scroll_view.add_widget(table_layout)

        # Кнопка выхода
        exit_btn = Button(
            text="ВЕРНУТЬСЯ В МЕНЮ",
            font_size=dp(18) if Window.width < 600 else dp(20),
            background_color=(0.2, 0.5, 0.8, 1),
            background_normal='',
            pos_hint={"center_x": 0.5, "y": 0.02},
            size_hint=(0.7, None),
            height=dp(50) if Window.height < 800 else dp(60),
            border=(dp(12), dp(12), dp(12), dp(12))
        )
        exit_btn.bind(on_press=self.exit_to_main_menu)

        layout.add_widget(main_box)
        layout.add_widget(scroll_view)
        layout.add_widget(exit_btn)

        # Создание попапа
        popup = Popup(
            title="",
            content=layout,
            size_hint=(0.95, 0.95) if Window.width < 600 else (0.85, 0.9),
            auto_dismiss=False,
            separator_height=0,
            background='',
            background_color=bg_color
        )

        # Фикс артефактов
        def force_redraw(*args):
            for child in table_layout.children:
                child.canvas.ask_update()
            layout.canvas.ask_update()

        popup.bind(on_open=lambda *args: Clock.schedule_once(force_redraw, 0.1))
        self.popup = popup  # Сохраняем ссылку в классе
        popup.open()

    def exit_to_main_menu(self, instance):
        self.close_connection()
        app = App.get_running_app()

        # Закрываем все попапы
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()

        # Полная перезагрузка приложения
        app.restart_app()

