from kivy.clock import Clock
from kivy.properties import partial
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Line
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.progressbar import ProgressBar
import sqlite3
import time

def has_pending_action():
    conn = sqlite3.connect("game_data.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM last_click")
    count = cur.fetchone()[0]
    conn.close()
    return count > 0


def get_city_faction(city_name):
    conn = sqlite3.connect("game_data.db")
    cur = conn.cursor()
    cur.execute("SELECT faction FROM cities WHERE name=?", (city_name,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None


def get_allies_for_faction(faction_name):
    conn = sqlite3.connect("game_data.db")
    cur = conn.cursor()
    # Исправленный SQL-запрос: выбираем faction1 и faction2
    cur.execute(
        "SELECT faction1, faction2 FROM diplomacies "
        "WHERE (faction1=? OR faction2=?) AND relationship='союз'",
        (faction_name, faction_name)
    )
    # Нормализация и сбор союзников
    allies = {
        row[1] if row[0] == faction_name else row[0]
        for row in cur.fetchall()
    }
    conn.close()
    return allies


class ManageFriend(Popup):
    """
    Окно союзники:
    отображает список союзников и действия.
    """

    def __init__(self, faction_name, game_area, **kwargs):
        super().__init__(**kwargs)
        self.faction_name = faction_name
        self.title = "Союзник"
        self.size_hint = (0.8, 0.8)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.selection_mode = None
        self.selected_ally = None
        self.highlighted_city = None  # Для хранения круга подсветки
        self.status_label = Label(text="", size_hint_y=None, height=30)
        self._build_content()


    def _build_content(self):
        container = BoxLayout(orientation='vertical', spacing=10, padding=10)
        container.add_widget(self._create_table())
        container.add_widget(self.status_label)
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=30)
        self.progress_bar.opacity = 0  # изначально скрыт
        container.add_widget(self.progress_bar)
        cancel = Button(text="Отмена выбора", size_hint_y=None, height=40)
        cancel.bind(on_release=self.cancel_selection_mode)
        container.add_widget(cancel)
        close = Button(text="Закрыть", size_hint_y=None, height=40)
        close.bind(on_release=lambda btn: self.dismiss())
        container.add_widget(close)
        self.content = container

    def cancel_selection_mode(self, instance):
        self.selection_mode = None
        self.status_label.text = "Выбор отменён."

    def _create_table(self):
        allies = self._get_allies_from_db()

        grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        grid.add_widget(Label(text="Фракция", bold=True, size_hint_y=None, height=30))
        grid.add_widget(Label(text="Действия", bold=True, size_hint_y=None, height=30))

        for ally in allies:
            grid.add_widget(Label(text=ally, size_hint_y=None, height=40))
            grid.add_widget(self._create_dropdown_for_ally(ally))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(grid)
        return scroll

    def _create_dropdown_for_ally(self, ally):
        dd_main = DropDown()

        # Вложенное меню ресурсов
        dd_resources = DropDown()
        resources = ['Кроны', 'Сырьё', 'Рабочие']
        for res in resources:
            btn_res = Button(text=res, size_hint_y=None, height=40)
            btn_res.bind(on_release=lambda btn: self._on_resource_selected(ally, btn.text, dd_resources, dd_main))
            dd_resources.add_widget(btn_res)

        # Кнопка "Ресурсы", при нажатии открывает второе меню справа
        btn_resources = Button(text="Ресурсы ->", size_hint_y=None, height=40)
        btn_resources.bind(on_release=lambda btn: dd_resources.open(btn))

        # Другие действия
        btn_defense = Button(text="Защита", size_hint_y=None, height=40)
        btn_attack = Button(text="Атака", size_hint_y=None, height=40)

        btn_defense.bind(on_release=partial(self._on_action_wrapper, 'defense', ally, dd_main))
        btn_attack.bind(on_release=partial(self._on_action_wrapper, 'attack', ally, dd_main))

        dd_main.add_widget(btn_resources)
        dd_main.add_widget(btn_defense)
        dd_main.add_widget(btn_attack)

        main_btn = Button(text="Запросить", size_hint_y=None, height=40)
        main_btn.bind(on_release=lambda btn: dd_main.open(btn))
        return main_btn

    def _on_action_wrapper(self, action, ally, dropdown, instance):
        dropdown.dismiss()
        if action == 'resources':
            self._show_resource_dropdown(ally, instance)  # передаём кнопку, куда привязать второе меню
        else:
            self._on_action(action, ally)

    def _show_resource_dropdown(self, ally, anchor_button):
        resource_dropdown = DropDown()
        resources = ['Кроны', 'Сырьё', 'Рабочие']

        for res in resources:
            btn = Button(text=res, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn_inst: self._on_resource_selected(ally, btn_inst.text, resource_dropdown))
            resource_dropdown.add_widget(btn)

        resource_dropdown.open(anchor_button)

    def _on_resource_selected(self, ally, resource, dropdown_res, dropdown_main):
        dropdown_res.dismiss()
        dropdown_main.dismiss()
        self._send_request(ally, resource)

    def _get_allies_from_db(self):
        conn = sqlite3.connect("game_data.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT faction1, faction2 FROM diplomacies "
            "WHERE (faction1=? OR faction2=?) AND relationship='союз'",
            (self.faction_name, self.faction_name)
        )
        # Используем set comprehension
        allies = {
            r[1] if r[0] == self.faction_name else r[0]
            for r in cur.fetchall()
        }
        conn.close()
        return list(allies)

    def _on_action(self, action, ally):
        self.progress_bar.opacity = 1
        self.progress_bar.value = 0
        self.status_label.text = f"Ожидание выбора города для {'защиты' if action == 'defense' else 'атаки'}..."

        self.city_wait_start_time = time.time()
        self.city_last_name = ""
        self.city_selection_duration = 3
        self.city_check_event = Clock.schedule_interval(
            lambda dt: self._check_city_selection(dt, action, ally), 0.2
        )

        self.progress_event = Clock.schedule_interval(
            lambda dt: self._update_progress_bar(dt), 0.05
        )

        self.dismiss()

    def _update_progress_bar(self, dt):
        if self.progress_bar.value < 100:
            self.progress_bar.value += 2
        else:
            self.progress_bar.value = 100

    def _has_existing_action(self):
        conn = sqlite3.connect("game_data.db")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM queries")
        count = cur.fetchone()[0]
        conn.close()
        return count > 0

    def _check_city_selection(self, dt, action, ally):
        conn = sqlite3.connect("game_data.db")
        cur = conn.cursor()
        cur.execute("SELECT city_name FROM last_click")
        row = cur.fetchone()
        conn.close()

        if row and row[0]:
            current_city = row[0]

            if not self.city_last_name:
                self.city_last_name = current_city
                self.city_wait_start_time = time.time()
            elif current_city == self.city_last_name:
                if time.time() - self.city_wait_start_time > self.city_selection_duration:
                    # Проверяем — есть ли уже действия
                    if self._has_existing_action():
                        self.status_label.text = "Нельзя отправить более одного запроса за ход."
                    else:
                        self._finalize_city_selection(current_city, action, ally)

                    # Останавливаем оба события
                    Clock.unschedule(self.city_check_event)
                    Clock.unschedule(self.progress_event)
        else:
            # Если ничего не выбрано слишком долго — можно таймаут сделать
            if time.time() - self.city_wait_start_time > 10:
                self.status_label.text = "Город не выбран. Повторите попытку."
                Clock.unschedule(self.city_check_event)
                Clock.unschedule(self.progress_event)

    def _finalize_city_selection(self, city_name, action, ally):
        city_faction = get_city_faction(city_name)
        allies = get_allies_for_faction(self.faction_name)

        if action == "defense":
            if city_faction == self.faction_name:
                self.save_query_defense_to_db(city_name)
                self.status_label.text = f"Запрос на защиту города {city_name} отправлен."
            else:
                self.status_label.text = "Нельзя защищать чужие города."
        elif action == "attack":
            if city_faction != self.faction_name and city_faction not in allies:
                self.save_query_attack_to_db(city_name)
                self.status_label.text = f"Запрос на атаку города {city_name} отправлен."
            else:
                self.status_label.text = "Нельзя атаковать дружественные города."

        self.progress_bar.opacity = 0

    def _handle_city_action(self, city_name, action, ally):
        if not city_name:
            self.status_label.text = "Город не выбран."
            return

        city_faction = get_city_faction(city_name)
        allies = get_allies_for_faction(self.faction_name)

        if action == "defense":
            if city_faction == self.faction_name:
                self.save_query_defense_to_db(city_name)
                self.status_label.text = f"Запрос на защиту города {city_name} отправлен."
            else:
                self.status_label.text = "Нельзя защищать чужие города."
        elif action == "attack":
            if city_faction != self.faction_name and city_faction not in allies:
                self.save_query_attack_to_db(city_name)
                self.status_label.text = f"Запрос на атаку города {city_name} отправлен."
            else:
                self.status_label.text = "Нельзя атаковать дружественные города."

    def set_selection_mode(self, mode, ally):
        self.selection_mode = mode
        self.selected_ally = ally

    def on_touch_down(self, touch):
        if self.selection_mode:
            for city in self.cities:
                if self.is_click_on_city(touch.x, touch.y, city):
                    self.highlight_city(city)
                    if self.selection_mode == 'defense':
                        if city['faction'] == self.faction_name:
                            self.save_query_defense_to_db(city['name'])
                            self.status_label.text = f"Запрос на защиту {city['name']} отправлен"
                    elif self.selection_mode == 'attack':
                        if city['faction'] != self.faction_name:
                            self.save_query_attack_to_db(city['name'])
                            self.status_label.text = f"Запрос на атаку {city['name']} отправлен"
                    self.selection_mode = None
                    break
        return super().on_touch_down(touch)

    def save_query_attack_to_db(self, attack_city):
        """
        Сохраняет запрос на атаку города в таблицу queries.
        """
        conn = sqlite3.connect("game_data.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO queries (resource, defense_city, attack_city, faction) VALUES (?, ?, ?, ?)",
            ("", "", attack_city, self.faction_name)  # Добавляем название фракции в запрос
        )

        conn.commit()
        conn.close()

    def save_query_defense_to_db(self, defense_city):
        """
        Сохраняет запрос на защиту города в таблицу queries.
        """
        conn = sqlite3.connect("game_data.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO queries (resource, defense_city, attack_city, faction) VALUES (?, ?, ?, ?)",
            ("", defense_city, "", self.faction_name)  # Добавляем название фракции в запрос
        )

        conn.commit()
        conn.close()

    def save_query_resources_to_db(self, resource):
        """
        Сохраняет запрос на передачу ресурса в таблицу queries.
        """
        conn = sqlite3.connect("game_data.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO queries (resource, defense_city, attack_city, faction) VALUES (?, ?, ?, ?)",
            (resource, "", "", self.faction_name)  # Добавляем название фракции в запрос
        )

        conn.commit()
        conn.close()

    def clear_selection_mode(self):
        self.selection_mode = None
        if self.highlighted_city:
            self.game_area.canvas.remove(self.highlighted_city)
            self.highlighted_city = None



    def _send_request(self, ally, resource):
        """
        Отправка запроса на передачу ресурса союзнику.
        """
        print(f"Запрос: передать {resource} союзнику {ally}")

        # Сохраняем запрос в таблице queries
        self.save_query_resources_to_db(resource)

        self.transfer_resource_to_ally(ally, resource)

    def transfer_resource_to_ally(self, ally_name, resource_type):
        print(f"Переводим {resource_type} для {ally_name}")

    def open_popup(self):
        super().open()

