# Archive Template

The archive page template (`templates/archive.html`) — an interactive calendar browser for all past editions.

---

## Template Overview

The archive template produces a ~320-line HTML document with an interactive calendar grid. It receives the full editions list from `publish_github.py:_update_archive()`.

**What it receives:**

```python
template.render(
    calendar={                              # Grouped by year-month
        "2026-01": [
            {"date": "2026-01-28", "vol": "I", "issue": 1, "lead_story": "...", "category_count": 10},
            {"date": "2026-01-29", "vol": "I", "issue": 2, "lead_story": "...", "category_count": 9},
            {"date": "2026-01-30", "vol": "I", "issue": 3, "lead_story": "...", "category_count": 10},
        ],
        "2026-02": [...],
    },
    editions=[                              # Flat list (for JSON embed)
        {"date": "2026-01-28", ...},
        {"date": "2026-01-29", ...},
        ...
    ],
    months=["2026-01", "2026-02"],          # Sorted month keys for selectors
    years=["2026"],                          # Available years for filtering
)
```

**Data embedded as JSON** for client-side interactivity:

```html
<script type="application/json" id="editions-data">
{{ editions | tojson }}
</script>
```

The `| tojson` Jinja2 filter serializes the Python dict to safe JSON.

---

## HTML Structure

```
<!DOCTYPE html>
<html lang="en" data-theme="light">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The AI Herald — Archive</title>
    <style>
        /* ~200 lines of CSS */
        /* Calendar grid layout */
        /* Month/year selector styles */
        /* Modal styles */
        /* Dark/light theme */
    </style>
  </head>
  <body>
    <!-- Section 1: Header -->
    <header>
      <h1>The AI Herald</h1>
      <p>Archive</p>
      <button class="theme-toggle" onclick="toggleTheme()">🌙</button>
      <a href="index.html">← Back to Today's Edition</a>
    </header>

    <!-- Section 2: Month/Year Selector -->
    <div class="archive-controls">
      <select id="year-select" onchange="filterArchive()">
        {% for year in years %}
        <option value="{{ year }}">{{ year }}</option>
        {% endfor %}
      </select>

      <select id="month-select" onchange="filterArchive()">
        <option value="all">All Months</option>
        {% for month in months %}
        <option value="{{ month }}">{{ month }}</option>
        {% endfor %}
      </select>
    </div>

    <!-- Section 3: Calendar Grid -->
    <div class="archive-grid" id="archive-grid">
      {% for year_month, month_editions in calendar.items() %}
      <div class="month-block" data-month="{{ year_month }}">
        <h2 class="month-header">{{ year_month }}</h2>
        <div class="edition-grid">
          {% for edition in month_editions %}
          <div class="edition-card"
               data-date="{{ edition.date }}"
               onclick="showEdition('{{ edition.date }}')">
            <div class="edition-date">{{ edition.date[-5:] }}</div>
            <div class="edition-vol">Vol. {{ edition.vol }}, No. {{ edition.issue }}</div>
            <div class="edition-lead">{{ edition.lead_story[:60] }}...</div>
            <div class="edition-count">{{ edition.category_count }} categories</div>
          </div>
          {% endfor %}
        </div>
      </div>
      {% endfor %}
    </div>

    <!-- Section 4: Edition Detail Modal (Popout) -->
    <div class="modal-overlay" id="modal-overlay" onclick="hideEdition()">
      <div class="modal-content" onclick="event.stopPropagation()">
        <button class="modal-close" onclick="hideEdition()">✕</button>

        <h2 class="modal-title" id="modal-title"></h2>
        <p class="modal-vol" id="modal-vol"></p>
        <p class="modal-lead" id="modal-lead"></p>
        <p class="modal-count" id="modal-count"></p>

        <a class="modal-link" id="modal-link" target="_blank">
          Read Full Edition →
        </a>
      </div>
    </div>

    <!-- Section 5: Footer -->
    <footer>
      <p>The AI Herald · An AI-generated daily digest</p>
      <p>
        <a href="index.html">Today's Edition</a>
        · Archive
      </p>
    </footer>

    <!-- Embedded data -->
    <script type="application/json" id="editions-data">
      {{ editions | tojson }}
    </script>

    <!-- Interactivity scripts -->
    <script>
      // Load embedded data
      const editions = JSON.parse(
        document.getElementById('editions-data').textContent
      );

      // Filter by year/month
      function filterArchive() { ... }

      // Show edition detail modal
      function showEdition(date) { ... }

      // Hide modal
      function hideEdition() { ... }

      // Theme toggle
      function toggleTheme() { ... }
    </script>
  </body>
</html>
```

---

## Key Features

### Calendar Grid

