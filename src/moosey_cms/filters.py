"""
Jinja2 template filters for content management.
Usage: Import and register with Jinja2Templates environment.
"""

from datetime import date, datetime, time, timezone
from email.utils import format_datetime
from html import unescape
from typing import Any
from urllib.parse import urljoin
import hashlib
import logging
import math
import os
import re

from jinja2 import pass_context

import bleach
import minify_html as _html_minifier
from bs4 import BeautifulSoup

from .seo import seo_tags

log = logging.getLogger(__name__)

# ============================================================================
# DATE & TIME FILTERS
# ============================================================================

def fancy_date(dt):
    """Format date as '13th Jan, 2026 at 6:00 PM'"""
    if not dt:
        return ""
    
    day = dt.day
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    
    formatted = dt.strftime(f'%-d{suffix} %b, %Y at %I:%M %p')
    # Remove leading zero from hour if present
    parts = formatted.split('at ')
    if len(parts) == 2 and parts[1][0] == '0':
        formatted = parts[0] + 'at ' + parts[1][1:]
    return formatted


def short_date(dt):
    """Format date as 'Jan 13, 2026'"""
    if not dt:
        return ""
    return dt.strftime('%b %d, %Y')


def iso_date(dt):
    """Format date as '2026-01-13'"""
    if not dt:
        return ""
    return dt.strftime('%Y-%m-%d')


def relative_time(dt, showAgo=True):
    """Format date as relative time (e.g., '2 hours ago', 'yesterday')"""
    if not dt:
        return ""
    
    now = datetime.now()
    diff = now - dt

    ago = " ago" if showAgo else ""
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}{ago}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''}{ago}"
    elif seconds < 172800:
        return "yesterday"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} days ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''}{ago}"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''}{ago}"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''}{ago}"


def time_only(dt):
    """Format as time only '6:00 PM'"""
    if not dt:
        return ""
    formatted = dt.strftime('%I:%M %p')
    if formatted[0] == '0':
        formatted = formatted[1:]
    return formatted

def strptime(s, fmt):
    return  datetime.strptime(s, fmt)


def rfc822_date(value):
    """Format a date/datetime for RSS feeds."""
    if not value:
        return ""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, time.min)
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return str(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt, usegmt=True)
# ============================================================================
# CURRENCY FILTERS
# ============================================================================

def currency(value, code='USD', symbol='$'):
    """Format number as currency '$1,234.56' using pycountry for currency info"""
    if value is None:
        return ""
    
    try:
        value = float(value)
        
        try:
            import pycountry
            
            try:
                currency_obj = pycountry.currencies.get(alpha_3=code.upper())
                decimals = 0 if currency_obj and int(currency_obj.numeric) == 392 else 2
            except (LookupError, AttributeError):
                decimals = 2
        except ImportError:
            decimals = 0 if code.upper() == 'JPY' else 2
        
        symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CNY': '¥', 'INR': '₹', 'KES': 'KSh', 'NGN': '₦',
            'ZAR': 'R', 'AUD': 'A$', 'CAD': 'C$', 'CHF': 'Fr',
            'BRL': 'R$', 'MXN': '$', 'RUB': '₽', 'TRY': '₺',
            'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr', 'PLN': 'zł',
            'AED': 'د.إ', 'SAR': 'ر.س', 'EGP': 'E£', 'THB': '฿',
            'SGD': 'S$', 'HKD': 'HK$', 'KRW': '₩', 'IDR': 'Rp',
            'PHP': '₱', 'VND': '₫', 'MYR': 'RM', 'PKR': '₨',
        }
        
        symbol = symbols.get(code.upper(), symbol)
        
        if decimals == 0:
            formatted = f"{int(value):,}"
        else:
            formatted = f"{value:,.{decimals}f}"
        
        return f"{symbol}{formatted}"
    except (ValueError, TypeError):
        return str(value)


