# Understanding The Digest

Every day at 8:00 AM IST, **The AI Herald** searches the internet for the latest AI developments and delivers a curated digest — by email and on the web. This page explains what you're looking at, how it's built, and how to get the most out of it.

---

## What the Digest Contains

The digest covers **10 categories** of AI news. Each category gets a dedicated search, and the AI selects and summarizes the most relevant stories from each.

### The 10 Categories

| Category | What It Covers |
|----------|----------------|
| **Repos** | New AI/ML repositories on GitHub — tools, libraries, frameworks. Repos older than 90 days are filtered out. |
| **Skills** | AI agent skills, plugins, and extensions — what the community is building to extend AI capabilities. |
| **Prompting** | Prompt engineering techniques, best practices, new approaches to working with LLMs. |
| **Papers** | AI/ML research papers — new architectures, training methods, breakthroughs. |
| **Startups** | AI startup news — funding rounds, new companies, product launches. |
| **Model Releases** | New AI models — open-source, commercial, fine-tunes, and model updates. |
| **Benchmarks** | AI benchmark results — which models are leading on which tasks. |
| **Industry News** | Major AI industry developments — policy, partnerships, acquisitions. |
| **Trends** | Emerging trends and patterns in AI — what's gaining momentum. |
| **Productivity** | AI tools for productivity — how people are using AI to work better. |

### What Each Story Includes

Every story in the digest has:

- **Headline** — the article or repository title, linked to the source
- **Summary** — a 3-5 sentence AI-written summary of what it's about
- **Source** — the website or platform the story came from
- **Date** — when the story was published

---

## The Email Digest

The email arrives in your inbox with a vintage-newspaper aesthetic. Here's how to read it:

### Email Layout

```
┌─────────────────────────────────────────┐
│           THE AI HERALD                  │  ← Masthead
│       January 30, 2026                   │  ← Dateline
│       "All the AI News That's Fit to Print" │  ← Tagline
│                                          │
│       ✦ REPOS ✦                         │  ← Category header
│                                          │
│  Top Story 1                             │
│  ─────────                               │
│  Summary text here...                    │
│  Source: github.com    Jan 30, 2026      │
│                                          │
│  Top Story 2                             │
│  ─────────                               │
│  Summary text here...                    │
│  Source: github.com    Jan 29, 2026      │
│  +3 more stories → Full Edition          │
│                                          │
│       ✦ MODEL RELEASES ✦                │
│  ... (same pattern for each category)    │
│                                          │
│  ┌──────────────────────────────────┐    │
│  │  READ TODAY'S FULL EDITION       │    │
│  └──────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### Key Points

- The email shows the **top 2 stories per category** for quick scanning
- Each category shows a **"+N more"** link pointing to the full web edition
- The disclaimer at the top explains the digest is AI-generated — this is important transparency
- The email is **HTML-only** (not plain text) — styled to look like a classic newspaper column

---

## The Web Edition

The full edition lives on GitHub Pages at **[exc33ded.github.io/prefect-AI-news-run](https://exc33ded.github.io/prefect-AI-news-run/)**.

### What's On the Website

**The Front Page** — a gothic/parchment-styled newspaper with:

- **Lead Story** — the most important story of the day, with a large drop-cap letter, displayed prominently
- **Index Rail** — a sidebar listing all categories and the number of stories in each, with quick-jump links
- **Full Sections** — every category gets its own section with ALL the stories, not just the top 2
- **Papers Side-Box** — research papers get a special sidebar treatment separate from the main layout
- **Dark/Light Theme Toggle** — click the 🌙/☀️ button to switch themes
- **Volume/Issue Numbers** — each edition has a Volume (Roman numerals, counting months since the first edition) and Issue number (sequential within the month)

**The Archive** — an interactive calendar at `https://exc33ded.github.io/prefect-AI-news-run/archive.html` where you can:
- Browse past editions by month and year
- Click any date to see what that day's digest contained
- See all historical editions since the pipeline started running

### Website Features

- **Responsive Design:** Works on desktop, tablet, and mobile
- **CSS Animations:** Shimmer effect on the title, flicker on the tagline, wax seal "AI" logo
- **No JavaScript Dependencies:** Everything works with vanilla HTML/CSS/JS — no frameworks
- **Offline-Friendly:** Once loaded, the page works without an internet connection
- **Print-Friendly:** The edition can be printed and looks good on paper

---

## How the AI Picks Stories

The AI doesn't pick stories — it summarizes stories that the search API already found. Here's the process:

1. **Search:** Tavily searches each category with carefully crafted queries (e.g., "new AI tools released today 2026 GitHub")
2. **Filter:** For the "repos" category, GitHub repos older than 90 days are filtered out to keep things fresh
3. **Summarize:** All search results are sent to DeepSeek (an AI model) with instructions to select the most relevant stories and write summaries
4. **Anti-Hallucination:** The AI only writes summaries — it never writes headlines or URLs. Headlines and URLs come directly from the search results, so you'll never see made-up content

### Why Two AI Providers?

The system uses **two AI providers** for resilience:

- **DeepSeek** (`deepseek-v4-flash`) is the primary — it's fast and cost-effective
- **Groq** (`llama-3.3-70b-versatile`) is the fallback — if DeepSeek has an outage, Groq takes over automatically
- If both fail (extremely rare), the digest is still delivered with raw search results — no AI summaries, but you'll still see what was found

---

## Volume and Issue Numbers

Every edition has a Volume and Issue number displayed at the top:

- **Volume:** Counted in Roman numerals (I, II, III, IV...), incremented each calendar month since the first edition was published
- **Issue:** Sequential number (1, 2, 3...), resetting to 1 at the start of each new volume (month)

For example: **Vol. III, No. 17** means "the 17th edition published in the third month of operation."

---

## How to Use the Digest Effectively

### Quick Morning Scan (5 minutes)
1. Open the email
2. Read the headlines and summaries for the categories you care about most
3. Click "+N more" links for categories that look interesting

### Deep Dive (15-20 minutes)
1. Open the full web edition
2. Scan the lead story and index rail
3. Read full summaries in categories relevant to your work
4. Click through to original sources for stories you want to explore further

### Research Mode
1. Use the archive to find past editions
2. Search for specific topics by browsing relevant category sections across dates
3. Follow source links to original papers, repos, or articles

---

## Transparency Notes

- **This digest is AI-generated.** Stories are sourced by automated search and summarized by an AI model
- **Headlines and URLs are real** — they come directly from search results, never from the AI
- **Summaries may contain errors** — the AI tries to be accurate, but it can misinterpret or oversimplify
- **Not comprehensive** — 10 categories with ~5 stories each means ~50 stories per day; AI news is vast, and this is a curated sample
- **The pipeline is open-source** — you can inspect, modify, and run the entire thing yourself
