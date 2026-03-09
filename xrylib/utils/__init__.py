"""
xrylib.utils — Shared helpers for date parsing, field normalisation, and type coercion.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, List, Optional

# ------------------------------------------------------------------ #
#  Date / time parsing                                                 #
# ------------------------------------------------------------------ #

# Common date/time formats seen in XRY XML exports
_DT_FORMATS: List[str] = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
]


def parse_datetime(value: Any) -> Optional[datetime]:
    """
    Parse a datetime from a string, int (Unix epoch), or datetime.

    Returns a timezone-aware UTC datetime, or None if parsing fails.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        # Unix epoch (seconds or milliseconds)
        ts = float(value)
        if ts > 1e10:  # likely milliseconds
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        # Try each known format
        for fmt in _DT_FORMATS:
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                continue
        # Last resort: try ISO fromisoformat (Python 3.7+)
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass
    return None


# ------------------------------------------------------------------ #
#  Boolean parsing                                                     #
# ------------------------------------------------------------------ #

_TRUTHY = {"true", "yes", "1", "y", "on", "deleted", "read"}
_FALSY = {"false", "no", "0", "n", "off", "unread"}


def parse_bool(value: Any) -> Optional[bool]:
    """Parse a boolean from string, int, or bool."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in _TRUTHY:
            return True
        if s in _FALSY:
            return False
    return None


# ------------------------------------------------------------------ #
#  Integer / float coercion                                            #
# ------------------------------------------------------------------ #


def parse_int(value: Any) -> Optional[int]:
    """Safely coerce a value to int."""
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def parse_float(value: Any) -> Optional[float]:
    """Safely coerce a value to float."""
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


# ------------------------------------------------------------------ #
#  String normalisation                                                #
# ------------------------------------------------------------------ #


def normalise_str(value: Any) -> Optional[str]:
    """Strip whitespace; return None for empty / None values."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def normalise_phone(number: Any) -> Optional[str]:
    """
    Minimal phone number normalisation: strip non-digit chars except leading '+'.
    """
    if number is None:
        return None
    s = str(number).strip()
    cleaned = re.sub(r"[^\d+]", "", s)
    return cleaned if cleaned else None


# ------------------------------------------------------------------ #
#  Direction detection                                                 #
# ------------------------------------------------------------------ #

_INCOMING_KEYWORDS = {"incoming", "received", "in", "receive", "recv"}
_OUTGOING_KEYWORDS = {"outgoing", "sent", "out", "send"}
_MISSED_KEYWORDS = {"missed", "unanswered"}


def parse_direction(value: Any) -> Optional[str]:
    """
    Normalise a direction string to one of:
    'Incoming' | 'Outgoing' | 'Missed' | 'Rejected' | 'Unknown'.
    """
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in _INCOMING_KEYWORDS:
        return "Incoming"
    if s in _OUTGOING_KEYWORDS:
        return "Outgoing"
    if s in _MISSED_KEYWORDS:
        return "Missed"
    if "reject" in s:
        return "Rejected"
    return "Unknown"


# ------------------------------------------------------------------ #
#  GPS coordinate parsing                                              #
# ------------------------------------------------------------------ #

# Accepts: "53.483959 -2.244644"  /  "53.483959,-2.244644"
_COORD_RE = re.compile(r"(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)")


def parse_coordinates(lat: Any, lon: Any):
    """
    Parse latitude and longitude into floats.
    Accepts combined 'lat lon' string if lon is None.
    Returns (latitude_float, longitude_float) or (None, None).
    """
    if lat is not None and lon is None:
        # Try to parse both from a combined string
        m = _COORD_RE.search(str(lat))
        if m:
            return parse_float(m.group(1)), parse_float(m.group(2))
        return None, None
    return parse_float(lat), parse_float(lon)
