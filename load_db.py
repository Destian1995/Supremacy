import sqlite3

# Подключение к базе данных (или создание новой, если файл не существует)
db_path = "game_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Создание таблицы turn
cursor.execute('''
    CREATE TABLE IF NOT EXISTS turn (
        faction TEXT PRIMARY KEY,
        turn_count INTEGER
    )
''')

# Создание таблицы turn_save
cursor.execute('''
    CREATE TABLE IF NOT EXISTS turn_save (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faction TEXT,
        turn_count INTEGER,
        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Сохранение изменений и закрытие соединения
conn.commit()
conn.close()

print("Таблицы успешно созданы.")