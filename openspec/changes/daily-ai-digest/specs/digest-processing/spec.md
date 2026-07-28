## ADDED Requirements

### Requirement: LLM summarization task
The system SHALL provide one Prefect task that takes the combined raw results from all four search categories and calls DeepSeek (`deepseek-v4-flash`, via the OpenAI SDK, `base_url=https://api.deepseek.com`) with a low/minimal reasoning-effort setting to dedupe near-identical results, rank by relevance/novelty, and produce the top 4-6 items per category.

#### Scenario: Digest produced from combined raw results
- **WHEN** the processing task receives raw results from all four search categories
- **THEN** it returns a per-category list of at most 6 items, each with title, 1-2 sentence summary, url, and source_name

### Requirement: Structured JSON output with schema validation
The system SHALL request JSON-formatted output from the LLM matching a fixed schema (`{category: [{title, summary, url, source_name}]}`) and SHALL validate/parse the response.

#### Scenario: Valid JSON parses on first attempt
- **WHEN** the LLM returns well-formed JSON matching the schema
- **THEN** the task parses it directly into the digest structure

#### Scenario: Malformed JSON falls back to a retry
- **WHEN** the LLM's first response fails to parse as JSON
- **THEN** the task retries once with an added "return valid JSON only" instruction before giving up on that run

### Requirement: Retry with backoff on API failure
The processing task SHALL retry up to 2 times with exponential backoff on DeepSeek API errors.

#### Scenario: Transient API error recovers
- **WHEN** a DeepSeek API call fails transiently (e.g. timeout, 5xx)
- **THEN** the task retries with exponential backoff up to 2 times before failing
