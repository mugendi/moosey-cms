from moosey_cms.filters import (
    truncate_words, reading_time, slugify, title_case,
    excerpt, smart_quotes, read_time, word_count,
)


class TestTruncateWords:
    def test_within_limit(self):
        text = "one two three"
        assert truncate_words(text, count=5) == text

    def test_over_limit(self):
        text = "one two three four five six"
        assert truncate_words(text, count=3) == "one two three..."

    def test_custom_suffix(self):
        text = "a b c d e"
        assert truncate_words(text, count=2, suffix=" [more]") == "a b [more]"

    def test_empty_returns_empty(self):
        assert truncate_words("") == ""

    def test_none_returns_empty(self):
        assert truncate_words(None) == ""


class TestReadingTime:
    def test_short_text(self):
        assert reading_time("hello world") == "1 min read"

    def test_long_text(self):
        words = " ".join(["word"] * 400)
        assert reading_time(words) == "2 min read"

    def test_custom_wpm(self):
        words = " ".join(["word"] * 400)
        assert reading_time(words, wpm=400) == "1 min read"

    def test_empty_returns_zero(self):
        assert reading_time("") == "0 min read"

    def test_none_returns_zero(self):
        assert reading_time(None) == "0 min read"


class TestReadTime:
    def test_short_text(self):
        assert read_time("hello world") == "1 min read"

    def test_long_text(self):
        words = " ".join(["word"] * 400)
        assert read_time(words) == "2 min read"

    def test_empty_returns_zero(self):
        assert read_time("") == "0 min read"


class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("Hello! World?") == "hello-world"

    def test_multiple_spaces(self):
        assert slugify("hello   world") == "hello-world"

    def test_trailing_dashes(self):
        assert slugify("hello-") == "hello"

    def test_empty_returns_empty(self):
        assert slugify("") == ""

    def test_none_returns_empty(self):
        assert slugify(None) == ""


class TestTitleCase:
    def test_basic(self):
        assert title_case("hello world") == "Hello World"

    def test_small_words_mid_sentence(self):
        assert title_case("a tale of two cities") == "A Tale of Two Cities"

    def test_acronyms_preserved(self):
        assert title_case("working with HTML and CSS") == "Working with HTML and CSS"

    def test_first_and_last_capitalized(self):
        assert title_case("the lord of the rings") == "The Lord of the Rings"

    def test_empty_returns_empty(self):
        assert title_case("") == ""

    def test_none_returns_empty(self):
        assert title_case(None) == ""


class TestExcerpt:
    def test_shorter_than_length(self):
        text = "Short text."
        assert excerpt(text, length=50) == text

    def test_break_at_sentence(self):
        text = "First sentence. Second sentence. Third sentence."
        assert excerpt(text, length=30) == "First sentence."

    def test_break_at_question_mark(self):
        text = "What is this? I don't know."
        result = excerpt(text, length=20)
        assert result == "What is this?"

    def test_fallback_to_word_break(self):
        text = "a " * 100
        result = excerpt(text.strip(), length=50)
        assert result.endswith("...")

    def test_none_returns_empty(self):
        assert excerpt(None) == ""


class TestSmartQuotes:
    def test_double_quotes(self):
        result = smart_quotes('He said "hello"')
        assert "\u201c" in result
        assert "\u201d" in result

    def test_single_quotes(self):
        result = smart_quotes("It's a test")
        assert "\u2018" in result
        assert "\u2019" in result

    def test_already_smart_unchanged(self):
        text = "Hello \u201cworld\u201d"
        assert smart_quotes(text) == text

    def test_empty_returns_empty(self):
        assert smart_quotes("") == ""

    def test_none_returns_empty(self):
        assert smart_quotes(None) == ""


class TestWordCount:
    def test_basic(self):
        assert word_count("hello world") == 2

    def test_html_stripped(self):
        assert word_count("<p>hello world</p>") == 2

    def test_empty_returns_zero(self):
        assert word_count("") == 0

    def test_none_returns_zero(self):
        assert word_count(None) == 0
