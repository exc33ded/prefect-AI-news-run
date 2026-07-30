# Responsive Layout

How the website adapts to different screen sizes — the grid system, breakpoints, and mobile/tablet behavior.

---

## Breakpoints

The edition template uses three breakpoints:

| Breakpoint | Target | What Changes |
|-----------|--------|-------------|
| `> 1200px` | Desktop (default) | 3-column story grid, sidebar visible, full masthead |
| `769px — 1024px` | Tablet | 2-column story grid, sidebar hidden, smaller masthead |
| `≤ 768px` | Mobile | Single-column layout, minimal masthead, larger touch targets |

```css
/* Default: Desktop (no media query needed) */
.story-grid {
    grid-template-columns: repeat(3, 1fr);
}

/* Tablet */
@media (max-width: 1024px) {
    .story-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Mobile */
@media (max-width: 768px) {
    .story-grid {
        grid-template-columns: 1fr;
    }
}
```

---

## Desktop Layout (> 1200px)

```
┌─────────────────────────────────────────────────────────────┐
│                   MASTHEAD (full)                           │
│  THE AI HERALD                    🌙                        │
│  January 30, 2026 · Vol. III, No. 5                         │
│  "All the AI News That's Fit to Print"                      │
│                        ╭──╮                                 │
│                        │AI│ (wax seal)                      │
│                        ╰──╯                                 │
├─────────────────────────────────────────────────────────────┤
│                      ⚠ DISCLAIMER                           │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                  │
│  LEAD STORY (75%)        │  INDEX RAIL (25%)                │
│                          │                                  │
│  ┌────────────────────┐  │  repos (5)                       │
│  │                    │  │  skills (3)                      │
│  │  Drop-cap          │  │  prompting (4)                   │
│  │  T  he full lead   │  │  papers (6)                      │
│  │    story summary   │  │  startups (3)                    │
│  │    with the first  │  │  model_releases (4)              │
│  │    letter enlarged │  │  benchmarks (2)                   │
│  │                    │  │  industry_news (5)                │
│  │  Source · Date     │  │  trends (3)                      │
│  └────────────────────┘  │  productivity (4)                │
│                          │                                  │
├──────────────────────────┴──────────────────────────────────┤
│                                                             │
│  ✦ REPOS ✦                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Story 1  │  │ Story 2  │  │ Story 3  │                 │
│  │ Story 4  │  │ Story 5  │  │          │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
│  ✦ SKILLS ✦                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ ...      │  │ ...      │  │ ...      │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
│  ... more sections ...                                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  FOOTER                                                     │
└─────────────────────────────────────────────────────────────┘
```

### Key Desktop Features

- **3-column story grid** for main category sections
- **Side-by-side front page** (lead story 75% + index rail 25%)
- **Sticky sidebar** — follows scroll on longer pages
- **Full masthead** with wax seal, volume/issue, shimmer animation
- **Theme toggle** top-right

---

## Tablet Layout (769px — 1024px)

```
┌──────────────────────────────────┐
│  MASTHEAD (reduced)              │
│  THE AI HERALD           🌙      │
│  January 30, 2026                │
├──────────────────────────────────┤
│  ⚠ DISCLAIMER                    │
├──────────────────────────────────┤
│  LEAD STORY (full width)         │
│  ┌────────────────────────────┐  │
│  │ Drop-cap summary...        │  │
│  └────────────────────────────┘  │
│  [Index rail sidebar removed]    │
├──────────────────────────────────┤
│  ✦ REPOS ✦                      │
│  ┌──────────┐  ┌──────────┐    │
│  │ Story 1  │  │ Story 2  │    │
│  │ Story 3  │  │ Story 4  │    │
│  │ Story 5  │  │          │    │
│  └──────────┘  └──────────┘    │
│                                  │
│  ✦ SKILLS ✦                     │
│  ┌──────────┐  ┌──────────┐    │
│  │ ...      │  │ ...      │    │
│  └──────────┘  └──────────┘    │
├──────────────────────────────────┤
│  FOOTER                          │
└──────────────────────────────────┘
```

### Tablet CSS

```css
@media (max-width: 1024px) {
    /* Reduce columns */
    .story-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    /* Hide index rail */
    .index-rail {
        display: none;
    }

    /* Full-width lead story */
    .front-page {
        flex-direction: column;
    }

    .lead-story {
        width: 100%;
    }

    /* Smaller masthead */
    .masthead-title {
        font-size: var(--text-3xl);  /* 2rem */
    }

    /* Smaller drop cap */
    .drop-cap {
        font-size: var(--text-4xl);  /* 3rem */
    }
}
```

**The sidebar is removed** because at tablet widths, 25% of the screen is too narrow for a useful index rail. Users scroll to find categories naturally.

---

## Mobile Layout (≤ 768px)

