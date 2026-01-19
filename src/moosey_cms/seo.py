"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

from jinja2 import pass_context
from markupsafe import Markup, escape
from typing import Optional


@pass_context
def seo_tags(
    context,
    title: Optional[str] = None,
    description: Optional[str] = None,
    image: Optional[str] = None,
    canonical_url: Optional[str] = None,
    keywords: Optional[str] = None,
    author: Optional[str] = None,
    publish_date: Optional[str] = None,  # ISO 8601 format YYYY-MM-DD
    noindex: bool = False,
):
    """
    Renders full suite of SEO, OpenGraph, and Twitter Card meta tags.
    """
    request = context.get("request")
    app = request.app

    site_data = app.state.site_data

    site_name = site_data.get("name")
    site_keywords = site_data.get("keywords")
    site_social = site_data.get("social")
    open_graph = site_data.get("open_graph")

    if site_social and len(site_social.keys()) > 0:
        twitter_handle = site_social["twitter"] if "twitter" in site_social else None

    if open_graph:
        og_image = open_graph["og_image"] if "og_image" in open_graph else None

    # 1. Resolve Data (Priority: Explicit Arg > Context Variable > Default)
    meta_title = title or context.get("title") or site_name
    meta_desc = description or context.get("description") or ""
    meta_author = author or context.get("author") or site_name
    meta_keywords = (
        keywords or context.get("keywords") or site_keywords or context.get("tags")
    )

    meta_keywords = (
        ", ".join(meta_keywords)
        if isinstance(meta_keywords, list)
        else str(meta_keywords)
    )

    # 2. Handle URLs (Absolute URLs are required for SEO/Social)
    base_url = str(request.base_url).rstrip("/") if request else ""

    # Resolve Image
    meta_image = None
    if og_image:

        raw_image = image or context.get("image") or og_image
        if raw_image and raw_image.startswith("http"):
            meta_image = raw_image
        else:
            # Ensure path starts with /
            if not raw_image.startswith("/"):
                raw_image = "/" + raw_image
            meta_image = f"{base_url}{raw_image}"

    # Resolve Current URL & Canonical
    current_url = str(request.url) if request else ""
    final_canonical = canonical_url or current_url

    # 3. Determine Content Type
    # If a publish date exists, Google treats it as an Article
    og_type = "article" if publish_date else "website"

    # 4. Build Tags List
    tags = []

    # --- Standard SEO ---
    tags.append(f"<title>{escape(meta_title)}</title>")
    tags.append(f'<meta name="description" content="{escape(meta_desc)}">')
    if meta_keywords:
        tags.append(f'<meta name="keywords" content="{escape(meta_keywords)}">')
    tags.append(f'<meta name="author" content="{escape(meta_author)}">')
    tags.append(f'<link rel="canonical" href="{final_canonical}">')

    # Robots (Block indexing if needed, e.g., for search results pages)
    if noindex:
        tags.append('<meta name="robots" content="noindex, nofollow">')
    else:
        tags.append('<meta name="robots" content="index, follow">')

    # --- Open Graph (Facebook/LinkedIn) ---
    if site_name:
        tags.append(f'<meta property="og:site_name" content="{site_name}">')

    tags.append(f'<meta property="og:type" content="{og_type}">')
    tags.append(f'<meta property="og:title" content="{escape(meta_title)}">')
    tags.append(f'<meta property="og:description" content="{escape(meta_desc)}">')
    tags.append(f'<meta property="og:url" content="{current_url}">')

    if meta_image:
        tags.append(f'<meta property="og:image" content="{meta_image}">')

    # --- Twitter Cards ---

    tags.append('<meta name="twitter:card" content="summary_large_image">')
    tags.append(f'<meta name="twitter:site" content="{twitter_handle}">')
    tags.append(f'<meta name="twitter:title" content="{escape(meta_title)}">')
    tags.append(f'<meta name="twitter:description" content="{escape(meta_desc)}">')

    if meta_image:
        tags.append(f'<meta name="twitter:image" content="{meta_image}">')

    # --- Article Specifics ---
    if publish_date:
        tags.append(
            f'<meta property="article:published_time" content="{publish_date}">'
        )
        tags.append(f'<meta property="article:author" content="{escape(meta_author)}">')

    # --- JSON-LD Structured Data (The "Pro" Touch) ---
    # This helps Google understand the page structure explicitly
    json_ld_type = "Article" if og_type == "article" else "WebSite"
    json_ld = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "{json_ld_type}",
      "headline": "{escape(meta_title)}",
      "image": "{meta_image}",
      "author": {{
        "@type": "Person",
        "name": "{escape(meta_author)}"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "{site_name}"
      }},
      "description": "{escape(meta_desc)}"
      {f', "datePublished": "{publish_date}"' if publish_date else ''}
    }}
    </script>
    """
    tags.append(json_ld.strip())

    return Markup("\n    ".join(tags))
