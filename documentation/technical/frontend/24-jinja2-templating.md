# Jinja2 Templating

How Jinja2 powers the templates — the syntax, the Python-side setup, the complete variable reference, and how to debug template errors.

---

## Overview

All three templates (email, edition, archive) are rendered by Python code using Jinja2. The rendering happens in three files:

| Template | Rendered In |
|----------|-------------|
| `templates/email.html` | `format_email.py:render_email()` |
| `templates/edition.html` | `format_page.py:render_page()` |
| `templates/archive.html` | `publish_github.py:_render_archive()` |

Each renderer creates a Jinja2 `Environment` pointing to the `daily_ai_digest/templates` package, then calls `.render()` with the data the template expects.

---

## Jinja2 Setup in Python

### Package Loader

```python
from jinja2 import Environment, PackageLoader

# Load templates from the daily_ai_digest/templates package
env = Environment(loader=PackageLoader("daily_ai_digest", "templates"))

# Get a specific template
template = env.get_template("edition.html")

# Render with data
html = template.render(
    date="January 30, 2026",
    vol="III",
    ...
)
```

**Why PackageLoader?** It finds templates inside the installed Python package. This works whether running locally or on Prefect Cloud — the package is always installed. File-based loaders (`FileSystemLoader`) would break on Prefect Cloud because the working directory is the cloned repo, not the package directory.

---

## Jinja2 Syntax Reference

### Variables

```jinja2
{{ variable }}            {# Simple variable output #}
{{ item.title }}          {# Attribute access #}
{{ dict['key'] }}         {# Dictionary access #}
{{ item.title | upper }}  {# Filter application #}
```

### Conditionals

```jinja2
{% if condition %}
    <p>Rendered if true</p>
{% elif other_condition %}
    <p>Rendered if elif true</p>
{% else %}
    <p>Rendered if all false</p>
{% endif %}
```

### Loops

```jinja2
{% for item in items %}
    <p>{{ item.title }}</p>
{% endfor %}

{% for key, value in dict.items() %}
    <p>{{ key }}: {{ value }}</p>
{% endfor %}
```

**Loop variables:**

```jinja2
{% for item in items %}
    {{ loop.index }}       {# 1-based counter #}
    {{ loop.index0 }}      {# 0-based counter #}
    {{ loop.first }}       {# True if first iteration #}
    {{ loop.last }}        {# True if last iteration #}
    {{ loop.length }}      {# Total iterations #}
{% endfor %}
```

### Comments

```jinja2
{# This is a Jinja2 comment. It won't appear in output. #}
```

### Filters

```jinja2
{{ text | default("fallback") }}   {# Use fallback if text is undefined #}
{{ items | length }}                {# Number of items in list #}
{{ text | title }}                  {# Title Case #}
{{ text | upper }}                  {# UPPERCASE #}
{{ text | lower }}                  {# lowercase #}
{{ text | truncate(60) }}           {# Truncate to 60 chars #}
{{ data | tojson }}                 {# Serialize to JSON #}
{{ text | safe }}                   {# Don't escape HTML (use carefully!) #}
```

### Macros (Reusable Components)

```jinja2
{% macro story_card(item) %}
<article class="story-card">
    <h3><a href="{{ item.url }}">{{ item.title }}</a></h3>
    <p>{{ item.summary }}</p>
</article>
{% endmacro %}

{# Use it #}
{{ story_card(lead_story) }}
```

---

## Complete Variable Reference

### `edition.html` (format_page.py)

| Variable | Type | Description |
|----------|------|-------------|
| `date` | str | Formatted date string (e.g., "January 30, 2026") |
| `vol` | str | Roman numeral volume (e.g., "III") |
| `issue` | int | Issue number within the month |
| `edition_url` | str | Full URL to the edition on GitHub Pages |
| `lead_story` | dict | First story from first non-empty category |
| `lead_story.title` | str | Lead story headline |
| `lead_story.summary` | str | Lead story summary (3-5 sentences) |
| `lead_story.url` | str | Lead story source URL |
| `lead_story.source_name` | str | Lead story source (e.g., "github.com") |
| `lead_story.published_date` | str | Lead story publication date (may be empty) |
| `sections` | dict | `{category_key: [story_dicts]}` |
| `sections[key][n].title` | str | Story headline |
| `sections[key][n].summary` | str | Story summary |
| `sections[key][n].url` | str | Story source URL |
| `sections[key][n].source_name` | str | Story source |
| `sections[key][n].published_date` | str | Story date (may be empty) |
| `category_labels` | dict | `{key: "🛠️ Repos"}` — display names |
| `category_story_counts` | dict | `{key: 5}` — story counts for index rail |
| `index_categories` | list | Ordered category keys for index rail |
| `papers` | list | Paper stories (separated for side-box layout) |

### `email.html` (format_email.py)

| Variable | Type | Description |
|----------|------|-------------|
| `date` | str | Formatted date string |
| `edition_url` | str | Link to the full web edition |
| `categories` | dict | `{key: [top_2_stories]}` — only top 2 per category |
| `categories[key][n].title` | str | Story headline |
| `categories[key][n].summary` | str | Story summary |
| `categories[key][n].url` | str | Story source URL |
| `categories[key][n].source_name` | str | Story source |
| `categories[key][n].published_date` | str | Story date (may be empty) |
| `category_labels` | dict | `{key: "🛠️ Repos"}` |
| `more_counts` | dict | `{key: count_excess}` — "+N more" links |

