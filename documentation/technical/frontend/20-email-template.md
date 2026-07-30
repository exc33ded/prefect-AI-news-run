# Email Template

The email HTML template (`templates/email.html`) — its structure, email client compatibility constraints, and how to modify it.

---

## Template Overview

The email template produces an HTML email styled as a vintage editorial digest. It receives pre-filtered data (top 2 per category) from `format_email.py`.

**What it receives:**

```python
template.render(
    date="January 30, 2026",
    edition_url="https://...2026-01-30.html",  # Link to full web edition
    categories={                                # Top 2 per category
        "repos": [{title, summary, url, source_name, published_date}, ...],
        "skills": [...],
        ...
    },
    category_labels={"repos": "🛠️ Repos", ...},
    total_stories=50,                           # FIXME: Verify
    more_counts={"repos": 3, "skills": 1, ...}, # "+N more" links
)
```

---

## HTML Structure

```
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The AI Herald — {{ date }}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f4e4c1;">
    <!-- Wrapper table (email-safe container) -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4e4c1;">
      <tr>
        <td align="center">
          <!-- Content table (max-width 600px) -->
          <table width="600" cellpadding="0" cellspacing="0"
                 style="max-width:600px; background-color:#ffffff; margin:20px auto;">

            <!-- Section 1: Header / Masthead -->
            <tr>
              <td style="background-color:#2c1810; padding:30px 40px; text-align:center;">
                <h1 style="font-family:Georgia,Times New Roman,serif; font-size:36px;
                           color:#f4e4c1; margin:0; letter-spacing:3px;">
                  THE AI HERALD
                </h1>
                <p style="font-family:Georgia,Times New Roman,serif; font-size:14px;
                          color:#c4a97d; margin:10px 0 0; font-style:italic;">
                  "All the AI News That's Fit to Print"
                </p>
                <p style="font-family:Georgia,Times New Roman,serif; font-size:14px;
                          color:#e8d5a3; margin:15px 0 0;">
                  {{ date }}
                </p>
              </td>
            </tr>

            <!-- Section 2: AI Disclaimer -->
            <tr>
              <td style="padding:20px 40px; background-color:#faf3e0;">
                <p style="font-family:Arial,sans-serif; font-size:11px; color:#8b7355;
                          margin:0; font-style:italic; text-align:center;">
                  ⚠ This digest is AI-generated. Headlines and URLs are from real search results.
                  Summaries are written by an AI model and may contain errors.
                </p>
              </td>
            </tr>

            <!-- Section 3: Category Loop -->
            {% for cat_key, items in categories.items() %}
            <tr>
              <td style="padding:30px 40px 10px;">
                <h2 style="font-family:Georgia,Times New Roman,serif; font-size:20px;
                           color:#8b0000; margin:0; text-align:center; border-bottom:2px
                           double #8b7355; padding-bottom:10px;">
                  ✦ {{ category_labels[cat_key] }} ✦
                </h2>
              </td>
            </tr>

            <!-- Story items (top 2 per category) -->
            {% for item in items %}
            <tr>
              <td style="padding:15px 40px;">
                <h3 style="font-family:Georgia,Times New Roman,serif; font-size:16px;
                           color:#2c1810; margin:0;">
                  <a href="{{ item.url }}" target="_blank"
                     style="color:#8b0000; text-decoration:none;">
                    {{ item.title }}
                  </a>
                </h3>
                <p style="font-family:Arial,sans-serif; font-size:11px; color:#8b7355;
                          margin:5px 0;">
                  {{ item.source_name }}
                  {% if item.published_date %} · {{ item.published_date }}{% endif %}
                </p>
                <p style="font-family:Georgia,Times New Roman,serif; font-size:14px;
                          color:#5c4033; line-height:1.6; margin:8px 0 0;">
                  {{ item.summary }}
                </p>
              </td>
            </tr>
            {% endfor %}

            <!-- "+N more" link -->
            {% if more_counts[cat_key] > 0 %}
            <tr>
              <td style="padding:5px 40px 20px; text-align:right;">
                <a href="{{ edition_url }}#section-{{ cat_key }}"
                   style="font-family:Arial,sans-serif; font-size:12px; color:#8b0000;">
                  +{{ more_counts[cat_key] }} more stories →
                </a>
              </td>
            </tr>
            {% endif %}
            {% endfor %}

            <!-- Section 4: CTA Button -->
            <tr>
              <td style="padding:30px 40px; text-align:center;">
                <a href="{{ edition_url }}"
                   style="display:inline-block; padding:12px 30px;
                          background-color:#8b0000; color:#ffffff;
                          font-family:Arial,sans-serif; font-size:14px;
                          text-decoration:none; border-radius:3px;">
                  READ TODAY'S FULL EDITION →
                </a>
              </td>
            </tr>

            <!-- Section 5: Footer -->
            <tr>
              <td style="padding:20px 40px; background-color:#2c1810; text-align:center;">
                <p style="font-family:Arial,sans-serif; font-size:11px; color:#c4a97d; margin:0;">
                  The AI Herald · An AI-generated daily digest
                </p>
                <p style="font-family:Arial,sans-serif; font-size:11px; color:#c4a97d; margin:5px 0 0;">
                  Built with Prefect, Tavily, DeepSeek & Groq
                </p>
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
```

