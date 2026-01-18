---
title: Features
description: Discover why Moosey CMS is the perfect choice for your next project.
date: 2026-01-21
---

## Why Choose Moosey?

Moosey isn't just another CMS. It's a **hybrid static-dynamic engine**. It combines the developer experience of a Static Site Generator (like Jekyll or Hugo) with the power of a live Python server.

### ⚡ 1. Hot Reloading
Change a template. Change a Markdown file. Change a CSS file.
**Boom.** The browser updates instantly without a full page refresh. We use WebSockets to inject changes directly into the DOM.

### 🎨 2. Smart Templating
Stop worrying about which template to use. Our **Waterfall Logic** figures it out:

1.  Look for specific file override (e.g., `features.html`)
2.  Look for folder-level layout
3.  Fallback to `page.html`

### 📝 3. Rich Content Support

We support GitHub Flavored Markdown and more out of the box.

#### Task Lists
Keep track of your deployment status directly in your docs:
- [x] Install Python 3.12
- [x] Install Moosey CMS
- [x] Configure `main.py`
- [ ] Deploy to production

#### Data Tables
Perfect for comparison or pricing pages.

| Feature | Moosey CMS | WordPress | Static Gen |
| :--- | :---: | :---: | :---: |
| **Database** | ❌ No | ✅ Yes | ❌ No |
| **Dynamic** | ✅ Yes | ✅ Yes | ❌ No |
| **Speed** | 🚀 Fast | 🐌 Slow | 🚀 Fast |
| **Python** | 🐍 Yes | 🐘 No | 🤷 Maybe |

#### Admonitions & Alerts
Call out important information to your users.

!!! tip "Pro Tip"
    You can use **Jinja2 variables** inside your Markdown content! 
    For example, this site is managed by: **{{ site_data.author }}**.

!!! warning "Heads Up"
    Because there is no database, all content must be committed to Git. This is a feature, not a bug!

### 🌍 4. Built-in SEO
We automatically generate:
*   OpenGraph Tags (Facebook/LinkedIn)
*   Twitter Cards
*   JSON-LD Structured Data
*   Canonical URLs

Just add `{{ seo() }}` to your base template and we handle the rest.