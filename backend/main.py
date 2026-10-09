from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime, timedelta

from ai.prediction import predict_priority, predict_collection_need

app = FastAPI(
    title="SwachhAI API",
    description="Smart Waste Management API",
    version="2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_PATH = "data/swachhai.db"


def get_database_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def get_latest_bins():
    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            s.bin_id,
            s.fill_level,
            s.weight,
            s.temperature,
            s.timestamp
        FROM sensor_readings s
        INNER JOIN (
            SELECT
                bin_id,
                MAX(id) AS max_id
            FROM sensor_readings
            GROUP BY bin_id
        ) latest
        ON s.bin_id = latest.bin_id
        AND s.id = latest.max_id
        ORDER BY s.bin_id
    """)

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def get_priority(fill):
    if fill >= 85:
        return "CRITICAL"
    elif fill >= 70:
        return "HIGH"
    elif fill >= 50:
        return "MEDIUM"
    else:
        return "LOW"


@app.get("/")
def home():
    return {
        "message": "SwachhAI Backend is running!",
        "status": "online",
        "version": "2.1"
    }


@app.get("/bins")
def get_bins():

    bins = get_latest_bins()

    for bin_data in bins:

        ai_result = predict_priority(
            fill_level=float(bin_data["fill_level"]),
            temperature=float(bin_data["temperature"]),
            weight=float(bin_data["weight"])
        )

        bin_data["priority"] = ai_result["priority"]
        bin_data["score"] = ai_result["score"]
        bin_data["reason"] = ai_result["reason"]
        bin_data["recommendation"] = ai_result["recommendation"]

    return bins


@app.get("/ai")
def get_ai_summary():

    bins = get_latest_bins()

    result = predict_collection_need(bins)

    return {
        "total_bins": len(bins),
        "overall_priority": result["priority"],
        "message": result["message"],
        "critical_bins": result["critical_bins"],
        "high_priority_bins": result["high_priority_bins"],
        "predictions": result["predictions"]
    }


@app.get("/ai/priority")
def get_priority_predictions():

    bins = get_latest_bins()

    predictions = []

    for bin_data in bins:

        result = predict_priority(
            fill_level=float(bin_data["fill_level"]),
            temperature=float(bin_data["temperature"]),
            weight=float(bin_data["weight"])
        )

        predictions.append({
            "bin_id": bin_data["bin_id"],
            "priority": result["priority"],
            "score": result["score"],
            "reason": result["reason"],
            "recommendation": result["recommendation"]
        })

    predictions.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return {
        "predictions": predictions
    }


@app.get("/ai/collection")
def get_collection_prediction():

    bins = get_latest_bins()

    result = predict_collection_need(bins)

    return result


@app.get("/routes")
def get_routes():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            s.bin_id,
            s.fill_level,
            s.weight,
            s.temperature,
            s.timestamp
        FROM sensor_readings s
        INNER JOIN (
            SELECT
                bin_id,
                MAX(id) AS max_id
            FROM sensor_readings
            GROUP BY bin_id
        ) latest
        ON s.bin_id = latest.bin_id
        AND s.id = latest.max_id
        ORDER BY s.fill_level DESC
    """)

    rows = cursor.fetchall()
    connection.close()

    routes = []

    for row in rows:

        fill = float(row["fill_level"])

        routes.append({
            "bin_id": row["bin_id"],
            "fill_level": fill,
            "weight": row["weight"],
            "temperature": row["temperature"],
            "priority": get_priority(fill),
            "timestamp": row["timestamp"]
        })

    return {
        "route": routes,
        "total_bins": len(routes)
    }


@app.get("/history")
def get_history(date: str):

    try:
        selected_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {
            "error": "Invalid date format. Use YYYY-MM-DD."
        }

    next_date = selected_date + timedelta(days=1)

    start_time = selected_date.strftime("%Y-%m-%d 00:00:00")
    end_time = next_date.strftime("%Y-%m-%d 00:00:00")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            bin_id,
            fill_level,
            weight,
            temperature,
            timestamp
        FROM sensor_readings
        WHERE timestamp >= ?
        AND timestamp < ?
        ORDER BY timestamp DESC, bin_id
    """, (start_time, end_time))

    rows = cursor.fetchall()
    connection.close()

    history = []

    for row in rows:

        fill = float(row["fill_level"])

        history.append({
            "id": row["id"],
            "bin_id": row["bin_id"],
            "fill_level": fill,
            "weight": row["weight"],
            "temperature": row["temperature"],
            "priority": get_priority(fill),
            "timestamp": row["timestamp"]
        })

    return {
        "date": date,
        "total_records": len(history),
        "records": history
    }


@app.get("/history/yesterday")
def get_yesterday_history():

    yesterday = datetime.now().date() - timedelta(days=1)

    date_string = yesterday.strftime("%Y-%m-%d")

    start_time = yesterday.strftime("%Y-%m-%d 00:00:00")
    end_time = (yesterday + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            bin_id,
            fill_level,
            weight,
            temperature,
            timestamp
        FROM sensor_readings
        WHERE timestamp >= ?
        AND timestamp < ?
        ORDER BY timestamp DESC, bin_id
    """, (start_time, end_time))

    rows = cursor.fetchall()
    connection.close()

    history = []

    for row in rows:

        fill = float(row["fill_level"])

        history.append({
            "id": row["id"],
            "bin_id": row["bin_id"],
            "fill_level": fill,
            "weight": row["weight"],
            "temperature": row["temperature"],
            "priority": get_priority(fill),
            "timestamp": row["timestamp"]
        })

    return {
        "date": date_string,
        "total_records": len(history),
        "records": history
    }


@app.get("/history/summary")
def get_history_summary(date: str):

    try:
        selected_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {
            "error": "Invalid date format. Use YYYY-MM-DD."
        }

    next_date = selected_date + timedelta(days=1)

    start_time = selected_date.strftime("%Y-%m-%d 00:00:00")
    end_time = next_date.strftime("%Y-%m-%d 00:00:00")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_records,
            AVG(fill_level) AS average_fill,
            MAX(fill_level) AS highest_fill,
            SUM(weight) AS total_weight
        FROM sensor_readings
        WHERE timestamp >= ?
        AND timestamp < ?
    """, (start_time, end_time))

    summary = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) AS critical_count
        FROM sensor_readings
        WHERE timestamp >= ?
        AND timestamp < ?
        AND fill_level >= 85
    """, (start_time, end_time))

    critical = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) AS high_count
        FROM sensor_readings
        WHERE timestamp >= ?
        AND timestamp < ?
        AND fill_level >= 70
        AND fill_level < 85
    """, (start_time, end_time))

    high = cursor.fetchone()

    connection.close()

    return {
        "date": date,
        "total_records": summary["total_records"] or 0,
        "average_fill": round(summary["average_fill"] or 0, 2),
        "highest_fill": round(summary["highest_fill"] or 0, 2),
        "total_weight": round(summary["total_weight"] or 0, 2),
        "critical_records": critical["critical_count"] or 0,
        "high_records": high["high_count"] or 0
    }