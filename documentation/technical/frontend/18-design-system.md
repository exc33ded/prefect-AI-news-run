# Design System

The visual language of The AI Herald website — colors, typography, spacing, and design tokens. This page explains the system; edit the CSS variables in templates to change the look globally.

---

## Design Philosophy

The website follows a **vintage newspaper aesthetic** (Daily Prophet / Harry Potter magical newspaper). Key principles:

- **Parchment textures** — warm beige/tan backgrounds simulating aged paper
- **Serif typography** — Georgia and Times New Roman for that classic newsprint feel
- **Dark ink colors** — deep browns and blacks for text, red accents like a masthead
- **Drop caps** — enlarged first letter of lead stories
- **Gothic ornaments** — wax seals, decorative borders, ornamental dividers
- **Magical touches** — shimmer animations, flicker effects, subtle motion

---

## Color Palette

### Light Theme (Default)

```css
:root {
    --bg-primary: #f4e4c1;        /* Parchment — main background */
    --bg-secondary: #e8d5a3;      /* Darker parchment — cards, sidebars */
    --bg-tertiary: #faf3e0;       /* Light parchment — hover states */
    --text-primary: #2c1810;      /* Dark brown ink — body text */
    --text-secondary: #5c4033;    /* Medium brown — meta text, dates */
    --text-muted: #8b7355;        /* Light brown — captions, footnotes */
    --accent: #8b0000;            /* Deep red — masthead, links, highlights */
    --accent-hover: #a52a2a;      /* Lighter red — hover states */
    --border: #8b7355;            /* Warm brown — borders, dividers */
    --border-light: #c4a97d;      /* Light brown — subtle borders */
    --shadow: rgba(44, 24, 16, 0.1);  /* Shadow color */
}
```

### Dark Theme

```css
[data-theme="dark"] {
    --bg-primary: #1a1a2e;        /* Dark navy — main background */
    --bg-secondary: #16213e;      /* Darker navy — cards, sidebars */
    --bg-tertiary: #0f3460;       /* Deep blue — hover states */
    --text-primary: #e8d5a3;      /* Warm parchment — body text */
    --text-secondary: #c4a97d;    /* Muted gold — meta text */
    --text-muted: #8b7355;        /* Brown — captions */
    --accent: #c41e3a;            /* Bright red — masthead, links */
    --accent-hover: #e63946;      /* Brighter red — hover states */
    --border: #2a2a4a;            /* Dark border */
    --border-light: #3a3a5a;      /* Slightly lighter border */
    --shadow: rgba(0, 0, 0, 0.3); /* Shadow color */
}
```

### Usage Map

| Variable | Used For |
|----------|----------|
| `--bg-primary` | Page background, main content area |
| `--bg-secondary` | Sidebar, index rail, category headers, cards |
| `--bg-tertiary` | Hover states on stories, table headers |
| `--text-primary` | Headlines, body text, lead story |
| `--text-secondary` | Source names, dates, metadata |
| `--text-muted` | Disclaimers, footnotes, "N more" links |
| `--accent` | Masthead title, links, category labels, drop-cap |
| `--border` | Section dividers, story separators, table borders |
| `--border-light` | Subtle inside borders, grid dividers |
| `--shadow` | Card shadows, modal shadows |

---

## Typography

### Font Stack

```css
/* Headlines - classic serif for authority */
--font-headline: 'Georgia', 'Times New Roman', serif;

/* Body - readable serif for long text */
--font-body: 'Georgia', 'Times New Roman', serif;

/* Meta / UI - sans-serif for clarity */
--font-meta: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
```

### Type Scale

```css
--text-xs: 0.75rem;     /* 12px — disclaimers, small notes */
--text-sm: 0.875rem;    /* 14px — dates, source names, metadata */
--text-base: 1rem;      /* 16px — body text, story summaries */
--text-lg: 1.125rem;    /* 18px — subheadings, index items */
--text-xl: 1.25rem;     /* 20px — category headers */
--text-2xl: 1.5rem;     /* 24px — story headlines */
--text-3xl: 2rem;       /* 32px — masthead subtitle */
--text-4xl: 3rem;       /* 48px — masthead title */
--text-5xl: 4rem;       /* 64px — lead story drop-cap */
```

### Usage

| Size | Where |
|------|-------|
| `--text-xs` | "AI-generated content" disclaimer |
| `--text-sm` | Source names, dates, "N more →" links |
| `--text-base` | Story summaries (3-5 sentences each) |
| `--text-lg` | Index rail items, subheadings |
| `--text-xl` | Category headers ("✦ REPOS ✦") |
| `--text-2xl` | Story headlines in sections |
| `--text-3xl` | Masthead dateline, section titles |
| `--text-4xl` | Masthead "The AI Herald" title |
| `--text-5xl` | Lead story drop-cap (first letter) |

---

## Spacing

```css
--space-xs: 0.25rem;    /* 4px */
--space-sm: 0.5rem;     /* 8px */
--space-md: 1rem;       /* 16px */
--space-lg: 1.5rem;     /* 24px */
--space-xl: 2rem;       /* 32px */
--space-2xl: 3rem;      /* 48px */
--space-3xl: 4rem;      /* 64px */
```

