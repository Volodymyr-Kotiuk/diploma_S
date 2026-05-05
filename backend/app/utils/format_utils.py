def bytes_to_mb(value: float | int | None) -> float | None:
    return None if value is None else round(float(value) / 1024 / 1024, 2)


def bytes_to_gb(value: float | int | None) -> float | None:
    return None if value is None else round(float(value) / 1024 / 1024 / 1024, 2)


def safe_float(value: object, default: float | None = None) -> float | None:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default
