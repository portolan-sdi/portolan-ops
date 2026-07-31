# AI/LLM tool policy

This policy applies to every repo in the portolan-sdi organization. It was adopted in July 2026.

## Purpose

Our goal with this policy is to ensure high-quality, reliable software by keeping humans in the loop. We therefore require contributors to follow the policy below whenever using tools powered by Artificial Intelligence (AI), such as Large Language Models (LLMs).

## Policy

There must always be a human in the loop who is accountable for contributions and has read, reviewed, and understood all submitted code or text changes before asking other project members to review them. Contributors should be confident that the contribution is high enough quality that providing a review is a good use of scarce maintainer time, and they should be able to answer questions about their work during review.

We aspire to be a welcoming community that helps new human contributors grow their expertise. Understanding that new contributors may be less confident in their contributions, we suggest starting with targeted, bite-size contributions. These are both easier for maintainers to review and more likely to be accepted.

This policy includes, but is not limited to, the following kinds of contributions:

* Code, usually in the form of a pull request
* RFCs or design proposals
* Issue or security vulnerability reporting
* Comments and feedback on pull requests

## Details

An agent may draft the diff and the PR description. The contributor must read, understand, and approve both before requesting review, and must be able to explain any line of either. Drafting is where tools help; the reading and the accountability stay human. The description should explain the motivation, implementation approach, expected impact, and any open questions or uncertainties to the same extent as a contribution made without tool assistance, within the body budget CI enforces.

An important implication of this policy is that it bans agents that take action in our digital spaces without human approval, such as the GitHub @claude agent. Similarly, automated review tools that publish comments without human review are not allowed. An opt-in review tool that keeps a human in the loop is acceptable. As another example, using an LLM to generate documentation, which a contributor manually reviews for correctness and relevance, edits, and then posts as a PR, is an approved use of tools under this policy.

## Distractive contributions

The reason for our "human-in-the-loop" contribution policy is that processing patches, PRs, RFCs, comments, issues, and security alerts is not free: it takes maintainer time and energy to review those contributions. Sending the unreviewed output of an LLM to open source project maintainers extracts work from them in the form of design and code review, so we call this kind of contribution a "distractive contribution."

Our golden rule is that a contribution should be worth more to the project than the time it takes to review it. These ideas are captured by this quote from the book [Working in Public](https://press.stripe.com/working-in-public) by Nadia Eghbal:

> When attention is being appropriated, producers need to weigh the costs and benefits of the transaction. To assess whether the appropriation of attention is net-positive, it's useful to distinguish between extractive and non-extractive contributions. Extractive contributions are those where the marginal cost of reviewing and merging that contribution is greater than the marginal benefit to the project's producers. In the case of a code contribution, it might be a pull request that's too complex or unwieldy to review, given the potential upside.
> —Nadia Eghbal

Before the advent of LLMs, open source maintainers would often review any and all changes sent to the project because posting a change for review was a sign of interest from a potential long-term contributor. New tools enable more development but shift effort from the implementor to the reviewer, and our policy exists to ensure that we value and do not squander maintainer time.

## Handling violations

If a maintainer judges that a contribution doesn't comply with this policy, they should paste the following response to request changes:

```
This PR does not appear to comply with our policy on tool-generated content,
and requires additional justification for why it is valuable enough to the
project for us to review it. Please see our developer policy on
AI-generated contributions in CONTRIBUTING.md.
```

The best ways to make a change less extractive and more valuable are to reduce its size or complexity or to increase its usefulness to the community. These factors are impossible to weigh objectively, and our policy leaves this determination to the maintainers of each repo.

If it becomes clear that a GitHub issue or PR is off-track and not moving in the right direction, maintainers should apply the `distractive` label to help other reviewers prioritize their review time.

If a contributor fails to make their change meaningfully less extractive, maintainers may lock the conversation and/or close the pull request, issue, or RFC. In case of repeated violations, the project reserves the right to temporarily or indefinitely ban the infringing person or account.

## Copyright

Artificial intelligence systems raise many questions around copyright that have yet to be answered. Our policy on AI tools is similar to our copyright policy: contributors are responsible for ensuring that they have the right to contribute code under the terms of our license (Apache-2.0), typically meaning that either they, their employer, or their collaborators hold the copyright. Using AI tools to regenerate copyrighted material does not remove the copyright, and contributors are responsible for ensuring that such material does not appear in their contributions. Contributions found to violate this policy will be removed like any other offending contribution. If a reviewer has doubts about the legal aspects of a contribution, they may ask the contributor to provide more details on the origins of a particular piece of code.

## Credits for this document

This document is adapted from [Development Seed's AI/LLM tool policy](https://github.com/developmentseed/.github/blob/main/CODE_OF_CONDUCT.md), which is adapted from [GDAL's AI/LLM user policy](https://github.com/OSGeo/gdal/blob/ded35dc7bb817006220dcbd477d671b6dd9140f8/doc/source/community/ai_tool_policy.rst#L4), which in turn is an adaptation of the [LLVM "AI Tool Use Policy"](https://github.com/llvm/llvm-project/blob/5b7ad38d6ba835e4d4acef538846931fd64a2028/llvm/docs/AIToolPolicy.md).