| Token | Used For |
|-------|----------|
| `--space-xs` | Tight internal padding |
| `--space-sm` | Story item gaps, inline spacing |
| `--space-md` | Padding inside cards, between related items |
| `--space-lg` | Section padding, between categories |
| `--space-xl` | Masthead padding, section margins |
| `--space-2xl` | Major section separation |
| `--space-3xl` | Page margins, footer spacing |

---

## Borders & Shadows

```css
/* Borders */
--border-thin: 1px;
--border-medium: 2px;
--border-thick: 3px;

/* Border styles for different contexts */
border: var(--border-thin) solid var(--border);         /* Default divider */
border-bottom: var(--border-medium) double var(--border); /* Newspaper-style */
border: var(--border-thin) solid var(--accent);          /* Accent borders */

/* Shadows */
box-shadow: 0 2px 8px var(--shadow);   /* Cards */
box-shadow: 0 4px 16px var(--shadow);  /* Modals, hover elevation */
box-shadow: 0 8px 32px var(--shadow);  /* Heavy elevation */
```

---

## Animations

### Shimmer (Masthead Title)

```css
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.masthead-title {
    background: linear-gradient(
        90deg,
        var(--accent) 0%,
        #ff6b6b 25%,
        var(--accent) 50%,
        #ff6b6b 75%,
        var(--accent) 100%
    );
    background-size: 200% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s ease-in-out infinite;
}
```

### Flicker (Tagline)

```css
@keyframes flicker {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.tagline {
    animation: flicker 4s ease-in-out infinite;
}
```

### Wax Seal (AI Logo)

```css
.wax-seal {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: radial-gradient(circle, #c41e3a, #8b0000);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3), inset 0 1px 3px rgba(255,255,255,0.2);
}
```

### Scroll Fade (Long Content)

```css
.scroll-fade {
    mask-image: linear-gradient(to bottom, black 80%, transparent 100%);
    -webkit-mask-image: linear-gradient(to bottom, black 80%, transparent 100%);
}
```

---

## Component Patterns

### Story Card

```html
<article class="story-card">
    <h3 class="story-headline">
        <a href="{{ item.url }}" target="_blank" rel="noopener">
            {{ item.title }}
        </a>
    </h3>
    <p class="story-meta">
        {{ item.source_name }}
        {% if item.published_date %} | {{ item.published_date }}{% endif %}
    </p>
    <p class="story-summary">{{ item.summary }}</p>
</article>
```

### Category Section

```html
<section class="category-section" id="section-{{ key }}">
    <h2 class="category-header">✦ {{ label }} ✦</h2>
    <div class="story-grid">
        {% for item in items %}
        <article class="story-card">...</article>
        {% endfor %}
    </div>
</section>
```

### Lead Story (Drop Cap)

```html
<article class="lead-story">
    <h2 class="lead-headline">
        <a href="{{ lead.url }}" target="_blank" rel="noopener">
            {{ lead.title }}
        </a>
    </h2>
    <p class="lead-summary">
        <span class="drop-cap">{{ lead.summary[:1] }}</span>
        {{ lead.summary[1:] }}
    </p>
    <p class="lead-meta">{{ lead.source_name }}</p>
</article>
```

---

## Icons & Ornaments

The website uses Unicode characters, not icon fonts or images:

| Character | Usage |
|-----------|-------|
| ✦ | Category headers ("✦ REPOS ✦") |
| ◆ | Secondary dividers |
| ─ | Horizontal rules |
| · | Separators in meta text ("source · date") |
| → | Link arrows, CTA buttons |
| 🌙 / ☀️ | Theme toggle (dark/light) |
| ✉ | Email / contact indicators |

**Why no icon fonts?** Fewer HTTP requests. Unicode renders everywhere. Consistent with the vintage aesthetic.

---

## Print Styles

The edition includes basic print styles:

```css
@media print {
    body {
        background: white;
        color: black;
    }

    .theme-toggle,
    .index-rail,
    .archive-link {
        display: none;     /* Hide interactive elements */
    }

    a {
        text-decoration: underline;
        color: black;
    }

    .lead-story {
        break-inside: avoid;
    }

    .story-card {
        break-inside: avoid;
    }
}
```

---

## Extending the Design System

To add a new color, font, or spacing value:

1. **Add the CSS variable** in both `:root` and `[data-theme="dark"]` blocks
2. **Use it in the template** with `var(--your-variable)`
3. **Document it here** (add to the appropriate table)

**Example — adding a highlight color for breaking news:**

```css
:root {
    --highlight: #ff6b6b;   /* Coral — breaking news highlight */
}

[data-theme="dark"] {
    --highlight: #ff4444;   /* Bright red — breaking news highlight */
}
```

Then use in HTML:

```html
<div style="border-left: 3px solid var(--highlight); padding-left: 1rem;">
    BREAKING NEWS
</div>
```

---

## Next Steps

- How the edition page is built → **[Edition Template](19-edition-template.md)**
- How the email is built → **[Email Template](20-email-template.md)**
- How themes work → **[Theme System](22-theme-system.md)**
- How responsive layout works → **[Responsive Layout](23-responsive-layout.md)**