def compact_currency(value, code='USD'):
    """Format large numbers compactly '$1.2M', '$45K'"""
    if value is None:
        return ""
    
    try:
        value = float(value)
        
        symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CNY': '¥', 'INR': '₹', 'KES': 'KSh', 'NGN': '₦',
            'ZAR': 'R', 'AUD': 'A$', 'CAD': 'C$', 'CHF': 'Fr'
        }
        
        symbol = symbols.get(code.upper(), '$')
        
        if value >= 1_000_000_000:
            return f"{symbol}{value/1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"{symbol}{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{symbol}{value/1_000:.1f}K"
        else:
            return f"{symbol}{value:.2f}"
    except (ValueError, TypeError):
        return str(value)


# ============================================================================
# COUNTRY & LOCALE FILTERS
# ============================================================================

def country_flag(country_code):
    """Convert ISO 3166-1 alpha-2 or alpha-3 country code to emoji flag"""
    if not country_code:
        return ""
    
    try:
        import pycountry
    except ImportError:
        if len(country_code) == 2:
            country_code = country_code.upper()
            return ''.join(chr(ord(c) + 127397) for c in country_code)
        return ""
    
    country_code = country_code.strip().upper()
    
    try:
        if len(country_code) == 2:
            country = pycountry.countries.get(alpha_2=country_code)
            alpha_2 = country.alpha_2 if country else None
        elif len(country_code) == 3:
            country = pycountry.countries.get(alpha_3=country_code)
            alpha_2 = country.alpha_2 if country else None
        else:
            return ""
    except (LookupError, AttributeError):
        return ""
    
    if alpha_2 and len(alpha_2) == 2:
        return ''.join(chr(ord(c) + 127397) for c in alpha_2)
    
    return ""


def country_name(country_code):
    """Convert country code (alpha-2 or alpha-3) to full name using pycountry"""
    if not country_code:
        return ""
    
    country_code = country_code.strip().upper()
    
    try:
        import pycountry
    except ImportError:
        fallback = {
            'US': 'United States', 'GB': 'United Kingdom', 'CA': 'Canada',
            'AU': 'Australia', 'DE': 'Germany', 'FR': 'France', 'IT': 'Italy',
            'ES': 'Spain', 'JP': 'Japan', 'CN': 'China', 'IN': 'India',
            'BR': 'Brazil', 'MX': 'Mexico', 'KE': 'Kenya', 'NG': 'Nigeria',
            'ZA': 'South Africa', 'EG': 'Egypt', 'GH': 'Ghana', 'TZ': 'Tanzania',
        }
        return fallback.get(country_code, country_code)
    
    try:
        if len(country_code) == 2:
            country = pycountry.countries.get(alpha_2=country_code)
        elif len(country_code) == 3:
            country = pycountry.countries.get(alpha_3=country_code)
        else:
            results = pycountry.countries.search_fuzzy(country_code)
            country = results[0] if results else None
        
        return country.name if country else country_code
    except (LookupError, AttributeError):
        return country_code


def language_name(language_code):
    """Convert language code (alpha-2 or alpha-3) to full name using pycountry"""
    if not language_code:
        return ""
    
    language_code = language_code.strip().lower()
    
    try:
        import pycountry
    except ImportError:
        fallback = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi', 'sw': 'Swahili',
        }
        return fallback.get(language_code, language_code)
    
    try:
        if len(language_code) == 2:
            language = pycountry.languages.get(alpha_2=language_code)
        elif len(language_code) == 3:
            language = pycountry.languages.get(alpha_3=language_code)
            if not language:
                language = pycountry.languages.get(bibliographic=language_code)
        else:
            results = pycountry.languages.search_fuzzy(language_code)
            language = results[0] if results else None
        
        return language.name if language else language_code
    except (LookupError, AttributeError):
        return language_code


def currency_name(currency_code):
    """Convert currency code to full name using pycountry"""
    if not currency_code:
        return ""
    
    try:
        import pycountry
        
        currency = pycountry.currencies.get(alpha_3=currency_code.upper())
        return currency.name if currency else currency_code.upper()
    except ImportError:
        fallback = {
            'USD': 'US Dollar', 'EUR': 'Euro', 'GBP': 'Pound Sterling',
            'JPY': 'Yen', 'CNY': 'Yuan Renminbi', 'INR': 'Indian Rupee',
            'KES': 'Kenyan Shilling', 'NGN': 'Naira', 'ZAR': 'Rand',
        }
        return fallback.get(currency_code.upper(), currency_code.upper())
    except (LookupError, AttributeError):
        return currency_code.upper()


# ============================================================================
# TEXT FORMATTING FILTERS
# ============================================================================

def truncate_words(text, count=50, suffix='...'):
    """Truncate text to specified word count"""
    if not text:
        return ""
    
    words = text.split()
    if len(words) <= count:
        return text
    
    return ' '.join(words[:count]) + suffix


