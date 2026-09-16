from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE_NAME = "Asia/Shanghai"


def resolve_timezone_name(
    preferred_timezone: str = "",
    *,
    fallback_timezone: str = DEFAULT_TIMEZONE_NAME,
) -> str:
    """Resolve a timezone name, falling back if invalid.

    Args:
        preferred_timezone: Preferred IANA timezone name.
        fallback_timezone: Fallback IANA timezone name.

    Returns:
        A valid IANA timezone name.
    """
    candidate = str(preferred_timezone or "").strip()
    fallback = str(fallback_timezone or "").strip() or DEFAULT_TIMEZONE_NAME

    if candidate:
        try:
            ZoneInfo(candidate)
            return candidate
        except ZoneInfoNotFoundError:
            pass

    try:
        ZoneInfo(fallback)
        return fallback
    except ZoneInfoNotFoundError:
        return DEFAULT_TIMEZONE_NAME


def get_timezone(timezone_name: str) -> ZoneInfo:
    """Get a ZoneInfo object for the given timezone name.

    Args:
        timezone_name: IANA timezone name.

    Returns:
        ZoneInfo instance.
    """
    resolved_name = resolve_timezone_name(timezone_name)
    try:
        return ZoneInfo(resolved_name)
    except ZoneInfoNotFoundError:
        return datetime.now().astimezone().tzinfo


def now_in_timezone(timezone_name: str) -> datetime:
    """Get the current time in the specified timezone.

    Args:
        timezone_name: IANA timezone name.

    Returns:
        Current datetime in the specified timezone.
    """
    return datetime.now(get_timezone(timezone_name))


def today_in_timezone(timezone_name: str) -> date:
    """Get today's date in the specified timezone.

    Args:
        timezone_name: IANA timezone name.

    Returns:
        Today's date in the specified timezone.
    """
    return now_in_timezone(timezone_name).date()


def parse_api_datetime(
    value: str,
    *,
    assume_timezone_name: str,
    target_timezone_name: str,
) -> datetime | None:
    """Parse a datetime string from the Dida365 API.

    Args:
        value: The datetime string from the API.
        assume_timezone_name: Timezone to assume if none is present.
        target_timezone_name: Target timezone for the result.

    Returns:
        Parsed datetime in the target timezone, or None if parsing fails.
    """
    text = str(value or "").strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00")
    if (
        len(normalized) >= 5
        and normalized[-5] in {"+", "-"}
        and normalized[-3] != ":"
    ):
        normalized = f"{normalized[:-2]}:{normalized[-2:]}"

    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        date_part = text[:10]
        try:
            parsed = datetime.fromisoformat(date_part)
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=get_timezone(assume_timezone_name))

    return parsed.astimezone(get_timezone(target_timezone_name))