Each month gets a `month-block` with an `edition-grid` inside. Cards show:
- Date (e.g., "01-28")
- Volume and Issue (e.g., "Vol. I, No. 1")
- Truncated lead story (60 chars)
- Category count

```css
.edition-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
}

.edition-card {
    background: var(--bg-secondary);
    padding: 1rem;
    border: 1px solid var(--border);
    cursor: pointer;
    transition: transform 0.2s;
}

.edition-card:hover {
    transform: translateY(-2px);
    background: var(--bg-tertiary);
}
```

### Month/Year Filtering

Two `<select>` dropdowns filter the grid:

```javascript
function filterArchive() {
    const year = document.getElementById('year-select').value;
    const month = document.getElementById('month-select').value;
    const blocks = document.querySelectorAll('.month-block');

    blocks.forEach(block => {
        const blockMonth = block.dataset.month;
        const blockYear = blockMonth.substring(0, 4);

        if (year !== 'all' && blockYear !== year) {
            block.style.display = 'none';
        } else if (month !== 'all' && blockMonth !== month) {
            block.style.display = 'none';
        } else {
            block.style.display = 'block';
        }
    });
}
```

### Edition Modal (Popout)

Clicking a card opens a modal with full edition details:

```javascript
function showEdition(date) {
    const edition = editions.find(e => e.date === date);
    document.getElementById('modal-title').textContent =
        `Edition — ${edition.date}`;
    document.getElementById('modal-vol').textContent =
        `Vol. ${edition.vol}, No. ${edition.issue}`;
    document.getElementById('modal-lead').textContent =
        edition.lead_story;
    document.getElementById('modal-count').textContent =
        `${edition.category_count} categories`;

    const link = document.getElementById('modal-link');
    link.href = `${edition.date}.html`;

    document.getElementById('modal-overlay').style.display = 'flex';
}

function hideEdition() {
    document.getElementById('modal-overlay').style.display = 'none';
}
```

### Embedded Data

The editions list is embedded as JSON in a `<script>` tag, making it available to client-side JavaScript without additional HTTP requests:

```html
<script type="application/json" id="editions-data">
[{"date": "2026-01-28", "vol": "I", "issue": 1, ...}, ...]
</script>
```

---

## CSS Structure

```css
/* CSS Variables — same as edition.html */
:root { ... }
[data-theme="dark"] { ... }

/* Calendar Layout */
.archive-grid { ... }
.month-block { ... }
.month-header { ... }
.edition-grid { ... }
.edition-card { ... }
.edition-date { ... }

/* Controls */
.archive-controls { ... }
#year-select, #month-select { ... }

/* Modal */
.modal-overlay { ... }
.modal-content { ... }

/* Responsive */
@media (max-width: 768px) {
    .edition-grid { grid-template-columns: 1fr; }
    .modal-content { width: 95%; }
}
```

---

## Data Flow

```
UPDATE ARCHIVE (publish_github.py)
  │
  ├── Append new edition to the list
  │     editions.append({date, vol, issue, lead_story, category_count})
  │
  ├── PUT docs/archive.json (updated list)
  │
  └── Render archive.html
        │
        ├── Group editions by year-month → calendar dict
        ├── Extract year/month lists for selectors
        ├── Jinja2 renders the HTML
        │     └── Calendar grid (server-rendered from calendar dict)
        │     └── JSON embed (client-side from editions list for filtering/modals)
        └── PUT docs/archive.html
```

The calendar grid is server-rendered from the `calendar` dict (grouped by month). The embedded JSON `editions` list powers client-side filtering and modals.

---

## Modifying the Archive

### Add Search/Filter by Keyword

Add a text input:

```html
<input type="text" id="search-input"
       placeholder="Search editions..."
       oninput="filterByKeyword()">
```

```javascript
function filterByKeyword() {
    const query = document.getElementById('search-input').value.toLowerCase();
    document.querySelectorAll('.edition-card').forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? 'block' : 'none';
    });
}
```

### Change Card Display

Show full lead story instead of truncated:

```html
<div class="edition-lead">{{ edition.lead_story }}</div>
<!-- Remove [:60] truncation in the Python code -->
```

### Add Pagination for Heavy Archives

If you have 100+ editions:

```javascript
const PAGE_SIZE = 12;
let currentPage = 0;

function showPage(page) {
    const cards = document.querySelectorAll('.edition-card');
    const start = page * PAGE_SIZE;
    const end = start + PAGE_SIZE;

    cards.forEach((card, i) => {
        card.style.display = (i >= start && i < end) ? 'block' : 'none';
    });
}
```

---

## Next Steps

- How the edition page works → **[Edition Template](19-edition-template.md)**
- Dark/light theme mechanics → **[Theme System](22-theme-system.md)**
- How data is passed to templates → **[Jinja2 Templating](24-jinja2-templating.md)**
