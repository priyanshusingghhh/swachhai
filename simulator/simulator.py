import sqlite3
import random
import time
from datetime import datetime

DB_PATH = "data/swachhai.db"

BIN_IDS = [
    "BIN_01",
    "BIN_02",
    "BIN_03",
    "BIN_04",
    "BIN_05"
]

def get_status(fill_level):
    if fill_level >= 85:
        return "CRITICAL"
    elif fill_level >= 60:
        return "WARNING"
    else:
        return "NORMAL"

def create_database():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bin_id TEXT,
            fill_level REAL,
            weight REAL,
            temperature REAL,
            status TEXT,
            timestamp TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(sensor_readings)")
    columns = [column[1] for column in cursor.fetchall()]

    if "status" not in columns:
        cursor.execute("""
            ALTER TABLE sensor_readings
            ADD COLUMN status TEXT
        """)

        cursor.execute("""
            UPDATE sensor_readings
            SET status = CASE
                WHEN fill_level >= 85 THEN 'CRITICAL'
                WHEN fill_level >= 60 THEN 'WARNING'
                ELSE 'NORMAL'
            END
            WHERE status IS NULL
        """)

    db.commit()
    db.close()

def generate_readings():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    for bin_id in BIN_IDS:
        fill_level = round(random.uniform(20, 95), 1)
        weight = round(fill_level * random.uniform(0.15, 0.22), 2)
        temperature = round(random.uniform(28, 38), 1)
        status = get_status(fill_level)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO sensor_readings
            (bin_id, fill_level, weight, temperature, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            bin_id,
            fill_level,
            weight,
            temperature,
            status,
            timestamp
        ))

        print(
            f"{timestamp} | {bin_id} | "
            f"Fill: {fill_level}% | "
            f"Weight: {weight}kg | "
            f"Temp: {temperature}°C | "
            f"Status: {status}"
        )

    db.commit()
    db.close()

def main():
    create_database()

    print("SwachhAI Simulator Started")
    print("New sensor data will be generated every 15 seconds.")
    print("Press Ctrl+C to stop.")
    print()

    while True:
        generate_readings()

        print()
        print("Waiting 15 seconds for the next sensor update...")
        print()

        time.sleep(15)

if __name__ == "__main__":
    main()