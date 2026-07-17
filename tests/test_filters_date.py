from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import patch

from moosey_cms.filters import (
    fancy_date, short_date, iso_date, relative_time,
    time_only, strptime, rfc822_date,
)


class TestFancyDate:
    def test_normal_date(self, sample_dates):
        assert fancy_date(sample_dates["normal"]) == "13th Jan, 2026 at 6:00 PM"

    def test_midnight(self, sample_dates):
        assert fancy_date(sample_dates["midnight"]) == "15th Jun, 2026 at 12:00 AM"

    def test_noon(self, sample_dates):
        assert fancy_date(sample_dates["noon"]) == "25th Dec, 2025 at 12:00 PM"

    def test_early_morning(self, sample_dates):
        assert fancy_date(sample_dates["early"]) == "5th Mar, 2026 at 5:30 AM"

    def test_ordinal_11th(self, sample_dates):
        result = fancy_date(sample_dates["ordinal_11"])
        assert "11th" in result

    def test_ordinal_12th(self, sample_dates):
        result = fancy_date(sample_dates["ordinal_12"])
        assert "12th" in result

    def test_ordinal_13th(self, sample_dates):
        result = fancy_date(sample_dates["ordinal_13"])
        assert "13th" in result

    def test_ordinal_21st(self, sample_dates):
        result = fancy_date(sample_dates["ordinal_21"])
        assert "21st" in result

    def test_ordinal_22nd(self, sample_dates):
        result = fancy_date(sample_dates["ordinal_22"])
        assert "22nd" in result

    def test_ordinal_23rd(self, sample_dates):
        result = fancy_date(sample_dates["ordinal_23"])
        assert "23rd" in result

    def test_ordinal_31st(self, sample_dates):
        result = fancy_date(sample_dates["ordinal_31"])
        assert "31st" in result

    def test_none_returns_empty(self):
        assert fancy_date(None) == ""

    def test_empty_string_returns_empty(self):
        assert fancy_date("") == ""


class TestShortDate:
    def test_normal(self, sample_dates):
        assert short_date(sample_dates["normal"]) == "Jan 13, 2026"

    def test_date_object(self, sample_dates):
        assert short_date(sample_dates["date_only"]) == "Jul 04, 2026"

    def test_none_returns_empty(self):
        assert short_date(None) == ""


class TestIsoDate:
    def test_normal(self, sample_dates):
        assert iso_date(sample_dates["normal"]) == "2026-01-13"

    def test_none_returns_empty(self):
        assert iso_date(None) == ""


class TestRelativeTime:
    def test_just_now(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = relative_time(now)
            assert result == "just now"

    def test_minutes_ago(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now - timedelta(minutes=5)
            result = relative_time(then)
            assert result == "5 minutes ago"

    def test_one_minute_ago(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now - timedelta(minutes=1)
            result = relative_time(then)
            assert result == "1 minute ago"

    def test_hours_ago(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now - timedelta(hours=3)
            result = relative_time(then)
            assert result == "3 hours ago"

    def test_yesterday(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now.replace(day=now.day - 1)
            result = relative_time(then)
            assert result == "yesterday"

    def test_days_ago(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now.replace(day=now.day - 4)
            result = relative_time(then)
            assert result == "4 days ago"

    def test_weeks_ago(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now - timedelta(days=14)
            result = relative_time(then)
            assert result == "2 weeks ago"

    def test_months_ago(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["midnight"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now.replace(month=now.month - 3)
            result = relative_time(then)
            assert result == "3 months ago"

    def test_years_ago(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now.replace(year=now.year - 2)
            result = relative_time(then)
            assert result == "2 years ago"

    def test_without_ago_suffix(self, sample_dates):
        with patch("moosey_cms.filters.datetime") as mock_dt:
            now = sample_dates["normal"]
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            then = now.replace(hour=now.hour - 2)
            result = relative_time(then, showAgo=False)
            assert result == "2 hours"

    def test_none_returns_empty(self):
        assert relative_time(None) == ""


class TestTimeOnly:
    def test_normal(self, sample_dates):
        assert time_only(sample_dates["normal"]) == "6:00 PM"

    def test_midnight(self, sample_dates):
        assert time_only(sample_dates["midnight"]) == "12:00 AM"

    def test_early_morning(self, sample_dates):
        assert time_only(sample_dates["early"]) == "5:30 AM"

    def test_none_returns_empty(self):
        assert time_only(None) == ""


class TestStrptime:
    def test_basic(self):
        result = strptime("2026-01-13", "%Y-%m-%d")
        assert result == datetime(2026, 1, 13)

    def test_with_time(self):
        result = strptime("2026-01-13 18:00", "%Y-%m-%d %H:%M")
        assert result == datetime(2026, 1, 13, 18, 0)


class TestRfc822Date:
    def test_datetime(self, sample_dates):
        result = rfc822_date(sample_dates["normal"])
        assert "Jan 2026" in result
        assert "GMT" in result

    def test_date_only(self, sample_dates):
        result = rfc822_date(sample_dates["date_only"])
        assert "Jul 2026" in result
        assert "GMT" in result

    def test_iso_string(self):
        result = rfc822_date("2026-01-13T18:00:00Z")
        assert "Jan 2026" in result
        assert "GMT" in result

    def test_none_returns_empty(self):
        assert rfc822_date(None) == ""

    def test_empty_string_returns_empty(self):
        assert rfc822_date("") == ""


class TestStringDateInputs:
    def test_iso_datetime_string(self):
        value = "2026-01-13T18:00:00Z"

        assert fancy_date(value) == "13th Jan, 2026 at 6:00 PM"
        assert short_date(value) == "Jan 13, 2026"
        assert iso_date(value) == "2026-01-13"
        assert time_only(value) == "6:00 PM"

    def test_iso_date_string(self):
        assert short_date("2026-07-04") == "Jul 04, 2026"

    def test_timezone_aware_string_supports_relative_time(self):
        assert "year" in relative_time("2000-01-01T00:00:00Z")

    def test_unparseable_string_is_returned_unchanged(self):
        value = "not-a-date"

        assert fancy_date(value) == value
        assert short_date(value) == value
        assert iso_date(value) == value
        assert relative_time(value) == value
        assert time_only(value) == value
        assert rfc822_date(value) == value
