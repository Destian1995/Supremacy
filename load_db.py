import sqlite3
import os

# Путь к базе данных
db_path = "game_data.db"

# Функция для добавления записи в таблицу station_images
def add_station_image(conn, faction, image_path):
    """Добавляет путь к изображению станции для указанной фракции."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO station_images (faction, image_path)
        VALUES (?, ?)
    ''', (faction, image_path))
    conn.commit()

# Функция для поиска изображений станций
def populate_station_images():
    # Подключение к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создание таблицы station_images, если она еще не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS station_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faction TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
    ''')
    conn.commit()

    # Базовый путь к папке с изображениями
    base_path = "files/army"

    # Список фракций (можно расширить при необходимости)
    factions = ["arkadia", "celestia", "eteria", "giperion", "halidon"]

    for faction in factions:
        # Формируем путь к изображению станции
        image_path = os.path.join(base_path, faction, "stations_weapons.jpg")

        # Проверяем, существует ли файл
        if os.path.exists(image_path):
            print(f"Найдено изображение для фракции {faction}: {image_path}")
            add_station_image(conn, faction.capitalize(), image_path)  # Добавляем запись в БД
        else:
            print(f"Изображение для фракции {faction} не найдено: {image_path}")

    # Закрываем соединение с базой данных
    conn.close()

# Вызов функции для наполнения таблицы
populate_station_images()