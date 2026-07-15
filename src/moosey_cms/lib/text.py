"""
Text utilities for Moosey CMS.
"""
import re
from datetime import date, datetime, time, timezone
from email.utils import format_datetime
from html import unescape
from typing import Any, Optional


def plain_text(value: str) -> str:
    """Convert HTML or Markdown-ish text into collapsed plain text."""
    if not value:
        return ""
    text = re.sub(r"<!--[\s\S]*?-->", "", str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    continue
    return None


def format_rfc822_date(value: Any) -> str:
    parsed = _coerce_datetime(value)
    if not parsed:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return format_datetime(parsed, usegmt=True)
