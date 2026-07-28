## ADDED Requirements

### Requirement: Shared structured digest as single source of truth
Both output renderers SHALL consume the same structured digest object produced by the processing task; no formatting-specific data transformation SHALL happen outside `format_email.py`/`format_page.py`.

#### Scenario: Same digest renders both outputs
- **WHEN** the flow has a structured digest for a run
- **THEN** both the email HTML and the GitHub Pages HTML are rendered from that same object, independently of each other

### Requirement: Vintage-editorial email rendering
The system SHALL render the digest into inline-CSS-only HTML styled as a vintage newspaper (serif fonts, black/cream palette, masthead, dateline, section dividers), with each item's headline linking to its original source URL, a labeled AI-summary disclaimer near the top, and a "Read today's full edition" link to the GitHub Pages page.

#### Scenario: Email item links to original source
- **WHEN** an item is rendered in the email
- **THEN** its headline is a clickable link pointing to the item's original `url`, not a summary or intermediate page

#### Scenario: Disclaimer present
- **WHEN** the email is rendered
- **THEN** it includes a visible disclaimer stating the content below is an AI-generated summary and headlines link to full original pieces

### Requirement: Magical-newspaper page rendering
The system SHALL render the digest into a Jinja2 template (`templates/edition.html`) styled as a parchment/gothic-serif "newspaper" with placeholder sections per category and a dateline, producing `docs/index.html` and an archived `docs/YYYY-MM-DD.html`.

#### Scenario: Page rendered with today's date
- **WHEN** the page-rendering task runs for a given date
- **THEN** it produces both `docs/index.html` (latest) and `docs/<that-date>.html` (archive) from the same template and digest
