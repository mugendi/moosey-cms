"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

"""
JSON-LD structured data helpers for Moosey CMS.

`json_ld` is the single primitive filter that renders a Python dict into a
``<script type="application/ld+json">…</script>`` block. The ``schema_*``
builders are convenience helpers that return dicts ready to pipe into
``json_ld``. Users can bypass every builder and pass their own dict.
"""

import json
from typing import Any, Dict, List, Optional, Union

from markupsafe import Markup


def json_ld(data: Dict[str, Any], indent: int = 2) -> str:
    """Render ``data`` as a JSON-LD ``<script>`` block.

    Properly escapes ``</`` (prevents premature script closure) and the
    Unicode line/paragraph separators that break some HTML parsers. Output
    is :class:`markupsafe.Markup` so it is auto-safe in Jinja.

    Usage::

        {{ schema_article(title="X") | json_ld | safe }}
        {{ {"@type": "Thing", "name": "Custom"} | json_ld | safe }}
    """
    if not isinstance(data, dict):
        return Markup("")

    payload = json.dumps(
        data,
        indent=indent,
        ensure_ascii=False,
        sort_keys=False,
        default=str,
    )
    # Prevent ``</script>`` breakout attacks.
    payload = payload.replace("</", "<\\/")
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return Markup(f'<script type="application/ld+json">\n{payload}\n</script>')


# ---------------------------------------------------------------------------
# Schema builders
# ---------------------------------------------------------------------------

def schema_article(
    title: str,
    description: Optional[str] = None,
    image: Optional[str] = None,
    author: Optional[str] = None,
    date_published: Optional[str] = None,
    date_modified: Optional[str] = None,
    url: Optional[str] = None,
    *,
    keywords: Optional[Union[str, List[str]]] = None,
    in_language: Optional[str] = None,
    article_section: Optional[str] = None,
    article_body: Optional[str] = None,
    word_count: Optional[int] = None,
    speakable: Optional[List[str]] = None,
    backstory: Optional[str] = None,
    date_created: Optional[str] = None,
    publisher: Optional[Union[str, Dict[str, Any]]] = None,
    comment_count: Optional[int] = None,
    about: Optional[Union[str, List[str]]] = None,
    abstract: Optional[str] = None,
    alternative_headline: Optional[str] = None,
    genre: Optional[Union[str, List[str]]] = None,
    license: Optional[str] = None,
    is_part_of: Optional[Dict[str, str]] = None,
    is_accessible_for_free: Optional[bool] = None,
    copyright_year: Optional[int] = None,
    copyright_holder: Optional[Union[str, Dict[str, Any]]] = None,
    discussion_url: Optional[str] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
    }
    if description: out["description"] = description
    if image: out["image"] = image
    if author: out["author"] = {"@type": "Person", "name": author}
    if date_published: out["datePublished"] = date_published
    if date_modified: out["dateModified"] = date_modified
    if url: out["mainEntityOfPage"] = {"@type": "WebPage", "@id": url}

    if keywords: out["keywords"] = ", ".join(keywords) if isinstance(keywords, list) else keywords
    if in_language: out["inLanguage"] = in_language
    if article_section: out["articleSection"] = article_section
    if article_body: out["articleBody"] = article_body
    if word_count is not None:
        out["wordCount"] = word_count
    elif article_body:
        out["wordCount"] = len(article_body.split())
    if speakable: out["speakable"] = {"@type": "SpeakableSpecification", "cssSelector": speakable}
    if backstory: out["backstory"] = backstory
    if date_created: out["dateCreated"] = date_created
    if publisher:
        if isinstance(publisher, str):
            out["publisher"] = {"@type": "Organization", "name": publisher}
        else:
            obj = {"@type": "Organization", **publisher}
            out["publisher"] = obj
    if comment_count is not None: out["commentCount"] = comment_count
    if about: out["about"] = ", ".join(about) if isinstance(about, list) else about
    if abstract: out["abstract"] = abstract
    if alternative_headline: out["alternativeHeadline"] = alternative_headline
    if genre: out["genre"] = ", ".join(genre) if isinstance(genre, list) else genre
    if license: out["license"] = license
    if is_part_of:
        obj = dict(is_part_of)
        obj.setdefault("@type", "WebPage")
        out["isPartOf"] = obj
    if is_accessible_for_free is not None: out["isAccessibleForFree"] = is_accessible_for_free
    if copyright_year is not None: out["copyrightYear"] = copyright_year
    if copyright_holder:
        if isinstance(copyright_holder, str):
            out["copyrightHolder"] = {"@type": "Organization", "name": copyright_holder}
        else:
            obj = {"@type": "Person", **copyright_holder}
            out["copyrightHolder"] = obj
    if discussion_url: out["discussionUrl"] = discussion_url
    return out


