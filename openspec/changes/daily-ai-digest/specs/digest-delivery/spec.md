## ADDED Requirements

### Requirement: Email delivery via Resend
The system SHALL send the rendered email HTML via Resend's API, authenticated with a `RESEND_API_KEY` secret, with sender/recipient configurable and retries=2.

#### Scenario: Email sent successfully
- **WHEN** the rendered email HTML is ready
- **THEN** the delivery task sends it via Resend to the configured recipient(s) and retries up to 2 times on failure

### Requirement: GitHub Pages publish via Contents API
The system SHALL publish the rendered page HTML to the GitHub repo's `docs/` folder using the GitHub Contents API, authenticated with a `GITHUB_TOKEN` secret with repo write access, creating or updating both `docs/index.html` and the dated archive file.

#### Scenario: Page committed to GitHub
- **WHEN** the rendered page HTML is ready
- **THEN** the publish task creates-or-updates `docs/index.html` and `docs/<date>.html` via the Contents API

### Requirement: Independent delivery channels
A failure in one delivery channel (email or GitHub publish) SHALL NOT prevent the other channel from completing.

#### Scenario: GitHub publish fails, email still sends
- **WHEN** the GitHub publish task fails (e.g. API error)
- **THEN** the flow logs the failure and still attempts/completes the email send

#### Scenario: Email fails, GitHub publish still completes
- **WHEN** the email delivery task fails
- **THEN** the flow logs the failure and the GitHub Pages publish still completes independently
