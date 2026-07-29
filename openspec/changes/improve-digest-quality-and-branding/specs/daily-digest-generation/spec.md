## ADDED Requirements

### Requirement: Digest item summaries are substantive
Each digest item's `summary` field SHALL be a 3-5 sentence write-up covering what happened, why it matters, and at least one concrete detail or number from the source material, rather than a 1-2 sentence restatement of the headline.

#### Scenario: LLM produces a digest item
- **WHEN** the LLM selects a raw result for inclusion in a category's digest
- **THEN** the returned `summary` for that item is 3-5 sentences long and includes a concrete detail (e.g. a number, name, or specific claim) beyond the headline

### Requirement: Email branding matches the published edition
The daily email SHALL display the publication name "The AI Herald" in its title, masthead, and footer, matching the name used on the published GitHub Pages edition and archive.

#### Scenario: Email is rendered
- **WHEN** `render_email` renders the daily email template
- **THEN** the rendered HTML's `<title>`, masthead heading, and footer text all read "The AI Herald" (or its uppercase form), with no occurrence of "AI Daily"

### Requirement: Search key fallback survives transient errors
`search_category`'s per-key Tavily fallback SHALL advance to the next available API key on any exception raised while querying the current key, not only on quota-exceeded or invalid-key errors, and SHALL only propagate an error once every key has been tried.

#### Scenario: First key hits a transient error
- **WHEN** the first Tavily API key raises a timeout or other non-quota, non-auth exception
- **THEN** the search falls through and retries with the next configured key instead of aborting the category's search

#### Scenario: All keys fail
- **WHEN** every configured Tavily API key raises an exception
- **THEN** the last error encountered is raised to the caller, which `search_category` catches and converts to an empty result list for that category