```
┌──────────────────────┐
│  THE AI HERALD  🌙   │
│  Jan 30, 2026        │
├──────────────────────┤
│  ⚠ AI DISCLAIMER     │
├──────────────────────┤
│  LEAD STORY          │
│  ┌────────────────┐  │
│  │ Drop-cap...    │  │
│  └────────────────┘  │
├──────────────────────┤
│  ✦ REPOS ✦          │
│  ┌────────────────┐  │
│  │ Story 1        │  │
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │ Story 2        │  │
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │ Story 3        │  │
│  └────────────────┘  │
│  ...                 │
├──────────────────────┤
│  ✦ SKILLS ✦         │
│  ...                 │
├──────────────────────┤
│  FOOTER              │
└──────────────────────┘
```

### Mobile CSS

```css
@media (max-width: 768px) {
    /* Single column */
    .story-grid {
        grid-template-columns: 1fr;
    }

    /* Minimal masthead */
    .masthead {
        padding: var(--space-md);
    }

    .masthead-title {
        font-size: var(--text-2xl);  /* 1.5rem */
        letter-spacing: 1px;
    }

    .masthead-vol,
    .masthead-tagline {
        display: none;  /* Hide secondary info */
    }

    .wax-seal {
        display: none;  /* Hide decorative seal */
    }

    /* Smaller spacing throughout */
    .category-section {
        padding: var(--space-md);
    }

    .story-card {
        padding: var(--space-md);
    }

    /* Smaller drop cap */
    .drop-cap {
        font-size: var(--text-3xl);  /* 2rem */
    }

    /* Larger touch targets */
    .story-headline a {
        padding: var(--space-sm) 0;
        display: block;
    }

    .theme-toggle {
        top: 0.5rem;
        right: 0.5rem;
        padding: 0.75rem;
    }

    /* Full-width cards with clear separators */
    .story-card {
        border-bottom: 1px solid var(--border-light);
        margin-bottom: var(--space-md);
    }

    .story-card:last-child {
        border-bottom: none;
    }
}
```

### Mobile Priorities

1. **Readability first** — single column, larger text (16px minimum for body)
2. **Touch-friendly** — links and buttons have minimum 44px touch targets
3. **Reduced decoration** — hide wax seal, animations, volume/issue in masthead
4. **Clear separation** — border between cards replaces grid gutters

---

## Index Rail Behavior

### Desktop: Sticky Sidebar

```css
.index-rail {
    position: sticky;
    top: 2rem;
    width: 25%;
    max-height: calc(100vh - 4rem);
    overflow-y: auto;
}
```

Stays visible while the user scrolls through categories. Allows quick navigation.

### Tablet: Hidden

```css
@media (max-width: 1024px) {
    .index-rail {
        display: none;
    }
}
```

Removed entirely — not enough horizontal space.

### Mobile: Hidden

Same as tablet — no index rail.

---

## Lead Story Behavior

### Desktop: Side-by-side with Index

```css
.front-page {
    display: flex;
    gap: 2rem;
}

.lead-story {
    width: 75%;
}
```

### Tablet: Full-width, No Index

```css
@media (max-width: 1024px) {
    .lead-story {
        width: 100%;
    }
}
```

### Mobile: Reduced Styling

Larger padding, smaller drop cap, no decorative borders.

---

## Papers Section Behavior

The papers section uses a special `side-box` layout on all devices:

```css
.papers-box {
    border-left: 3px solid var(--accent);
    padding-left: 1.5rem;
    background: var(--bg-secondary);
    max-width: 400px;
    float: right;
    margin-left: 2rem;
    margin-bottom: 2rem;
}
```

On mobile, the float is removed:

```css
@media (max-width: 768px) {
    .papers-box {
        float: none;
        max-width: 100%;
        margin-left: 0;
    }
}
```

---

## Typography Scaling

| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| Masthead title | 3rem (48px) | 2rem (32px) | 1.5rem (24px) |
| Category headers | 1.25rem (20px) | 1.125rem (18px) | 1rem (16px) |
| Story headlines | 1.5rem (24px) | 1.25rem (20px) | 1.125rem (18px) |
| Story summaries | 1rem (16px) | 1rem (16px) | 1rem (16px) |
| Meta text | 0.875rem (14px) | 0.875rem (14px) | 0.8125rem (13px) |
| Drop cap | 4rem (64px) | 3rem (48px) | 2rem (32px) |

**Body text stays at 1rem (16px)** on all devices — it's the minimum comfortable reading size and shouldn't shrink.

---

## Testing Responsiveness

### Browser DevTools

1. Open the edition in a browser
2. F12 → Toggle Device Toolbar (Ctrl+Shift+M / Cmd+Shift+M)
3. Test at these widths:
   - 1920px (Desktop)
   - 1024px (Tablet landscape)
   - 768px (Tablet portrait)
   - 375px (iPhone SE)
   - 414px (iPhone 11)
   - 360px (Small Android)

### What to Check

- No horizontal scrollbar at any width
- Text is readable (at least 16px for body)
- Links/buttons are tappable (at least 44px touch targets on mobile)
- No content is cut off or overlapping
- Theme toggle is always visible and clickable
- Animations don't cause layout shifts
- Images (if any) scale properly

---

## Next Steps

- Design tokens → **[Design System](18-design-system.md)**
- Edition page structure → **[Edition Template](19-edition-template.md)**
- Archive page → **[Archive Template](21-archive-template.md)**
