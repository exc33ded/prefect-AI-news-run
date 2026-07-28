## ADDED Requirements

### Requirement: Single orchestrating flow
The system SHALL provide one `@flow` function named `daily_ai_digest` that runs one search task per configured category in parallel, waits for all to complete, passes combined results to the processing task, renders both outputs from the resulting digest, and delivers both.

#### Scenario: End-to-end run
- **WHEN** `daily_ai_digest` is triggered (manually or on schedule)
- **THEN** it executes search (parallel) → process → format (email + page) → deliver (email + publish), in that dependency order

### Requirement: Partial-failure tolerance
The flow SHALL continue with partial data if one or more search tasks fail, logging the failure rather than aborting the run.

#### Scenario: One search category fails
- **WHEN** one of the configured category search tasks raises an error
- **THEN** the flow logs the failure and proceeds to processing using the results from the remaining categories

### Requirement: Cloud-visible logging
The flow SHALL enable `log_prints=True` (or equivalent) so each stage's progress and results are visible in the Prefect Cloud UI.

#### Scenario: Stage progress visible in UI
- **WHEN** the flow runs on Prefect Cloud
- **THEN** logs for each stage (search results per category, digest summary, delivery outcomes) appear in the flow run's logs

### Requirement: Serverless Managed deployment
The flow SHALL be deployable to Prefect Cloud on a `prefect:managed` work pool with code pulled from a GitHub repository and dependencies installed from the repo's `requirements.txt`, on a configurable daily cron schedule, without requiring any self-hosted worker.

#### Scenario: Deployment runs without a worker
- **WHEN** the deployment's schedule fires
- **THEN** Prefect Cloud provisions the managed infrastructure, clones the repo, installs `requirements.txt`, and runs the flow with no user-operated worker process involved
