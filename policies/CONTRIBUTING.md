# Contributing to Portolan

Thanks for contributing to Portolan! This guide applies across all `portolan-sdi` repos. Please also make sure to read our [AI policy](AI_POLICY.md) and [code of conduct](CODE_OF_CONDUCT.md).

## Getting started

Portolan aims to be a welcoming, inclusive community. New contributions are great! Here are some things to keep in mind for first-timers.

### Proposing changes

Small changes like bug fixes are generally accepted provided they pass CI and adversarial review, and a human maintainer has signed off on them. (Maintainers may self-merge.)

Substantive design discussions happen in GitHub issues, not in Slack. Large changes require an issue with a discussion before any code is committed to the codebase (a PR with an example implementation may help for clarification, but please make sure it's truly worth maintainer attention). Examples of large changes include:
- Refactoring thousands of lines of code
- Adding a command or command group
- Adding a runtime dependency
- Adding a new repo or moving code between repos
- Changing how two or more repos work together

(If you are not sure if a change is large, it's probably large.)

When proposing a large change, open an issue that explains who needs the change, why, and what the current limitations are. Make sure to use the existing issue templates, and make sure to include a use case unless that's clearly not necessary. Proposed use cases should be closer to user stories (e.g., "A user wants to be able to visualize PMTiles with multiple styles") rather than a list of features (e.g., "It would be good if the Portolan spec supported listing multiple styles as assets in the STAC JSON").

### A note on AI bug reports/feature requests

Opening tickets has become incredibly cheap thanks to agents. Implementing those tickets has, too, for the same reason, which means that the bottleneck is now the time it takes for a maintainer to read your ticket, understand it, and hand it off to their own agent to implement. Sometimes this is appropriate, such as in the case of large changes (see above). But for small changes where the fix is pretty clear, we strongly encourage prefer that tickets be accompanied by a fix PR so that maintainers are not just spending all their time [being meat proxies](https://gruhn.me/blog/2026-08-03/). (For large fixes, too, we really appreciate contributors who are willing to handle the PR themselves once maintainers have signed off on the proposal.) 

### Conventions

Pretty much all of our code is Apache 2.0, with a couple of exceptions (see [norms/repos.md](https://github.com/portolan-sdi/portolan-ops/blob/main/norms/repos.md)). Commits must follow [Conventional Commits](https://www.conventionalcommits.org/). Writing must follow the [Portolan prose rules](https://github.com/portolan-sdi/portolan-ops/blob/main/norms/prose.md), which are enforced in CI by Vale and `prose-lint` hooks.

### Agents and code quality

Agents are great! We use them a lot to build Portolan. But we still expect code to be good. So:
- We enforce strict CI quality gates. Make sure your PR passes these.
- Make sure your changes include thorough, meaningful tests.
- Update docs where needed (but avoid adding a bunch of AI slop to them).
- Actually test that your code does what it claims to do -- don't just trust an agent blindly.
- Run at least one or two adversarial review passes on your PR and push the relevant fixes.

Humans are always responsible for their contributions to Portolan, even (and especially) when using agents. Contributors must be able to explain their contributions. See our [AI policy](AI_POLICY.md) for more detail.

### Core vs. community tooling

Portolan's goal is not to build comprehensive tooling for every possible use case. We distinguish between 1) the specification (which is the heart of the project), 2) tooling that we build and maintain because it makes it easier for us to develop and implement the spec for what we consider general-purpose use cases, and 3) non-essential tooling that we are happy to see community members build and maintain, but that we do not have the bandwidth to maintain ourselves. With that in mind, we will do our best to make the spec and core tooling easy to extend and build on.

Over time, we hope to push out some of the tooling that we've built to upstream projects (e.g., STAC), and also to potentially adopt some community-contributed tooling into core. This will be done at the discretion of the project leads/steering committee. If you are developing community tooling that you hope will eventually be promoted to core, we strongly encourage you to check out [the CI norms](https://github.com/portolan-sdi/portolan-ops/blob/main/norms/ci.md) in this repo and make sure your work is aligned with our standards, which will make it easier to eventually integrate your code.

### Communication

For day-to-day communications, please see the [Portolan channel](https://cloudnativegeo.slack.com/archives/C0A1JBH9529) in the Cloud-Native Geo Slack. Follow the Slack channel for our weekly standup. Announcements are posted in the [Portolan Google Group](https://groups.google.com/g/portolan). Security issues should be reported privately per the [security policy](SECURITY.md), never in a public issue.

The [code of conduct](CODE_OF_CONDUCT.md) applies in all community spaces.

### Maintainer bandwidth

Please be respectful of [maintainers' time and attention](AI_POLICY.md#distractive-contributions). Portolan is led by a small core of maintainers who are responsible for many repos. Generally, we try to respond to issues, PRs, and Slack messages within a couple of days, but we can't always get to things immediately. If you think we've missed a message or forgotten something, feel free to send a quick Slack message, but avoid sending repeated follow-ups or contacting maintainers on platforms other than Slack or GitHub.

## Governance and decision-making

Portolan is still an early-stage open-source project, so decisions are made by a small group of core maintainers acting as a provisional steering committee. Currently this consists of:
- Nissim Lebovits (Radiant Earth), who is also the provisional [BDFL](https://en.wikipedia.org/wiki/Benevolent_dictator_for_life)
- Chris Holmes (Planet)
- Cayetano Benavent (CARTO)

As the project matures, we expect to transition to a more formal steering committee model along the lines of [STAC's governance](https://github.com/radiantearth/stac-spec/blob/master/process.md#governance).

Portolan is intended as a community-driven project, based on models like STAC and GeoParquet. Currently, development is supported primarily by Radiant Earth, with contributions from staff at CARTO, Planet, Development Seed, the Lincoln Institute, and more.

### Becoming a maintainer

Contributors can become maintainers by generally showing an interest in doing so; participating actively in Slack and/or weekly meetings; consistently contributing good, substantive code; and doing maintainer-y work such as reviewing PRs and updating docs and CI. Please talk to Nissim if you're interested in being a maintainer on the project.