### `archive.html` (publish_github.py)

| Variable | Type | Description |
|----------|------|-------------|
| `calendar` | dict | `{"YYYY-MM": [edition_dicts]}` — grouped by month |
| `calendar[month][n].date` | str | Edition date ("2026-01-28") |
| `calendar[month][n].vol` | str | Volume (Roman numeral) |
| `calendar[month][n].issue` | int | Issue number |
| `calendar[month][n].lead_story` | str | Lead story title |
| `calendar[month][n].category_count` | int | Number of categories with results |
| `editions` | list | Flat list of all editions (for JSON embed) |
| `months` | list | Sorted month strings for selector dropdown |
| `years` | list | Available years for selector dropdown |

---

## Common Patterns

### Conditional Display

```jinja2
{% if item.published_date %}
    <span class="date">{{ item.published_date }}</span>
{% endif %}
```

Always check optional fields before rendering. Not all stories have dates. Not all categories have results.

### Safe HTML Links

```jinja2
<a href="{{ item.url }}" target="_blank" rel="noopener">
    {{ item.title }}
</a>
```

Always use `target="_blank"` for external links (user preference). Always use `rel="noopener"` for security.

### Category Iteration Pattern

```jinja2
{% for cat_key in index_categories %}
    {% if sections[cat_key] | length > 0 %}
    <section class="category-section" id="section-{{ cat_key }}">
        <h2>{{ category_labels[cat_key] }}</h2>
        {% for item in sections[cat_key] %}
            {{ story_card(item) }}
        {% endfor %}
    </section>
    {% endif %}
{% endfor %}
```

- Iterate in a defined order (`index_categories`), not dict order
- Check length before rendering section (empty categories get skipped)
- Use `id="section-{{ key }}"` for anchor links from the index rail

### Truncation for Cards

```jinja2
<div class="edition-lead">{{ edition.lead_story[:60] }}...</div>
```

Archive cards show truncated lead story titles. Python's `[:60]` slicing works in Jinja2.

---

## Debugging Template Errors

### "UndefinedError: 'X' is undefined"

The template references a variable that wasn't passed in `.render()`.

**Fix:** Pass the variable from the Python renderer, or use `default()`:

```jinja2
{{ optional_variable | default("No value") }}
```

### "TemplateNotFound: email.html"

The template file isn't found. Check:
- The template is in `daily_ai_digest/templates/`
- The `PackageLoader` points to `"daily_ai_digest"` not `"daily_ai_digest.templates"`
- The template filename matches exactly (case-sensitive)

### "Value is not a valid list"

You're trying to iterate over something that isn't iterable:

```jinja2
{# Wrong — categories is a dict, not list #}
{% for cat in categories %}

{# Right — iterate dict.items() #}
{% for key, items in categories.items() %}
```

### Jinja2 Rendering Is Blank

The template rendered but produced empty output. Common causes:
- An `{% if %}` condition blocks all content
- The data passed is empty (check what `.render()` receives)
- A syntax error silently swallowed (check Jinja2 version for silent failures)

**Debug by removing conditions:**

```jinja2
{# Temporarily remove to see what renders #}
{# {% if condition %} #}
    <p>Content that was hidden</p>
{# {% endif %} #}
```

### Local Rendering Test

```python
# Test template rendering without running the full pipeline
from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader("daily_ai_digest", "templates"))
template = env.get_template("edition.html")
html = template.render(
    date="January 30, 2026",
    vol="III",
    issue=5,
    edition_url="https://example.com",
    lead_story={
        "title": "Test Lead Story",
        "summary": "This is a test summary for the lead story.",
        "url": "https://example.com/story",
        "source_name": "example.com",
        "published_date": "2026-01-30",
    },
    sections={"repos": [], "skills": []},  # Add mock data
    category_labels={"repos": "🛠️ Repos", "skills": "🧠 Skills"},
    category_story_counts={"repos": 0, "skills": 0},
    index_categories=["repos", "skills"],
    papers=[],
)
with open("test-output.html", "w") as f:
    f.write(html)
print("Written to test-output.html")
```

---

## Security Notes

### Auto-Escaping

Jinja2 auto-escapes HTML by default in most configurations. `{{ "<script>alert('xss')</script>" }}` renders as `&lt;script&gt;...` — it's safe by default.

### The `|safe` Filter

Only use `|safe` when you're absolutely sure the content is safe:

```jinja2
{# DANGEROUS — only use for trusted content #}
{{ user_provided_content | safe }}
```

In this project, `|safe` is not used. All data comes from the Python pipeline (trusted) or is user data displayed through Jinja2's auto-escaping.

### `target="_blank"` with `rel="noopener"`

Always:

```html
<a href="{{ item.url }}" target="_blank" rel="noopener noreferrer">
```

`rel="noopener"` prevents the opened page from accessing `window.opener`. `rel="noreferrer"` prevents the referrer header from being sent.

---

## Next Steps

- How the edition page uses Jinja2 → **[Edition Template](19-edition-template.md)**
- How the email uses Jinja2 → **[Email Template](20-email-template.md)**
- How the archive page uses Jinja2 → **[Archive Template](21-archive-template.md)**
