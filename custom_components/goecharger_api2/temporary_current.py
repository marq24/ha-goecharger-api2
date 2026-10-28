"""Validation for an expiring limit; never changes the user's amp/ama settings."""
import math
from collections.abc import Mapping


def is_finite_number(value) -> bool:
    """Reject booleans and oversized integers without leaking conversion errors."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def current_bounds(data: Mapping, limit_to_16a: bool = False) -> tuple[int, int]:
    """Require known hardware/user bounds rather than guessing an upper limit."""
    if not isinstance(data, Mapping):
        raise ValueError("Charger data is unavailable")
    variant = data.get("var")
    if isinstance(variant, bool) or variant not in (11, 22):
        raise ValueError("The charger current rating is unknown")
    lower, upper = data.get("mca"), data.get("ama")
    for value in (lower, upper):
        if not is_finite_number(value):
            raise ValueError("The charger current bounds are unavailable")
    reported = data.get("tcl")
    if reported is not None and (
        not is_finite_number(reported) or reported < 0 or reported != int(reported)
    ):
        raise ValueError("The temporary current limit is not a valid reported value")
    maximum = min(16 if variant == 11 or limit_to_16a else 32, math.floor(upper))
    minimum = max(6, math.ceil(lower))
    if minimum > maximum:
        raise ValueError("The charger current bounds are inconsistent")
    return minimum, maximum


def validate_current(value, data: Mapping, limit_to_16a: bool = False) -> int:
    """Only accept whole amperes in range; zero/null reset semantics are not assumed."""
    if not isinstance(data, Mapping) or "tcl" not in data:
        raise ValueError("This charger has not reported temporary-current-limit support")
    minimum, maximum = current_bounds(data, limit_to_16a)
    if not is_finite_number(value):
        raise ValueError("Current must be a finite number of whole amperes")
    if value != int(value) or not minimum <= value <= maximum:
        raise ValueError(f"Current must be between {minimum} and {maximum} whole amperes")
    return int(value)


def require_acknowledgement(result, current: int) -> None:
    """The existing bridge returns the submitted value only after a successful write."""
    if not isinstance(result, dict) or isinstance(result.get("tcl"), bool) or result.get("tcl") != current:
        raise ValueError("The charger did not acknowledge the temporary current limit")