def reading_time(text, wpm=200):
    """Calculate reading time in minutes"""
    if not text:
        return "0 min read"
    
    word_count = len(text.split())
    minutes = max(1, round(word_count / wpm))
    
    return f"{minutes} min read"


def slugify(text):
    """Convert text to URL-friendly slug"""
    if not text:
        return ""
    
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def title_case(text):
    """Convert to title case, preserving acronyms"""
    if not text:
        return ""
    
    small_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 
                   'in', 'of', 'on', 'or', 'the', 'to', 'up', 'via', 'with'}
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        if word.isupper() and len(word) > 1:
            result.append(word)
        elif i == 0 or i == len(words) - 1:
            result.append(word.capitalize())
        elif word.lower() in small_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def _split_words(text):
    """Split on any delimiter or camelCase boundary"""
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    return re.split(r'[\s_\-]+', s)


def snake_case(text):
    """Convert to snake_case"""
    if not text:
        return ""
    return '_'.join(w.lower() for w in _split_words(text))


def kebab_case(text):
    """Convert to kebab-case"""
    if not text:
        return ""
    return '-'.join(w.lower() for w in _split_words(text))


def camel_case(text):
    """Convert to camelCase"""
    if not text:
        return ""
    words = _split_words(text)
    return words[0].lower() + ''.join(w.capitalize() for w in words[1:])


def pascal_case(text):
    """Convert to PascalCase"""
    if not text:
        return ""
    return ''.join(w.capitalize() for w in _split_words(text))


def upper_case(text):
    """Convert to UPPER CASE"""
    if not text:
        return ""
    return text.upper()


def lower_case(text):
    """Convert to lower case"""
    if not text:
        return ""
    return text.lower()


def excerpt(text, length=150, suffix='...'):
    """Create excerpt from text, breaking at sentence"""
    if not text:
        return ""
    if len(text) <= length:
        return text
    
    truncated = text[:length]
    last_period = truncated.rfind('.')
    last_question = truncated.rfind('?')
    last_exclamation = truncated.rfind('!')
    
    break_point = max(last_period, last_question, last_exclamation)
    
    if break_point >= length * 0.4:
        return text[:break_point + 1]
    else:
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + suffix
        return truncated + suffix


def smart_quotes(text):
    """Convert straight quotes to smart/curly quotes"""
    if not text:
        return ""
    
    text = re.sub(r'(\s|^)"', '\u201c', text)
    text = re.sub(r'"(\s|$|[,.;:!?])', '\u201d', text)
    text = re.sub(r"(\s|^)'", '\u2018', text)
    text = re.sub(r"'(\s|$|[,.;:!?])", '\u2019', text)
    
    return text


# ============================================================================
# NUMBER FORMATTING FILTERS
# ============================================================================

def number_format(value, decimals=0):
    """Format number with thousand separators"""
    if value is None:
        return ""
    
    try:
        value = float(value)
        if decimals == 0:
            return f"{int(value):,}"
        else:
            return f"{value:,.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


def percentage(value, decimals=1):
    """Format as percentage"""
    if value is None:
        return ""
    
    try:
        value = float(value)
        return f"{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)


def ordinal(value):
    """Convert number to ordinal (1st, 2nd, 3rd)"""
    if value is None:
        return ""
    
    try:
        value = int(value)
        if 10 <= value % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
        return f"{value}{suffix}"
    except (ValueError, TypeError):
        return str(value)


# ============================================================================
# FILE SIZE FILTERS
# ============================================================================

def filesize(bytes_value):
    """Format bytes as human-readable file size"""
    if bytes_value is None:
        return ""
    
    try:
        bytes_value = float(bytes_value)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        
        return f"{bytes_value:.1f} PB"
    except (ValueError, TypeError):
        return str(bytes_value)


# ============================================================================
# UTILITY FILTERS
# ============================================================================

def default_if_none(value, default=""):
    """Return default value if None"""
    return default if value is None else value


def yesno(value, yes="Yes", no="No"):
    """Convert boolean to yes/no text"""
    return yes if value else no

def read_time(text: str) -> str:
    if not text:
        return "0 min read"

    word_count = len(text.split())
    # Average reading speed is 200 wpm
    minutes = math.ceil(word_count / 200)
    if minutes <= 1:
        return "1 min read"
    return f"{minutes} min read"


