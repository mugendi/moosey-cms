from moosey_cms.filters import number_format, percentage, ordinal, filesize


class TestNumberFormat:
    def test_thousands(self):
        assert number_format(1234) == "1,234"

    def test_millions(self):
        assert number_format(1000000) == "1,000,000"

    def test_with_decimals(self):
        assert number_format(1234.56, decimals=2) == "1,234.56"

    def test_zero(self):
        assert number_format(0) == "0"

    def test_none_returns_empty(self):
        assert number_format(None) == ""

    def test_invalid_value_returns_str(self):
        assert number_format("bad") == "bad"


class TestPercentage:
    def test_basic(self):
        assert percentage(85.0) == "85.0%"

    def test_custom_decimals(self):
        assert percentage(85.333, decimals=2) == "85.33%"

    def test_zero(self):
        assert percentage(0) == "0.0%"

    def test_none_returns_empty(self):
        assert percentage(None) == ""

    def test_invalid_value_returns_str(self):
        assert percentage("bad") == "bad"


class TestOrdinal:
    def test_first(self):
        assert ordinal(1) == "1st"

    def test_second(self):
        assert ordinal(2) == "2nd"

    def test_third(self):
        assert ordinal(3) == "3rd"

    def test_fourth(self):
        assert ordinal(4) == "4th"

    def test_eleventh(self):
        assert ordinal(11) == "11th"

    def test_twelfth(self):
        assert ordinal(12) == "12th"

    def test_thirteenth(self):
        assert ordinal(13) == "13th"

    def test_twenty_first(self):
        assert ordinal(21) == "21st"

    def test_twenty_second(self):
        assert ordinal(22) == "22nd"

    def test_twenty_third(self):
        assert ordinal(23) == "23rd"

    def test_string_number(self):
        assert ordinal("5") == "5th"

    def test_none_returns_empty(self):
        assert ordinal(None) == ""

    def test_invalid_value_returns_str(self):
        assert ordinal("bad") == "bad"


class TestFilesize:
    def test_bytes(self):
        assert filesize(500) == "500.0 B"

    def test_kilobytes(self):
        assert filesize(1500) == "1.5 KB"

    def test_megabytes(self):
        assert filesize(1500000) == "1.4 MB"

    def test_gigabytes(self):
        assert filesize(1500000000) == "1.4 GB"

    def test_terabytes(self):
        assert filesize(1500000000000) == "1.4 TB"

    def test_none_returns_empty(self):
        assert filesize(None) == ""

    def test_invalid_value_returns_str(self):
        assert filesize("bad") == "bad"
