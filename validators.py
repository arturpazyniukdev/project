import math


def ensure_number(value, label):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{label} must be an int or float, got {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number, got {value}")