@pass_context
def absolute_url(context, value, base_url=None):
    """Resolve a relative URL against site_data.web.site_url or request.base_url."""
    if not value:
        return ""
    value = str(value)
    if re.match(r"^[a-z][a-z0-9+.-]*:", value, re.IGNORECASE) or value.startswith("#"):
        return value

    request = context.get("request")
    site_data = context.get("site_data") or {}
    web = site_data.get("web", {}) if isinstance(site_data, dict) else {}
    base = (
        base_url
        or web.get("site_url")
        or site_data.get("site_url")
        or site_data.get("base_url")
        or (str(request.base_url) if request else "")
    )
    if not base:
        return value
    return urljoin(str(base).rstrip("/") + "/", value.lstrip("/"))


# ============================================================================
# MARKDOWN RENDERING
# ============================================================================

def markdown(text, inline=False):
    """
    Render a Markdown string to HTML using Moosey's configured renderer
    (tables, TOC, magic links, better emphasis, emoji, task lists,
    fenced code, sane headers, math, admonitions, and custom emoticons).

    Returns *raw HTML*. Jinja escapes it by default - pipe through ``safe``
    to inject it into the page. This is intentional, so you keep control
    over what gets injected.

    Usage:
        {{ bio | markdown | safe }}
        {{ "**Hi**" | markdown | safe }}

    Set ``inline=True`` to drop the wrapping ``<p>`` tags added by
    Python-Markdown for single-block content. Useful for short snippets
    inside titles, captions, or table cells:

        <h1>{{ title | markdown(inline=True) | safe }}</h1>

    Empty / None input returns an empty string so the filter is safe to
    call on missing frontmatter fields.
    """
    if not text:
        return ""

    from .md import parse_markdown
    html = parse_markdown(text)

    if inline and html.startswith("<p>") and html.endswith("</p>") \
            and html.count("<p>") == 1:
        html = html[3:-4]

    return html


# ============================================================================
# HTML UTILITIES
# ============================================================================

