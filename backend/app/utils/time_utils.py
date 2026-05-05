from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def human_duration(seconds: float | int | None) -> str:
    if not seconds:
        return "невідомо"
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days:
        return f"{days} д {hours} год"
    if hours:
        return f"{hours} год {minutes} хв"
    return f"{minutes} хв"
