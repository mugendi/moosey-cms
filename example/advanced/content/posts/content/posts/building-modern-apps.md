---
title: Building Modern Apps with FastAPI and {{site_data.name}}
date: 2026-01-15
image: https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&q=80
tags: [fastapi, python, architecture]
---

FastAPI has taken the Python world by storm. In this post, we explore why it is the superior choice for modern web development.

## Why Async Matters

In the old days of WSGI, workers were blocked.

```python
# Old way
def sync_worker():
    time.sleep(5)
    return "Done"
```

With **ASGI**, we can handle thousands of concurrent connections.

> "FastAPI is one of the fastest Python frameworks available." - Benchmarks

### Key Features

1.  **Type Hints:** Validate data automatically.
2.  **Performance:** Rivals NodeJS and Go.
3.  **Standards:** Based on OpenAPI and JSON Schema.

Let's look at a table of comparison:

| Feature | Flask | FastAPI |
| :--- | :--- | :--- |
| Async | Add-on | Native |
| Validation | Extension | Native |
| Doc Gen | Extension | Native |

### Conclusion

Switching to FastAPI is a no-brainer for data-intensive applications.
```

#### `content/pages/about.md`
A standard page.

```markdown
---
title: About Us
description: We are a team of digital nomads building tools for creators.
---

## Our Mission

We believe that content management should be simple, fast, and fun. We stripped away the databases, the complicated dashboards, and the plugin hell to bring you **Moosey CMS**.

### The Team

![Office](https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&q=80)

We are a distributed team working from 4 different continents.

*   **Anthony:** Lead Developer
*   **Sarah:** Design System
*   **Mike:** Devops
```

### 3. Usage

1.  Ensure your `main.py` points `CONTENT_DIR` to `public/content` and `TEMPLATES_DIR` to `public/templates`.
2.  Run `uv run uvicorn main:app --reload`.
3.  Visit `http://localhost:8000`.

You will see a fully responsive, styled website with a Hero homepage, a Blog index with featured layouts, and beautiful typography for articles.