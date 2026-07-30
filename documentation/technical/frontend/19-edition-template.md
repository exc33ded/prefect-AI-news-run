# Edition Template

The daily edition HTML template (`templates/edition.html`) — its structure, sections, Jinja2 variables, and how to modify it.

---

## Template Overview

The edition template produces a ~425-line HTML document styled as a gothic/parchment newspaper. It receives the digest data from `format_page.py` and renders the full web edition.

**What it receives:**

```python
template.render(
    date="January 30, 2026",
    vol="III",                          # Roman numeral volume
    issue=5,                            # Issue number this month
    edition_url="https://...html",      # Full URL to this edition
    lead_story={title, summary, url, source_name, published_date},
    sections={                          # Category → stories
        "repos": [{title, summary, url, source_name, date}, ...],
        "skills": [...],
        ...
    },
    category_labels={"repos": "🛠️ Repos", ...},
    category_story_counts={"repos": 5, ...},  # For index rail
    index_categories=["repos", "skills", ...],  # Ordered list for sidebar
    papers=[...],                       # Papers get special treatment
)
```

---

## HTML Structure

```
<!DOCTYPE html>
<html lang="en" data-theme="light">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The AI Herald — {{ date }}</title>
    <style>
        /* ~300 lines of CSS */
        /* CSS variables (light + dark) */
        /* Layout (grid + flexbox) */
        /* Animations (shimmer, flicker) */
        /* Print styles */
    </style>
  </head>
  <body>
    <!-- Section 1: Masthead -->
    <header class="masthead">
        <h1 class="masthead-title">THE AI HERALD</h1>
        <p class="masthead-dateline">{{ date }}</p>
        <p class="masthead-vol">Vol. {{ vol }}, No. {{ issue }}</p>
        <p class="masthead-tagline">"All the AI News That's Fit to Print"</p>
        <div class="wax-seal">AI</div>
        <button class="theme-toggle" onclick="toggleTheme()">🌙</button>
    </header>

    <!-- Section 2: AI Disclaimer -->
    <div class="disclaimer">
        <em>⚠ This digest is AI-generated...</em>
    </div>

    <!-- Section 3: Front Page (Lead + Index) -->
    <main class="front-page">
        <!-- Lead Story -->
        <article class="lead-story">
            <h2 class="lead-headline">
                <a href="{{ lead_story.url }}" target="_blank" rel="noopener">
                    {{ lead_story.title }}
                </a>
            </h2>
            <p class="lead-summary">
                <span class="drop-cap">{{ lead_story.summary[:1] }}</span>
                {{ lead_story.summary[1:] }}
            </p>
            <p class="lead-meta">
                {{ lead_story.source_name }}
                {% if lead_story.published_date %} · {{ lead_story.published_date }}{% endif %}
            </p>
        </article>

        <!-- Index Rail (Sidebar) -->
        <aside class="index-rail">
            <h3>Today's Edition</h3>
            <ul>
                {% for cat_key in index_categories %}
                <li>
                    <a href="#section-{{ cat_key }}">
                        {{ category_labels[cat_key] }}
                        <span class="count">{{ category_story_counts[cat_key] }}</span>
                    </a>
                </li>
                {% endfor %}
            </ul>
        </aside>
    </main>

    <!-- Section 4: Category Sections -->
    {% for cat_key in index_categories %}
    {% if cat_key != "papers" %}
    <section class="category-section" id="section-{{ cat_key }}">
        <h2 class="category-header">
            ✦ {{ category_labels[cat_key] }} ✦
        </h2>
        <div class="story-grid">
            {% for item in sections[cat_key] %}
            <article class="story-card">
                <h3 class="story-headline">
                    <a href="{{ item.url }}" target="_blank" rel="noopener">
                        {{ item.title }}
                    </a>
                </h3>
                <p class="story-meta">
                    {{ item.source_name }}
                    {% if item.published_date %} · {{ item.published_date }}{% endif %}
                </p>
                <p class="story-summary">{{ item.summary }}</p>
            </article>
            {% endfor %}
        </div>
    </section>
    {% endif %}
    {% endfor %}

    <!-- Section 5: Papers Side-Box -->
    {% if papers %}
    <section class="papers-section" id="section-papers">
        <h2 class="category-header">✦ {{ category_labels['papers'] }} ✦</h2>
        <div class="papers-box">
            {% for item in sections['papers'] %}
            <article class="story-card paper-card">
                <h3 class="story-headline">
                    <a href="{{ item.url }}" target="_blank" rel="noopener">
                        {{ item.title }}
                    </a>
                </h3>
                <p class="story-meta">
                    {{ item.source_name }}
                    {% if item.published_date %} · {{ item.published_date }}{% endif %}
                </p>
                <p class="story-summary">{{ item.summary }}</p>
            </article>
            {% endfor %}
        </div>
    </section>
    {% endif %}

    <!-- Section 6: Footer -->
    <footer>
        <p>The AI Herald · An AI-generated daily digest</p>
        <p>
            <a href="archive.html">Archive</a>
            · Vol. {{ vol }}, No. {{ issue }}
            · {{ date }}
        </p>
    </footer>

    <script>
        // Theme toggle logic
        function toggleTheme() {
            const html = document.documentElement;
            const button = document.querySelector('.theme-toggle');
            if (html.dataset.theme === 'dark') {
                html.dataset.theme = 'light';
                button.textContent = '🌙';
            } else {
                html.dataset.theme = 'dark';
                button.textContent = '☀️';
            }
        }
    </script>
  </body>
</html>
```

