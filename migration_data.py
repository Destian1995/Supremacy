import sqlite3
import json

# Подключение к базе данных
db_path = "game_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Проверка существования таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='units';")
table_exists = cursor.fetchone()

if table_exists:
    print("Таблица 'units' существует.")
else:
    print("Таблица 'units' не существует.")

conn.close()
# Функция для добавления юнита в таблицу units
def add_unit(faction, unit_name, cost_money, cost_time, image_path, attack, defense, durability, unit_class):
    cursor.execute('''
        INSERT INTO units (faction, unit_name, cost_money, cost_time, image_path, attack, defense, durability, unit_class)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (faction, unit_name, cost_money, cost_time, image_path, attack, defense, durability, unit_class))
    conn.commit()

# Загрузка данных из JSON-файлов
data_files = {
    "Аркадия": "files/config/units/arkadia.json",
    "Селестия": "files/config/units/celestia.json",
    "Хиперион": "files/config/units/giperion.json",
    "Этерия": "files/config/units/eteria.json",
    "Халидон": "files/config/units/halidon.json"
}

for faction, file_name in data_files.items():
    with open(file_name, "r", encoding="utf-8") as file:
        faction_data = json.load(file)
        for unit_name, unit_info in faction_data.items():
            cost_money, cost_time = unit_info["cost"]
            image_path = unit_info["image"]
            stats = unit_info["stats"]
            attack = stats["Урон"]
            defense = stats["Защита"]
            durability = stats["Живучесть"]
            unit_class = stats["Класс юнита"]
            add_unit(faction, unit_name, cost_money, cost_time, image_path, attack, defense, durability, unit_class)

# Закрытие соединения
conn.close()

print("Данные успешно добавлены в таблицу 'units'.")