def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def severity_from_risk(score: float) -> str:
    if score >= 90:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def status_from_risk(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 40:
        return "warning"
    return "healthy"
