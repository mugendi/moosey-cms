# Patterns & Project Structure

Real-world conventions for organizing moosey-cms projects.

## Example Site Structure

```
mysite/
├── content/
│   ├── index.md              # Homepage
│   ├── about.md              # About page
│   ├── blog/
│   │   ├── first-post.md
│   │   └── second-post.md
│   └── projects/
│       ├── project-a.md
│       └── project-b.md
├── templates/
│   ├── base.html             # Base layout
│   ├── index.html            # Homepage template
│   ├── page.html             # Default page template
│   ├── blog.html             # Blog listing
│   └── partials/
│       ├── header.html
│       ├── footer.html
│       └── card.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── data/
│   └── team.yaml             # Custom data files
├── overrides/
│   └── index.html            # Template override
└── pyproject.toml
```

## Path Convention

Content paths match their URLs automatically:

| File | URL |
|------|-----|
| `content/index.md` | `/` |
| `content/about.md` | `/about` |
| `content/blog/first-post.md` | `/blog/first-post` |

## Templates

Templates live in the `templates/` directory and use Jinja2 syntax.

- `base.html` — shared layout with blocks for child templates to override
- Template names correspond to page types or explicit `template` frontmatter
- Partials in `templates/partials/` included via `{% include "partials/header.html" %}`

## Static Files

Place assets in `static/`:

```toml
[tool.moosey-cms]
dirs.static = "static"
```

Referenced automatically:

```jinja2
<link rel="stylesheet" href="{{ static('css/style.css') }}">
```

## Data Files

YAML or JSON files in `data/` are accessible as `{{ data.filename.key }}` in templates:

```yaml
# data/team.yaml
members:
  - name: Alice
    role: Developer
```

```jinja2
{% for member in data.team.members %}
  <li>{{ member.name }} — {{ member.role }}</li>
{% endfor %}
```

## Template Overrides

Place custom templates in `overrides/` to replace built-in rendering:

```
overrides/
├── index.html              # Override homepage template
└── blog.html               # Override blog listing
```

moosey-cms checks `overrides/` before falling back to the default template lookup.

## Custom Pages

Define extra pages beyond the content directory:

```toml
[tool.moosey-cms.pages]
archive = { template = "archive.html", paginate = { items = "data.team.members", per_page = 10 } }
```

This renders `archive.html` at `/archive` with pagination over the team members data.
