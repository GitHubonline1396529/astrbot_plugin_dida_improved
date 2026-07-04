from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from astrbot_plugin_dida_improved.time_utils import (
    get_timezone,
    now_in_timezone,
    parse_api_datetime,
    resolve_timezone_name,
    today_in_timezone,
)


class TestResolveTimezoneName:
    def test_valid_timezone(self):
        assert resolve_timezone_name("Asia/Shanghai") == "Asia/Shanghai"

    def test_invalid_timezone(self):
        assert (
            resolve_timezone_name("Invalid/Zone", fallback_timezone="UTC")
            == "UTC"
        )

    def test_empty_string(self):
        assert resolve_timezone_name("") == "Asia/Shanghai"

    def test_invalid_fallback(self):
        result = resolve_timezone_name(
            "Invalid/Zone", fallback_timezone="Also/Invalid"
        )
        assert result == "Asia/Shanghai"


class TestGetTimezone:
    def test_valid(self):
        tz = get_timezone("Asia/Shanghai")
        assert isinstance(tz, ZoneInfo)

    def test_invalid_falls_back_to_local(self):
        tz = get_timezone("Bogus/Place")
        assert isinstance(tz, ZoneInfo)


class TestNowInTimezone:
    def test_returns_datetime(self):
        dt = now_in_timezone("UTC")
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None
        assert dt.tzinfo.key == "UTC"

    def test_asia_shanghai_offset(self):
        dt = now_in_timezone("Asia/Shanghai")
        assert dt.utcoffset() == timedelta(hours=8)


class TestTodayInTimezone:
    def test_returns_date(self):
        d = today_in_timezone("UTC")
        assert isinstance(d, date)


class TestParseApiDatetime:
    def test_full_iso_with_tz(self):
        result = parse_api_datetime(
            "2026-07-04T10:00:00+08:00",
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="UTC",
        )
        assert result is not None
        assert result.hour == 2
        assert result.minute == 0
        assert result.tzinfo.key == "UTC"

    def test_z_suffix(self):
        result = parse_api_datetime(
            "2026-07-04T02:00:00Z",
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="Asia/Shanghai",
        )
        assert result is not None
        assert result.hour == 10

    def test_no_tz_uses_assume(self):
        result = parse_api_datetime(
            "2026-07-04T10:00:00",
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="UTC",
        )
        assert result is not None
        assert result.hour == 2

    def test_date_only(self):
        result = parse_api_datetime(
            "2026-07-04",
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="Asia/Shanghai",
        )
        assert result is not None
        assert result.year == 2026
        assert result.month == 7
        assert result.day == 4
        assert result.hour == 0

    def test_empty_string(self):
        result = parse_api_datetime(
            "",
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="Asia/Shanghai",
        )
        assert result is None

    def test_none(self):
        result = parse_api_datetime(
            None,  # type: ignore[arg-type]
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="Asia/Shanghai",
        )
        assert result is None

    def test_invalid_string(self):
        result = parse_api_datetime(
            "not-a-date",
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="Asia/Shanghai",
        )
        assert result is None

    def test_offset_without_colon(self):
        result = parse_api_datetime(
            "2026-07-04T10:00:00+0800",
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="UTC",
        )
        assert result is not None
        assert result.hour == 2

    def test_target_timezone_conversion(self):
        result = parse_api_datetime(
            "2026-07-04T10:00:00+08:00",
            assume_timezone_name="Asia/Shanghai",
            target_timezone_name="America/New_York",
        )
        assert result is not None
        # 10:00 CST = 22:00 EDT previous day
        assert result.hour == 22
        assert result.day == 3
