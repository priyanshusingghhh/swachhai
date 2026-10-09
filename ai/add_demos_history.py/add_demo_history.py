
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "data/swachhai.db"
BIN_IDS = ["BIN_01", "BIN_02", "BIN_03", "BIN_04", "BIN_05"]

def get_status(fill):
    if fill >= 85:
        return "CRITICAL"
    if fill >= 60:
        return "WARNING"
    return "NORMAL"

def main():
    random.seed(42)
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

    today = datetime.now().date()
    inserted = 0

    for days_ago in range(7, 0, -1):
        day = today - timedelta(days=days_ago)

        for hour in [8, 12, 16, 20]:
            for bin_id in BIN_IDS:
                fill = round(random.uniform(20, 95), 1)
                weight = round(fill * random.uniform(0.15, 0.22), 2)
                temperature = round(random.uniform(28, 38), 1)
                timestamp = datetime.combine(
                    day, datetime.min.time()
                ).replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                    INSERT INTO sensor_readings
                    (bin_id, fill_level, weight, temperature, status, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    bin_id, fill, weight, temperature,
                    get_status(fill), timestamp
                ))
                inserted += 1

    db.commit()
    db.close()
    print(f"Added {inserted} demo history records.")
    print("These are simulated readings, not real sensor measurements.")

if __name__ == "__main__":
    main()