def strip_html(text):
    """Remove HTML tags/comments and collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r'<!--[\s\S]*?-->', '', str(text))
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def strip_comments(text, enabled=True):
    """
    Removes HTML comments from the output.
    Usage: {% filter strip_comments(enabled=True) %} ... {% endfilter %}
    """
    if not enabled or not text:
        return text
    
    # Regex: Matches <!-- followed by anything (including newlines) until -->
    # The *? ensures it is non-greedy (stops at the first closing tag)
    return re.sub(r'<!--[\s\S]*?-->', '', str(text))

def minify_html(
    text,
    enabled=True,
    keep_comments=True,
    minify_css=False,
    minify_js=False,
):
    """
    Minify rendered HTML while preserving whitespace-sensitive elements.
    """
    if not enabled or not text:
        return text

    text = str(text)

    try:
        return _html_minifier.minify(
            text,
            keep_closing_tags=True,
            keep_html_and_head_opening_tags=True,
            keep_input_type_text_attr=True,
            keep_comments=keep_comments,
            minify_css=minify_css,
            minify_js=minify_js,
        ).strip()
    except Exception as exc:
        log.debug("HTML minification failed; returning original HTML: %s", exc)
        return text

# ============================================================================
# SANITIZE - HTML allowlist (bleach, always on by default)
# ============================================================================

_DEFAULT_ALLOWED_TAGS = [
    "a", "abbr", "address", "article", "aside", "audio", "b", "bdi", "bdo",
    "blockquote", "br", "caption", "cite", "code", "col", "colgroup", "data",
    "dd", "del", "details", "dfn", "div", "dl", "dt", "em", "figcaption",
    "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hgroup",
    "hr", "i", "img", "ins", "kbd", "li", "mark", "nav", "ol", "p", "pre",
    "q", "rp", "rt", "ruby", "s", "samp", "section", "small", "source", "span",
    "strong", "sub", "summary", "sup", "table", "tbody", "td", "tfoot", "th",
    "thead", "time", "tr", "u", "ul", "var", "video", "wbr",
]

_DEFAULT_ALLOWED_ATTRS = {
    "*":          ["class", "id", "title", "lang", "dir", "translate"],
    "a":          ["href", "title", "rel", "target", "hreflang", "download"],
    "abbr":       ["title"],
    "blockquote": ["cite"],
    "del":        ["datetime", "cite"],
    "details":    ["open"],
    "img":        ["src", "alt", "title", "width", "height", "loading",
                  "decoding", "referrerpolicy", "srcset", "sizes", "fetchpriority"],
    "ins":        ["datetime", "cite"],
    "ol":         ["start", "reversed", "type"],
    "li":         ["value"],
    "q":          ["cite"],
    "time":       ["datetime"],
    "td":         ["colspan", "rowspan", "headers"],
    "th":         ["colspan", "rowspan", "headers", "scope", "abbr"],
    "video":      ["src", "controls", "width", "height", "poster", "preload",
                   "autoplay", "loop", "muted", "playsinline"],
    "audio":      ["src", "controls", "preload", "autoplay", "loop", "muted"],
    "source":     ["src", "type", "srcset", "sizes", "media"],
    "col":        ["span"],
    "colgroup":   ["span"],
    "data":       ["value"],
}

_DEFAULT_ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]
_DEFAULT_ALLOWED_STYLES: list = []


def sanitize(html, tags=None, attrs=None, protocols=None,
             styles=None, strip=True, strip_comments=True):
    """
    Run ``bleach.clean`` with sane CMS defaults.

    Always-on by pipeline (in ``template_render_content``); exposed as a manual
    filter for untrusted HTML coming from other sources.

    Inline CSS styles are disallowed by default. Pass ``styles`` as a list of
    allowed property names *and* install ``bleach[css]`` to honor them.

    Usage::

        {{ untrusted_html | sanitize | safe }}
    """
    kwargs = dict(
        tags=tags or _DEFAULT_ALLOWED_TAGS,
        attributes=attrs or _DEFAULT_ALLOWED_ATTRS,
        protocols=protocols or _DEFAULT_ALLOWED_PROTOCOLS,
        strip=strip,
        strip_comments=strip_comments,
    )
    # bleach 6 renamed `styles` to `css_sanitizer`. Inline styles are off by
    # default (None) which requires no extra dep. If the caller supplies a
    # styles allowlist, lazily build a CSSSanitizer behind bleach[css].
    if styles:
        try:
            from bleach.css_sanitizer import CSSSanitizer
            kwargs["css_sanitizer"] = CSSSanitizer(allowed_css_properties=styles)
        except ImportError:
            pass  # bleach[css] not installed; fall back to no styles
    return bleach.clean(html or "", **kwargs)


def get_sanitize_config(site_data: dict) -> dict | None:
    """Read ``site_data.sanitize`` and merge with defaults.

    Returns ``None`` for full opt-out (``sanitize: False``). Otherwise returns
    a dict with keys: ``auto`` (bool), ``bleach_kwargs`` (dict).
    """
    cfg = (site_data or {}).get("sanitize")
    if cfg is False:
        return None
    if cfg is None:
        cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}

    bleach_kwargs = {
        "tags": cfg.get("tags", _DEFAULT_ALLOWED_TAGS),
        "attrs": cfg.get("attrs", _DEFAULT_ALLOWED_ATTRS),
        "protocols": cfg.get("protocols", _DEFAULT_ALLOWED_PROTOCOLS),
        "strip": cfg.get("strip", False),
        "strip_comments": cfg.get("strip_comments", True),
    }
    styles = cfg.get("styles", _DEFAULT_ALLOWED_STYLES)
    return {"auto": cfg.get("auto", True),
            "styles": styles,
            "bleach_kwargs": bleach_kwargs}


# ============================================================================
# SEO & DATA HELPERS
# ============================================================================

@pass_context
def cache_bust(context, url, mode="mtime"):
    """Append cache-busting query string to a static asset URL.

    Resolves the file under the static dir on ``app.state`` and reads its
    mtime (default) or sha8 of file bytes. Falls back to the plain URL when
    the file can't be located (never raises).

    Usage::

        <link href="{{ '/static/site.css' | cache_bust }}" rel="stylesheet">
    """
    if not url:
        return ""
    request = context.get("request")
    if not request:
        return url
    static_dir = getattr(request.app.state, "moosey_static_dir", None)
    if not static_dir:
        return url
    path_part = url.split("?", 1)[0]
    try:
        rel = path_part.lstrip("/")
        if rel.startswith("static/"):
            rel = rel[len("static/"):]
        candidate = (static_dir / rel).resolve()
        candidate.relative_to(static_dir.resolve())
        if not candidate.is_file():
            return url
        if mode == "sha8":
            with open(candidate, "rb") as fh:
                val = hashlib.sha256(fh.read(2 ** 20)).hexdigest()[:8]
        else:
            val = str(int(candidate.stat().st_mtime))
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}v={val}"
    except Exception:
        return url


def pluralize(singular, count, plural=None):
    """Return ``singular`` if ``count == 1`` else ``plural`` (or singular+'s').

    Idiomatic in templates: ``{{ 'review' | pluralize(reviews_count) }}``.
    """
    if count == 1:
        return singular
    return plural if plural is not None else singular + "s"


def word_count(text):
    """Number of whitespace-separated words. Strips HTML if any present."""
    if not text:
        return 0
    if "<" in text and ">" in text:
        text = re.sub(r"<[^>]+>", " ", text)
    return len(text.split())


@pass_context
def inline(context, path, encode=None):
    """Inline a static asset's contents directly into the page.

    Looks the file up under ``app.state.moosey_static_dir``. Returns "" if not
    found. ``encode="data-uri"`` returns a ``data:<mime>;base64,…`` string.
    """
    if not path:
        return ""
    request = context.get("request")
    if not request:
        return ""
    static_dir = getattr(request.app.state, "moosey_static_dir", None)
    if not static_dir:
        return ""
    try:
        rel = path.lstrip("/")
        if rel.startswith("static/"):
            rel = rel[len("static/"):]
        candidate = (static_dir / rel).resolve()
        candidate.relative_to(static_dir.resolve())
        if not candidate.is_file():
            return ""
        with open(candidate, "rb") as fh:
            data = fh.read()
    except Exception:
        return ""

    if encode == "data-uri":
        import mimetypes
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        import base64
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{b64}"
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        import base64
        return f"data:application/octet-stream;base64,{base64.b64encode(data).decode('ascii')}"


# ============================================================================
# IMAGE FILTERS (forwarding wrappers around moosey_cms.images)
# ============================================================================

from .images import (
    image_url_filter as _image_url_filter,
    responsive_image_html as _responsive_image_html,
    image_dimensions_impl as _image_dimensions_impl,
    dominant_color_impl as _dominant_color_impl,
    image_cdn_impl as _image_cdn_impl,
)


def img_attrs(src, width=None, height=None, loading="lazy",
              decoding="async", referrerpolicy="no-referrer"):
    """Build ``src loading decoding width=… height=…`` attr string for ``<img>``."""
    if not src:
        return ""
    parts = [f'src="{src}"', f'loading="{loading}"',
             f'decoding="{decoding}"',
             f'referrerpolicy="{referrerpolicy}"']
    if width:
        parts.append(f'width="{width}"')
    if height:
        parts.append(f'height="{height}"')
    return " ".join(parts)


def lazy_image(html_or_src, attrs=False):
    """Inject lazy/async/referrerpolicy attrs. Detects ``<img`` vs bare src.

    With ``attrs=True`` (or given a bare src), returns an attr string rather
    than a full ``<img>`` tag - useful when you want to compose your own tag.
    """
    if not html_or_src:
        return ""
    s = str(html_or_src)
    if s.lstrip().lower().startswith("<img"):
        # Inject before the closing > of the opening tag.
        m = re.search(r"<img\b([^>]*)>", s, re.IGNORECASE)
        if not m:
            return s
        attrs_block = m.group(1)
        # Don't double-add if already present.
        additions = []
        if "loading=" not in attrs_block.lower():
            additions.append('loading="lazy"')
        if "decoding=" not in attrs_block.lower():
            additions.append('decoding="async"')
        if "referrerpolicy=" not in attrs_block.lower():
            additions.append('referrerpolicy="no-referrer"')
        if not additions:
            return s
        if attrs_block.endswith("/"):
            new_attrs = " " + " ".join(additions) + attrs_block
        else:
            new_attrs = attrs_block + " " + " ".join(additions)
        return s[:m.start(1)] + new_attrs + s[m.end(1):]
    # Bare src
    return img_attrs(s)


def image_dimensions(src):
    """Read width/height of a local image; returns ``width="…" height="…"``."""
    return _image_dimensions_impl(src)


@pass_context
def dominant_color(context, src, default="#0b172a"):
    """Most common hex color of a local image (for LQIP backgrounds)."""
    static_dir = getattr(context.get("request", None) and context["request"].app.state,
                         "moosey_static_dir", None)
    return _dominant_color_impl(src, default=default, static_dir=static_dir)


def image_cdn(src, **params):
    """Rewrite a path into a CDN transform URL (provider from site_data)."""
    # Provider/base_url are looked up lazily from site_data at call time.
    # We don't have context here, so this filter falls through to a thin wrapper
    # that uses the request-bound provider if available; otherwise "cloudflare".
    return _image_cdn_impl(src, **params)


@pass_context
def image_cdn_ctx(context, src, **params):
    """Context-aware CDN adapter honoring ``site_data.image_cdn``."""
    site_data = context.get("site_data") or {}
    cdn_cfg = site_data.get("image_cdn") or {}
    provider = cdn_cfg.get("provider", "cloudflare")
    base_url = cdn_cfg.get("base_url")
    return _image_cdn_impl(src, provider=provider, base_url=base_url, **params)


@pass_context
def image(context, src, widths=None, sizes="100vw",
          loading="lazy", decoding="async", **params):
    """Unified image filter.

    Without ``widths`` → returns a URL string (for ``img src=...``).
    With ``widths``    → returns a full ``<img srcset sizes>`` HTML tag.
    """
    request = context.get("request")
    route = (getattr(request.app.state, "moosey_image_route_prefix", None)
             if request else None) or "/__moosey/img/"
    if widths:
        return _responsive_image_html(
            src, _route_prefix=route, widths=widths, sizes=sizes,
            loading=loading, decoding=decoding, **params
        )
    return _image_url_filter(src, _route_prefix=route, **params)


@pass_context
def image_url(context, src, **params):
    """Deprecated - use ``image`` instead."""
    if not src:
        return ""
    import warnings as _w
    _w.warn("image_url() is deprecated, use image() instead",
            DeprecationWarning, stacklevel=2)
    return image(context, src, **params)


@pass_context
def responsive_image(context, src, widths=(400, 800, 1200, 1600),
                     sizes="100vw", loading="lazy", decoding="async",
                     **shared):
    """Deprecated - use ``image`` instead."""
    import warnings as _w
    _w.warn("responsive_image() is deprecated, use image() instead",
            DeprecationWarning, stacklevel=2)
    return image(context, src, widths=widths, sizes=sizes,
                 loading=loading, decoding=decoding, **shared)


# ============================================================================
# CONTENT HELPERS (embed, headings, toc_from_html, gravatar)
# ============================================================================

import hashlib as _hashlib  # ensure available; was imported above
from urllib.parse import quote as _quote

_OEMBED_PROVIDERS = {
    # provider key: regex; builder function name in dict below
}


def _yt_embed(url):
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|v/))([\w-]{11})", url)
    if not m:
        return None
    vid = m.group(1)
    return (f'<iframe src="https://www.youtube.com/embed/{vid}" '
            f'width="480" height="270" frameborder="0" allowfullscreen '
            f'loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>')


def _vimeo_embed(url):
    m = re.search(r"vimeo\.com/(\d+)", url)
    if not m:
        return None
    vid = m.group(1)
    return (f'<iframe src="https://player.vimeo.com/video/{vid}" '
            f'width="480" height="270" frameborder="0" allowfullscreen '
            f'loading="lazy" referrerpolicy="no-referrer"></iframe>')


def _twitter_embed(url):
    if re.match(r"https?://(?:www\.)?(twitter|x)\.com/[^/]+/status/(\d+)", url):
        return (f'<blockquote class="twitter-tweet" data-dnt="true">'
                f'<a href="{url}">{url}</a></blockquote>'
                f'<script async src="https://platform.twitter.com/widgets.js" '
                f'charset="utf-8"></script>')
    return None


def _gist_embed(url):
    m = re.match(r"https?://gist\.github\.com/([^/]+/[\w-]+)", url)
    if not m:
        return None
    return (f'<script src="https://gist.github.com/{m.group(1)}.js"></script>')


def _codepen_embed(url):
    m = re.match(r"https?://codepen\.io/([^/]+)/pen/([\w-]+)", url)
    if not m:
        return None
    return (f'<p class="codepen" data-default-tab="result">'
            f'<a href="{url}">See the Pen</a></p>'
            f'<script async src="https://static.codepen.io/assets/embed/ei.js"></script>')


_EMBED_BUILDERS = (_yt_embed, _vimeo_embed, _twitter_embed, _gist_embed, _codepen_embed)


def embed(url, maxwidth=480, maxheight=360):
    """oEmbed-lite: convert a known video/social/gist URL into embed HTML.

    Falls back to a plain ``<a href="url">url</a>`` if the provider is unknown
    or no network call is made (we use static substring transforms; no external
    oEmbed API calls - so the result is offline-cacheable for ≥24h).
    """
    if not url:
        return ""
    for builder in _EMBED_BUILDERS:
        out = builder(url)
        if out:
            return out
    return f'<a href="{url}">{url}</a>'


def headings(html, min_level=2, max_level=4):
    """Extract ``[(id, text, level), ...]`` from rendered HTML."""
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []
    out = []
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        level = int(h.name[1])
        if level < min_level or level > max_level:
            continue
        hid = h.get("id", "")
        text = h.get_text(strip=True)
        out.append((hid, text, level))
    return out


def toc_from_html(html, min_level=2, max_level=4, klass="prose-toc"):
    """Render a ``<nav class="…"><ul>…</ul></nav>`` of headings in ``html``."""
    items = headings(html, min_level=min_level, max_level=max_level)
    if not items:
        return ""
    parts = [f'<nav class="{klass}"><ul>']
    for hid, text, level in items:
        indent = "  " * (level - min_level)
        href = f"#{hid}" if hid else "#"
        parts.append(f'{indent}<li class="toc-level-{level}"><a href="{href}">{text}</a></li>')
    parts.append("</ul></nav>")
    return "\n".join(parts)


def gravatar(email, size=80, default="404", rating="g"):
    """Return a Gravatar URL for ``email`` (md5-hashed, no network call)."""
    if not email:
        return ""
    digest = _hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
    return (f"https://www.gravatar.com/avatar/{digest}"
            f"?s={size}&d={_quote(str(default))}&r={rating}")


# ============================================================================
# REGISTRATION FUNCTION
# ============================================================================

def register_filters(jinja_env):
    """
    Register all filters with a Jinja2 environment.
    
    Usage:
        from fastapi.templating import Jinja2Templates
        from . import filters
        
        templates = Jinja2Templates(directory="templates")
        filters.register_filters(templates.env)
    """
    filters_dict = {
        'fancy_date': fancy_date,
        'short_date': short_date,
        'iso_date': iso_date,
        'relative_time': relative_time,
        'strptime': strptime,
        'rfc822_date': rfc822_date,
        'time_only': time_only,
        'currency': currency,
        'compact_currency': compact_currency,
        'country_flag': country_flag,
        'country_name': country_name,
        'language_name': language_name,
        'currency_name': currency_name,
        'truncate_words': truncate_words,
        'reading_time': reading_time,
        'slugify': slugify,
        'title_case': title_case,
        'snake_case': snake_case,
        'kebab_case': kebab_case,
        'camel_case': camel_case,
        'pascal_case': pascal_case,
        'upper_case': upper_case,
        'lower_case': lower_case,
        'excerpt': excerpt,
        'smart_quotes': smart_quotes,
        'number_format': number_format,
        'percentage': percentage,
        'ordinal': ordinal,
        'filesize': filesize,
        'default_if_none': default_if_none,
        'yesno': yesno,
        'read_time':read_time,
        'absolute_url': absolute_url,
        'strip_html': strip_html,
        'strip_comments': strip_comments,
        'minify_html': minify_html,
        'markdown': markdown,
        # Sanitize
        'sanitize': sanitize,
        # SEO & data
        'cache_bust': cache_bust,
        'pluralize': pluralize,
        'word_count': word_count,
        'inline': inline,
        # Images
        'img_attrs': img_attrs,
        'lazy_image': lazy_image,
        'image_dimensions': image_dimensions,
        'dominant_color': dominant_color,
        'image_cdn': image_cdn_ctx,
        'image': image,
        'image_url': image_url,
        'responsive_image': responsive_image,
        # Content helpers
        'embed': embed,
        'headings': headings,
        'toc_from_html': toc_from_html,
        'gravatar': gravatar,

    }
    
    for name, func in filters_dict.items():
        jinja_env.filters[name] = func

    jinja_env.globals['seo'] = seo_tags
    
    return jinja_env
