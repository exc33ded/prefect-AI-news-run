## ADDED Requirements

### Requirement: Stale GitHub repos are excluded from the repos category
The system SHALL exclude a candidate item in the "repos" category's raw search results if its URL points to a GitHub repository whose `created_at` date is older than 90 days at the time of the flow run.

#### Scenario: Repo is older than the freshness threshold
- **WHEN** a `repos` category search result's URL is `https://github.com/<owner>/<repo>` and the GitHub API reports that repo's `created_at` as more than 90 days before the current run
- **THEN** that item is removed from the raw results before they are passed to `process_results`

#### Scenario: Repo is within the freshness threshold
- **WHEN** a `repos` category search result's URL points to a GitHub repo created within the last 90 days
- **THEN** that item is kept in the raw results passed to `process_results`

### Requirement: Freshness lookup fails open
The system SHALL keep a candidate item unfiltered whenever its repo age cannot be positively determined, rather than dropping it.

#### Scenario: URL is not a GitHub repo
- **WHEN** a `repos` category search result's URL does not match the `github.com/<owner>/<repo>` shape
- **THEN** the item is kept in the raw results unchanged, with no freshness check attempted

#### Scenario: GitHub API lookup fails
- **WHEN** the GitHub API call for a candidate repo's `created_at` errors (timeout, rate limit, non-200 response)
- **THEN** the item is kept in the raw results rather than being dropped

### Requirement: Other categories are unaffected
The freshness filter SHALL apply only to the "repos" category; all other categories' raw search results SHALL pass through unchanged.

#### Scenario: Non-repos category search results
- **WHEN** `search_category` returns raw results for any category other than "repos"
- **THEN** no GitHub freshness filtering is applied to those results