def schema_breadcrumbs(items: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": it.get("name", ""),
                "item": it.get("url", ""),
            }
            for i, it in enumerate(items)
        ],
    }


def schema_faqpage(faqs: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f.get("answer", ""),
                },
            }
            for f in faqs
        ],
    }


def schema_howto(
    name: str,
    steps: List[Dict[str, str]],
    description: Optional[str] = None,
    image: Optional[str] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": name,
        "step": [
            {
                "@type": "HowToStep",
                "position": i + 1,
                "name": s.get("name", ""),
                "text": s.get("text", ""),
            }
            for i, s in enumerate(steps)
        ],
    }
    if description: out["description"] = description
    if image: out["image"] = image
    return out


def schema_localbusiness(
    name: str,
    url: str,
    telephone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[Dict[str, str]] = None,
    hours: Optional[List[Dict[str, Any]]] = None,
    image: Optional[str] = None,
    same_as: Optional[List[str]] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": name,
        "url": url,
    }
    if telephone: out["telephone"] = telephone
    if email: out["email"] = email
    if address:
        a = dict(address)
        a.setdefault("@type", "PostalAddress")
        out["address"] = a
    if hours:
        out["openingHoursSpecification"] = [
            {"@type": "OpeningHoursSpecification", **h} for h in hours
        ]
    if image: out["image"] = image
    if same_as: out["sameAs"] = same_as
    return out


def schema_product(
    name: str,
    image: Optional[str] = None,
    description: Optional[str] = None,
    sku: Optional[str] = None,
    price: Optional[float] = None,
    currency: Optional[str] = None,
    availability: Optional[str] = None,
    rating: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
    }
    if image: out["image"] = image
    if description: out["description"] = description
    if sku: out["sku"] = sku
    if price is not None and currency:
        out["offers"] = {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": currency,
        }
        if availability:
            out["offers"]["availability"] = availability
    if rating:
        out["aggregateRating"] = {
            "@type": "AggregateRating",
            **rating,
        }
    return out


def schema_event(
    name: str,
    start_date: str,
    end_date: Optional[str] = None,
    location: Optional[Dict[str, str]] = None,
    url: Optional[str] = None,
    image: Optional[str] = None,
    organizer: Optional[str] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": name,
        "startDate": start_date,
    }
    if end_date: out["endDate"] = end_date
    if location:
        l = dict(location)
        l.setdefault("@type", "Place")
        out["location"] = l
    if url: out["url"] = url
    if image: out["image"] = image
    if organizer: out["organizer"] = {"@type": "Organization", "name": organizer}
    return out


def schema_organization(
    name: str,
    url: str,
    logo: Optional[str] = None,
    same_as: Optional[List[str]] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
        "url": url,
    }
    if logo:
        out["logo"] = {"@type": "ImageObject", "url": logo}
    if same_as:
        out["sameAs"] = same_as
    return out


def schema_website(
    name: str,
    url: str,
    publisher: Optional[str] = None,
    potential_action: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": name,
        "url": url,
    }
    if publisher: out["publisher"] = {"@type": "Organization", "name": publisher}
    if potential_action: out["potentialAction"] = potential_action
    return out


def schema_person(
    name: str,
    url: Optional[str] = None,
    job_title: Optional[str] = None,
    image: Optional[str] = None,
    same_as: Optional[List[str]] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": name,
    }
    if url: out["url"] = url
    if job_title: out["jobTitle"] = job_title
    if image: out["image"] = image
    if same_as: out["sameAs"] = same_as
    return out


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_BUILDERS = {
    "schema_article": schema_article,
    "schema_breadcrumbs": schema_breadcrumbs,
    "schema_faqpage": schema_faqpage,
    "schema_howto": schema_howto,
    "schema_localbusiness": schema_localbusiness,
    "schema_product": schema_product,
    "schema_event": schema_event,
    "schema_organization": schema_organization,
    "schema_website": schema_website,
    "schema_person": schema_person,
}


def register(jinja_env) -> None:
    """Register the ``json_ld`` filter and every ``schema_*`` global on env."""
    jinja_env.filters["json_ld"] = json_ld
    for name, fn in _BUILDERS.items():
        jinja_env.globals[name] = fn