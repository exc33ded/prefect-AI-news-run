## ADDED Requirements

### Requirement: Config-driven, parallel category search
The system SHALL define search categories (key, label, query) in a single config list (`categories.py`), not hardcoded per-task functions, and SHALL run one independent search task per configured category in parallel (via Prefect `.submit()`). The default configuration SHALL include at least: trending/new AI GitHub repos, new AI agent skills/tools/harnesses, new prompting/agentic-workflow techniques, and today's AI/ML research papers (biased to arxiv.org cs.AI/cs.LG/cs.CL).

#### Scenario: All configured categories searched concurrently
- **WHEN** the flow runs
- **THEN** one Tavily search task per entry in the categories config is submitted without waiting on each other, each scoped to its category's query and biased to the last day of results

#### Scenario: Adding a category requires no code change
- **WHEN** a new entry is added to the categories config list
- **THEN** the flow searches, processes, and renders that category on the next run without modifying `search.py`, `process.py`, or the templates

### Requirement: Multi-key rotation and fallback
The system SHALL support 1-4 configured Tavily API keys and rotate across them so a single rate-limited key does not fail the run.

#### Scenario: Key round-robin
- **WHEN** each search task starts
- **THEN** it uses a key selected by round-robin index across the configured keys

#### Scenario: Rate limit fallback
- **WHEN** a search request returns a rate-limit error
- **THEN** the task retries once using the next available key before giving up

### Requirement: Structured, empty-tolerant results
Each search task SHALL return a list of structured results (title, url, snippet/content, published date if available) and SHALL NOT raise if Tavily returns zero results for its category.

#### Scenario: Empty category result
- **WHEN** a search task's query returns no results
- **THEN** the task returns an empty list and the flow continues processing the other categories
