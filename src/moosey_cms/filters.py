"""
Jinja2 template filters for content management.
Usage: Import and register with Jinja2Templates environment.
"""

from datetime import datetime
from typing import Any
import re
import math

from .seo import seo_tags

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
    
    formatted = dt.strftime(f'%d{suffix} %b, %Y at %I:%M %p')
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


def relative_time(dt):
    """Format date as relative time (e.g., '2 hours ago', 'yesterday')"""
    if not dt:
        return ""
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 172800:
        return "yesterday"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} days ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def time_only(dt):
    """Format as time only '6:00 PM'"""
    if not dt:
        return ""
    formatted = dt.strftime('%I:%M %p')
    if formatted[0] == '0':
        formatted = formatted[1:]
    return formatted


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
        
        country_code = country_code.strip().upper()
        
        if len(country_code) == 2:
            alpha_2 = country_code
        elif len(country_code) == 3:
            country = pycountry.countries.get(alpha_3=country_code)
            alpha_2 = country.alpha_2 if country else None
        else:
            return ""
        
        if alpha_2 and len(alpha_2) == 2:
            return ''.join(chr(ord(c) + 127397) for c in alpha_2)
        
        return ""
    except (ImportError, LookupError, AttributeError):
        if len(country_code) == 2:
            country_code = country_code.upper()
            return ''.join(chr(ord(c) + 127397) for c in country_code)
        return ""


def country_name(country_code):
    """Convert country code (alpha-2 or alpha-3) to full name using pycountry"""
    if not country_code:
        return ""
    
    try:
        import pycountry
        
        country_code = country_code.strip().upper()
        
        if len(country_code) == 2:
            country = pycountry.countries.get(alpha_2=country_code)
        elif len(country_code) == 3:
            country = pycountry.countries.get(alpha_3=country_code)
        else:
            results = pycountry.countries.search_fuzzy(country_code)
            country = results[0] if results else None
        
        return country.name if country else country_code
    except ImportError:
        fallback = {
            'US': 'United States', 'GB': 'United Kingdom', 'CA': 'Canada',
            'AU': 'Australia', 'DE': 'Germany', 'FR': 'France', 'IT': 'Italy',
            'ES': 'Spain', 'JP': 'Japan', 'CN': 'China', 'IN': 'India',
            'BR': 'Brazil', 'MX': 'Mexico', 'KE': 'Kenya', 'NG': 'Nigeria',
            'ZA': 'South Africa', 'EG': 'Egypt', 'GH': 'Ghana', 'TZ': 'Tanzania',
        }
        return fallback.get(country_code.upper(), country_code)
    except (LookupError, AttributeError):
        return country_code


def language_name(language_code):
    """Convert language code (alpha-2 or alpha-3) to full name using pycountry"""
    if not language_code:
        return ""
    
    try:
        import pycountry
        
        language_code = language_code.strip().lower()
        
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
    except ImportError:
        fallback = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi', 'sw': 'Swahili',
        }
        return fallback.get(language_code.lower(), language_code)
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
                   'in', 'of', 'on', 'or', 'the', 'to', 'up', 'via'}
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        if i == 0 or i == len(words) - 1:
            result.append(word.capitalize())
        elif word.isupper() and len(word) > 1:
            result.append(word)
        elif word.lower() in small_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def excerpt(text, length=150, suffix='...'):
    """Create excerpt from text, breaking at sentence"""
    if not text or len(text) <= length:
        return text
    
    truncated = text[:length]
    last_period = truncated.rfind('.')
    last_question = truncated.rfind('?')
    last_exclamation = truncated.rfind('!')
    
    break_point = max(last_period, last_question, last_exclamation)
    
    if break_point > length * 0.6:
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
        'excerpt': excerpt,
        'smart_quotes': smart_quotes,
        'number_format': number_format,
        'percentage': percentage,
        'ordinal': ordinal,
        'filesize': filesize,
        'default_if_none': default_if_none,
        'yesno': yesno,
        'read_time':read_time
    }
    
    for name, func in filters_dict.items():
        jinja_env.filters[name] = func

    jinja_env.globals['seo'] = seo_tags
    
    return jinja_env