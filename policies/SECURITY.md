# Security policy

This policy applies to every repo in the portolan-sdi organization.

## Reporting a vulnerability

Report vulnerabilities privately through GitHub Security Advisories. Open the affected repo's **Security** tab and choose **Report a vulnerability**. Never use a public issue for a security problem.

You can expect an acknowledgment within 7 days and a fix or mitigation plan within 30 days for confirmed issues.

## Supported versions

Unless a repo states otherwise, only the latest release line is supported with security fixes.

## Automated auditing

Repos with Python packages run `pip-audit` and `bandit` in CI, and Dependabot monitors GitHub Actions and package dependencies. See each repo's workflows for specifics.
