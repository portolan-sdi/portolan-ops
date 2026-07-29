# Portolan Voice

This voice governs all collectively-produced, public-facing copy such as the Portolan website, official announcements, and docs. It also governs the written artifacts around the work: READMEs, PR and issue bodies, commit message bodies, and code comments meant to last. The goal is to make sure that all material representing Portolan, including material drafted with an LLM, shares a coherent voice. (Individually-produced material like blogs, talks, and podcasts are different; your blog should be your own voice.)

Portolan sounds calm, direct, and sure of itself. It states facts without hedging, and is opinionated about quality and honest about limits. It never uses language that sounds like SEO, a sales pitch, or AI slop. Some guidance on this:

On content:

- Every claim needs a mechanism or a checkable fact behind it, such as a named tool, a named competitor, or a cost the reader can verify. If a sentence of praise has no proof sentence near it, cut the praise.
- Portolan is opinionated about high quality standards for publishing geospatial data, but also a work in progress. We emphasize being an open-source, evolving standard, and we actively welcome community contributions.
- Focus on outcomes. Many of our potential users don't know about or understand cloud-native geospatial tech. We emphasize what Portolan makes possible rather than what Portolan is in order to make it easy for less technical users to understand the benefits (e.g., "Portolan makes it easy to share geospatial data" rather than "Portolan is a standard based on STAC, COG, and GeoParquet").
- Relatedly, many of these benefits are subtractions, e.g., "Portolan lets you publish geospatial data with no server," or "Portolan is much cheaper than publishing formats like ESRI." Name the subtraction once and move on. A standalone sentence of stacked negations ("no X, no Y, no Z") sounds like advertising.
- State an outcome once, in plain words, and stop. If an image already implies the outcome, don't also name it. "A searchable web of open data" does not need "so data can be found and combined."
- Scope claims to what stays true. "Everything is open source" breaks the day a vendor ships a commercial product on the standard, while "no vendor can lock you in" survives it. Before writing an absolute, ask what future fact would falsify it.
- When the honest claim is relative, make the comparison explicit. Don't say "simple"; say what the alternative requires and what Portolan removes. Admitting difficulty is fine, especially when the admission points at our tooling (e.g., "building a catalog still takes work, which is what the CLI is for").
- Pick verbs that show how the product actually works. Write "query a dataset," not "load a dataset," because nothing in Portolan gets downloaded or imported.
- Portolan is "AI-ready," not "AI-first." Agents are the means, people are the ends.

On style:

- Write flat, declarative sentences, mostly under twenty words.
- Vary sentence texture. Good writers don't write five one-clause sentences in a row. Deliberately use a range of punctuation (mostly commas and periods) and sentence structures to avoid tedious repetition.
- Don't be aphoristic or poetic. LLMs especially are bad at metaphors and aphorisms. So just… don't use them (this is especially true of section headers; choose plain and descriptive over stupid aphorisms, every time).
- Don't write mirrored phrases. "Published by anyone, discoverable by everyone" and "found together, used together" sound like advertising. If two halves of a sentence share the same structure, rewrite one.
- Don't use a colon to set up a dramatic second clause. Use colons to introduce lists or specifics.
- Paragraphs should be mostly two or three sentences, with one subject per paragraph. If you're tempted to end a paragraph with a summing-up line to drive it home, don't.
- Use plain, active verbs like publish, share, access, or store. Cut needless adjectives like powerful or seamless; keep only functional ones like standardized or cloud-optimized. Similarly, be wary of absolutes like infinite or everyone.
- Technical terms can be used without explanation, but the surrounding prose should remain accessible. Don't bludgeon people with jargon.
- Don't abuse "X, so you can Y." There are a wealth of other conjunctions in the English language. Try some new ones!
- If your sentence needs an em-dash or a semi-colon, ask yourself if you really need it. Instead, try splitting your clauses into separate sentences, reversing the order of the clauses, or just… not writing meaningless bloated prose.
- Cut the marketing BS. No rule of three unless there are actually, legitimately three items in the list.
- When in doubt, [Source Cooperative](https://source.coop/) is our reference point for what we should sound like. Look at their [docs](https://docs.source.coop/) and website. Also, [this prose style guide](https://raw.githubusercontent.com/dbreunig/scaffold-docs-skill/refs/heads/main/references/prose-style.md) based on Strunk and White is great.

Agents MUST abide by this voice in all collective public-facing copy and in every written artifact.
