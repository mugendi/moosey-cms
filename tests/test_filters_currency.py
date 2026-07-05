from unittest.mock import patch

from moosey_cms.filters import (
    currency, compact_currency,
    country_flag, country_name, language_name, currency_name,
)


class TestCurrency:
    def test_usd(self):
        assert currency(1234.56) == "$1,234.56"

    def test_eur(self):
        assert currency(1234.56, code="EUR", symbol="€") == "€1,234.56"

    def test_jpy_zero_decimal(self):
        assert currency(1500, code="JPY") == "¥1,500"

    def test_integer_input(self):
        assert currency(42) == "$42.00"

    def test_large_number(self):
        assert currency(1000000) == "$1,000,000.00"

    def test_none_returns_empty(self):
        assert currency(None) == ""

    def test_invalid_value_returns_str(self):
        assert currency("not-a-number") == "not-a-number"

    def test_without_pycountry(self):
        with patch.dict("sys.modules", {"pycountry": None}):
            import importlib
            import moosey_cms.filters as f
            importlib.reload(f)
            assert f.currency(1500, code="JPY") == "¥1,500"


class TestCompactCurrency:
    def test_thousands(self):
        assert compact_currency(45000) == "$45.0K"

    def test_millions(self):
        assert compact_currency(1200000) == "$1.2M"

    def test_billions(self):
        assert compact_currency(1500000000) == "$1.5B"

    def test_small_value(self):
        assert compact_currency(999) == "$999.00"

    def test_eur(self):
        assert compact_currency(2000000, code="EUR") == "€2.0M"

    def test_none_returns_empty(self):
        assert compact_currency(None) == ""

    def test_invalid_value_returns_str(self):
        assert compact_currency("bad") == "bad"


class TestCountryFlag:
    def test_alpha_2_us(self):
        assert country_flag("US") == "🇺🇸"

    def test_alpha_3_ken(self):
        assert country_flag("KEN") == "🇰🇪"

    def test_lowercase(self):
        assert country_flag("gb") == "🇬🇧"

    def test_invalid_code(self):
        assert country_flag("ZZ") == ""

    def test_none_returns_empty(self):
        assert country_flag(None) == ""

    def test_invalid_length(self):
        assert country_flag("TOOLONG") == ""


class TestCountryName:
    def test_alpha_2(self):
        assert country_name("US") == "United States"

    def test_alpha_3(self):
        assert country_name("KEN") == "Kenya"

    def test_none_returns_empty(self):
        assert country_name(None) == ""

    def test_invalid_code(self):
        result = country_name("ZZ")
        assert result == "ZZ"

    def test_without_pycountry(self):
        with patch.dict("sys.modules", {"pycountry": None}):
            import importlib
            import moosey_cms.filters as f
            importlib.reload(f)
            assert f.country_name("US") == "United States"


class TestLanguageName:
    def test_alpha_2(self):
        assert language_name("en") == "English"

    def test_alpha_3(self):
        assert language_name("swa") == "Swahili"

    def test_none_returns_empty(self):
        assert language_name(None) == ""

    def test_invalid_code(self):
        result = language_name("xx")
        assert result == "xx"

    def test_without_pycountry(self):
        with patch.dict("sys.modules", {"pycountry": None}):
            import importlib
            import moosey_cms.filters as f
            importlib.reload(f)
            assert f.language_name("en") == "English"


class TestCurrencyName:
    def test_usd(self):
        assert currency_name("USD") == "US Dollar"

    def test_kes(self):
        assert currency_name("KES") == "Kenyan Shilling"

    def test_lowercase(self):
        assert currency_name("eur") == "Euro"

    def test_none_returns_empty(self):
        assert currency_name(None) == ""

    def test_invalid_code(self):
        assert currency_name("XXX") == "XXX"

    def test_without_pycountry(self):
        with patch.dict("sys.modules", {"pycountry": None}):
            import importlib
            import moosey_cms.filters as f
            importlib.reload(f)
            assert f.currency_name("KES") == "Kenyan Shilling"
