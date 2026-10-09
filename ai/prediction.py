def predict_priority(fill_level, temperature, weight):
    fill_level = float(fill_level)
    temperature = float(temperature)
    weight = float(weight)

    score = 0
    reasons = []

    if fill_level >= 85:
        score += 60
        reasons.append("very high fill level")
    elif fill_level >= 70:
        score += 45
        reasons.append("high fill level")
    elif fill_level >= 50:
        score += 25
        reasons.append("moderate fill level")
    else:
        score += 10

    if weight >= 15:
        score += 20
        reasons.append("high waste weight")
    elif weight >= 10:
        score += 12
        reasons.append("increasing waste weight")
    elif weight >= 5:
        score += 6

    if temperature >= 40:
        score += 20
        reasons.append("high temperature")
    elif temperature >= 35:
        score += 10
        reasons.append("elevated temperature")

    if score >= 70:
        priority = "CRITICAL"
        recommendation = "Collect immediately."
    elif score >= 50:
        priority = "HIGH"
        recommendation = "Schedule collection soon."
    elif score >= 30:
        priority = "MEDIUM"
        recommendation = "Monitor closely."
    else:
        priority = "LOW"
        recommendation = "No immediate collection required."

    if reasons:
        reason_text = ", ".join(reasons)
    else:
        reason_text = "normal sensor conditions"

    return {
        "priority": priority,
        "score": score,
        "reason": reason_text,
        "recommendation": recommendation
    }


def predict_collection_need(bins):
    if not bins:
        return {
            "priority": "LOW",
            "message": "No bin data available.",
            "bins": []
        }

    predictions = []

    for bin_data in bins:
        prediction = predict_priority(
            bin_data["fill_level"],
            bin_data["temperature"],
            bin_data["weight"]
        )

        predictions.append({
            "bin_id": bin_data["bin_id"],
            "fill_level": bin_data["fill_level"],
            "weight": bin_data["weight"],
            "temperature": bin_data["temperature"],
            "priority": prediction["priority"],
            "score": prediction["score"],
            "reason": prediction["reason"],
            "recommendation": prediction["recommendation"]
        })

    priority_order = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1
    }

    predictions.sort(
        key=lambda x: priority_order[x["priority"]],
        reverse=True
    )

    critical = [
        item for item in predictions
        if item["priority"] == "CRITICAL"
    ]

    high = [
        item for item in predictions
        if item["priority"] == "HIGH"
    ]

    if critical:
        overall_priority = "CRITICAL"
        message = "Immediate collection required for critical bins."
    elif high:
        overall_priority = "HIGH"
        message = "Collection should be scheduled soon."
    elif any(item["priority"] == "MEDIUM" for item in predictions):
        overall_priority = "MEDIUM"
        message = "Some bins require closer monitoring."
    else:
        overall_priority = "LOW"
        message = "No immediate collection required."

    return {
        "priority": overall_priority,
        "message": message,
        "critical_bins": len(critical),
        "high_priority_bins": len(high),
        "predictions": predictions
    }


if __name__ == "__main__":
    sample_bins = [
        {
            "bin_id": "BIN_01",
            "fill_level": 92,
            "weight": 16,
            "temperature": 38
        },
        {
            "bin_id": "BIN_02",
            "fill_level": 68,
            "weight": 9,
            "temperature": 33
        },
        {
            "bin_id": "BIN_03",
            "fill_level": 35,
            "weight": 4,
            "temperature": 30
        }
    ]

    result = predict_collection_need(sample_bins)

    print("\nSwachhAI AI Prediction")
    print("----------------------")

    print("Overall Priority:", result["priority"])
    print("Message:", result["message"])
    print("Critical Bins:", result["critical_bins"])
    print("High Priority Bins:", result["high_priority_bins"])

    print("\nBin Predictions:")

    for item in result["predictions"]:
        print(
            item["bin_id"],
            "| Priority:", item["priority"],
            "| Score:", item["score"],
            "| Reason:", item["reason"],
            "|", item["recommendation"]
        )