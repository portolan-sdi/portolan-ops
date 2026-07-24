# Security policy

This policy applies to every repo in the portolan-sdi organization.

## Reporting a vulnerability

Report vulnerabilities privately via GitHub Security Advisories: open the affected repo's **Security** tab and choose **Report a vulnerability**. Do not open a public issue for security problems.

You can expect an acknowledgment within 7 days and a fix or mitigation plan within 30 days for confirmed issues.

## Supported versions

Unless a repo states otherwise, only the latest release line is supported with security fixes.

## Automated auditing

Repos with Python packages run `pip-audit` and `bandit` in CI, and Dependabot monitors GitHub Actions and package dependencies. See each repo's workflows for specifics.