---

## Section Details

### Masthead

The top banner with title, date, volume/issue, and theme toggle.

**Key elements:**
- `.masthead-title` — shimmer animation on "THE AI HERALD"
- `.masthead-tagline` — flicker animation on the tagline
- `.wax-seal` — circular "AI" logo (CSS radial gradient)
- `.theme-toggle` — 🌙/☀️ button

### Front Page

Two-column layout: lead story (75%) + index rail (25%).

**Lead story:**
- First item from first non-empty category
- `.drop-cap` — enlarged first letter (64px, floated left)
- Full summary displayed

**Index rail:**
- Sticky sidebar (or absolute positioned on mobile)
- Lists all categories with story counts
- Anchor links jump to `#section-{key}`

### Category Sections

3-column grid for regular categories, special `side-box` layout for papers.

**Story grid:**
```css
.story-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
}
```

**Papers box:**
```css
.papers-box {
    border-left: 3px solid var(--accent);
    padding-left: 1.5rem;
    background: var(--bg-secondary);
}
```

### Footer

Simple footer with "Archive" link, volume/issue, and date.

---

## CSS Architecture

### Variable System
All colors, fonts, and spacing use CSS variables defined in `:root` and `[data-theme="dark"]`. See [Design System](18-design-system.md) for full reference.

### Layout System
- **Grid** for story sections (3 columns)
- **Flexbox** for front page (lead + sidebar)
- **Absolute positioning** for sidebar on desktop, static on mobile
- **Percentage-based widths** with max-width constraints

### Media Queries
```css
/* Tablet */
@media (max-width: 1024px) {
    .story-grid { grid-template-columns: repeat(2, 1fr); }
    .index-rail { display: none; }
}

/* Mobile */
@media (max-width: 768px) {
    .story-grid { grid-template-columns: 1fr; }
    .masthead-title { font-size: 2rem; }
    .drop-cap { font-size: 3rem; }
    .lead-story { padding: 1rem; }
}
```

### Animations
- `.masthead-title` — shimmer (3s infinite)
- `.masthead-tagline` — flicker (4s infinite)
- All animations use GPU-accelerated properties (`transform`, `opacity`, `background-position`)

---

## Modifying the Template

### Change Layout Width

```css
body {
    max-width: 1200px;      /* Change from 1200px to your preferred width */
    margin: 0 auto;
    padding: 0 var(--space-lg);
}
```

### Change Column Count

```css
.story-grid {
    grid-template-columns: repeat(2, 1fr);  /* 2-column instead of 3-column */
    /* or: repeat(4, 1fr) for 4 columns on very wide screens */
}
```

### Add a New Template Variable

1. Pass the variable from `format_page.py`:

```python
template.render(
    ...,
    custom_var=some_value,
)
```

2. Use it in the template:

```html
<div class="custom-section">
    {{ custom_var }}
</div>
```

### Add a Custom CSS Animation

```html
<style>
@keyframes my-animation {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

.my-element {
    animation: my-animation 2s ease-in-out infinite;
}
</style>
```

---

## Next Steps

- Visual design tokens → **[Design System](18-design-system.md)**
- Dark/light theme mechanics → **[Theme System](22-theme-system.md)**
- Mobile/tablet behavior → **[Responsive Layout](23-responsive-layout.md)**
- How Jinja2 powers the template → **[Jinja2 Templating](24-jinja2-templating.md)**
