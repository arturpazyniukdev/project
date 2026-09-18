import math


def ensure_number(value, label):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{label} must be an int or float, got {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number, got {value}")
    return value


def ensure_text(value, label):
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a str, got {type(value).__name__}")
    value = value.strip()
    if len(value) == 0:
        raise ValueError(f"{label} should not be empty")
    return value
