# Theme System

How the dark/light theme toggle works — CSS variables, JavaScript toggle logic, and how to add themes.

---

## How It Works

The theme system uses a `data-theme` attribute on `<html>` plus CSS variables:

```html
<html lang="en" data-theme="light">
```

- `data-theme="light"` → CSS applies `:root` variables
- `data-theme="dark"` → CSS applies `[data-theme="dark"]` overrides

The toggle button switches the attribute, and CSS responds instantly.

---

## CSS Variable Architecture

### Light Theme (Default — `:root`)

```css
:root {
    --bg-primary: #f4e4c1;
    --bg-secondary: #e8d5a3;
    --bg-tertiary: #faf3e0;
    --text-primary: #2c1810;
    --text-secondary: #5c4033;
    --text-muted: #8b7355;
    --accent: #8b0000;
    --accent-hover: #a52a2a;
    --border: #8b7355;
    --border-light: #c4a97d;
    --shadow: rgba(44, 24, 16, 0.1);
}
```

### Dark Theme (`[data-theme="dark"]`)

```css
[data-theme="dark"] {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-tertiary: #0f3460;
    --text-primary: #e8d5a3;
    --text-secondary: #c4a97d;
    --text-muted: #8b7355;
    --accent: #c41e3a;
    --accent-hover: #e63946;
    --border: #2a2a4a;
    --border-light: #3a3a5a;
    --shadow: rgba(0, 0, 0, 0.3);
}
```

### How Variables Are Used

Every color in the template uses variables, never hardcoded hex values:

```css
/* Correct — uses variable, theme-aware */
body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.story-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
}

a {
    color: var(--accent);
}

a:hover {
    color: var(--accent-hover);
}

/* Wrong — hardcoded, won't respond to theme */
body {
    background-color: #f4e4c1;  /* Ignores dark theme */
}
```

---

## JavaScript Toggle Logic

### Basic Toggle (edition.html)

```javascript
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
```

### With localStorage Persistence (archive.html)

```javascript
function toggleTheme() {
    const html = document.documentElement;
    const button = document.querySelector('.theme-toggle');
    const currentTheme = html.dataset.theme;
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.dataset.theme = newTheme;
    button.textContent = newTheme === 'dark' ? '☀️' : '🌙';

    localStorage.setItem('ai-herald-theme', newTheme);
}

// Apply saved theme on page load
(function() {
    const savedTheme = localStorage.getItem('ai-herald-theme');
    if (savedTheme) {
        document.documentElement.dataset.theme = savedTheme;
        const button = document.querySelector('.theme-toggle');
        if (button) {
            button.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        }
    }
})();
```

---

## The Toggle Button

```html
<button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark/light theme">
    🌙
</button>
```

Styled as:

```css
.theme-toggle {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: none;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 1.2rem;
    cursor: pointer;
    transition: transform 0.2s;
}

.theme-toggle:hover {
    transform: scale(1.1);
}
```

The emoji changes dynamically:
- Light theme: shows 🌙 (indicating "click for dark mode")
- Dark theme: shows ☀️ (indicating "click for light mode")

---

## Adding a New Theme

### Step 1: Define the CSS

```css
[data-theme="sepia"] {
    --bg-primary: #f5e6c8;
    --bg-secondary: #e8d5a3;
    --bg-tertiary: #faf0dc;
    --text-primary: #4a3728;
    --text-secondary: #6b5744;
    --text-muted: #8b7355;
    --accent: #8b4513;
    --accent-hover: #a0522d;
    --border: #8b7355;
    --border-light: #c4a97d;
    --shadow: rgba(74, 55, 40, 0.1);
}
```

### Step 2: Update the Toggle

```javascript
function toggleTheme() {
    const themes = ['light', 'dark', 'sepia'];  // Theme rotation
    const html = document.documentElement;
    const current = html.dataset.theme;
    const nextIndex = (themes.indexOf(current) + 1) % themes.length;
    const next = themes[nextIndex];

    html.dataset.theme = next;

    // Update button icon
    const icons = {'light': '🌙', 'dark': '☀️', 'sepia': '📜'};
    document.querySelector('.theme-toggle').textContent = icons[next];

    localStorage.setItem('ai-herald-theme', next);
}
```

---

## System Preference Detection

Optionally respect the OS/browser dark mode preference:

```javascript
(function() {
    const saved = localStorage.getItem('ai-herald-theme');
    if (saved) {
        document.documentElement.dataset.theme = saved;
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.dataset.theme = 'dark';
    }

    // Listen for OS theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('ai-herald-theme')) {
            document.documentElement.dataset.theme = e.matches ? 'dark' : 'light';
        }
    });
})();
```

**Note:** This project doesn't use `prefers-color-scheme` for the initial state. The default is always `light` (newspaper aesthetic). Users toggle manually. The reasoning is that the newspaper look is fundamental to the design — it's not just a "dark mode" preference, it's part of the identity.

---

## Print Styles

The theme system doesn't affect print:

```css
@media print {
    body {
        background: white !important;
        color: black !important;
    }

    /* Override theme variables for print */
    * {
        --bg-primary: white;
        --text-primary: black;
        --accent: black;
    }
}
```

---

## Theme Consistency Across Pages

The `edition.html` and `archive.html` templates share the same CSS variable definitions. Both have the toggle button. The archive page additionally uses `localStorage` for persistence between page navigations.

---

## Next Steps

- Design tokens reference → **[Design System](18-design-system.md)**
- Edition page layout → **[Edition Template](19-edition-template.md)**
- Archive page → **[Archive Template](21-archive-template.md)**