---

## Email Client Compatibility

### Critical Rules

1. **Table-based layout** — `<table>` not `<div>` with flexbox/grid. Gmail and Outlook strip or ignore modern layout.
2. **Inline CSS only** — No `<style>` blocks in `<head>`. Outlook strips them.
3. **No external resources** — No `<link>`, no `@import`, no external fonts. These trigger security warnings.
4. **Fixed width** — 600px max. Mobile clients scale it down; desktop clients keep it readable.
5. **Web-safe fonts** — `Georgia`, `Times New Roman`, `Arial`, `serif`, `sans-serif` only. Custom fonts won't load.

### Client-Specific Notes

| Client | Quirks |
|--------|--------|
| **Gmail** | Strips `<style>` blocks. Ignores `background-image`. Supports web fonts but they're blocked by default. Clips emails > 102KB. |
| **Outlook (Windows)** | Uses Word's rendering engine. No `border-radius`, no `box-shadow`, no `background-image`. Limited `padding` support. |
| **Outlook (Mac/Web)** | Uses WebKit. Modern CSS mostly works. |
| **Apple Mail** | Best support. WebKit-based. Most modern CSS works including animations. |
| **Yahoo / AOL** | Strips `<style>` blocks. Moderate support for inline CSS. |

### What We Avoid

- `flexbox` / `grid` — use `<table>` instead
- `border-radius` — use flat borders
- `box-shadow` — not supported in Outlook
- `background-image` — not supported in Outlook/Gmail
- `position: absolute/fixed` — unpredictable in email clients
- Custom fonts (`@font-face`, `@import`) — blocked in many clients
- JavaScript — stripped by ALL email clients

---

## Color Scheme (Email-Specific)

The email uses hardcoded colors (not CSS variables) for compatibility:

| Color | Hex | Purpose |
|-------|-----|---------|
| Parchment bg | `#f4e4c1` | Outer background |
| White | `#ffffff` | Content background |
| Dark brown | `#2c1810` | Masthead/footer background |
| Light tan | `#e8d5a3` | Masthead text |
| Medium tan | `#c4a97d` | Secondary text in footer |
| Deep red | `#8b0000` | Links, category headers, CTA button |
| Medium brown | `#5c4033` | Body text |
| Light brown | `#8b7355` | Meta text (source, date) |
| Very light tan | `#faf3e0` | Disclaimer background |

---

## Modifying the Email Template

### Change Layout Width

```html
<table width="700" ... style="max-width:700px;">
```

**Max 600-700px** for email compatibility. Wider emails force horizontal scrolling in many clients.

### Add a Logo

```html
<tr>
  <td style="text-align:center; padding-top:20px;">
    <img src="https://yourdomain.com/logo.png" alt="AI Herald"
         width="80" height="80"
         style="display:block; margin:0 auto;">
  </td>
</tr>
```

**Important:** Image must be hosted on a public HTTPS URL. Add `width` and `height` attributes (Outlook requirement).

### Change CTA Button Color

```html
<a href="{{ edition_url }}"
   style="background-color:#0066cc; ...">  <!-- Blue instead of red -->
```

### Add a Subtitle/Feature Section

Insert a new `<tr>` block before or after a category:

```html
<tr>
  <td style="padding:20px 40px; text-align:center;">
    <p style="font-family:Georgia,serif; font-size:16px; color:#2c1810;">
      📰 Featured Story of the Day
    </p>
    <!-- Featured story content -->
  </td>
</tr>
```

### Reduce Digest Size (Avoid Gmail Clipping)

Gmail clips emails > 102KB. If the email is getting clipped:
- Show top 1 per category instead of top 2
- Shorten summaries in `process.py` (`"write a 1-2 sentence summary"`)
- Remove the disclaimer section (not recommended)
- Split into separate "brief" and "full" emails

---

## Testing Email Changes

### Local Test

```bash
# Render the email and save to a file
uv run python -c "
from daily_ai_digest.format_email import render_email
# Use mock digest data
mock_digest = {...}  # You'll need mock data
html = render_email(mock_digest, 'https://example.com')
with open('email-preview.html', 'w') as f:
    f.write(html)
"

# Open in browser
start email-preview.html
```

### Email Client Test

After rendering locally:
1. Open `email-preview.html` in a browser
2. Copy the rendered HTML (Ctrl+A, Ctrl+C)
3. Paste into your email client's HTML editor
4. Send a test to yourself
5. Check in Gmail, Outlook, Apple Mail, mobile

### Automated Testing

Services like [Litmus](https://litmus.com) and [Email on Acid](https://www.emailonacid.com) provide screenshots across 50+ email clients. Useful for major template changes.

---

## Next Steps

- How the web edition is built → **[Edition Template](19-edition-template.md)**
- How the archive page works → **[Archive Template](21-archive-template.md)**
- Visual design tokens → **[Design System](18-design-system.md)**
