# Portolan messaging

> **STATUS: provisional, close to final.** This file distills the working Portolan Messaging document. The content is roughly 90% settled and will be finalized soon. Until then it still wins: describe Portolan only in the terms below, and never fall back to older copy in this or any other repo. Sections marked _to confirm_ are the known open items. When the messaging document is finalized, update this file first, then let dependent copy (starting with [org-profile/README.md](org-profile/README.md)) follow.

This is the single source of truth for how Portolan describes itself. All collective public copy derives from it, written in the voice defined by [VOICE.md](../VOICE.md).

## One-liner

> A standard for cloud-native geospatial catalogs, the tools to build them, and the registry that connects them.

## One paragraph

> Portolan publishes geospatial data as plain files on object storage, with no servers, no databases, and no proprietary licenses. Structured metadata lets a person or an agent read a catalog and query it directly. The standard sets the quality bar, a validator enforces it, tools make catalogs cheap to build, and a registry connects them into a network anyone can search.

## What Portolan is

Portolan makes geospatial data easy to publish and easy to use. A catalog is plain files in your own storage, described so that a person or an agent can understand the data and query it directly. Publishing works the same way whether you are a satellite company releasing a planetary archive or a city posting its building footprints. No servers, no databases, no accounts.

Under the hood, Portolan is an opinionated standard for cloud-native geospatial catalogs, plus the tooling around it. A catalog is a directory of open-format data on any S3-compatible bucket, described by structured STAC metadata and built on COG, GeoParquet, PMTiles, COPC, and GeoZarr. The standard defines what a great catalog is. The validator proves a catalog meets it. The CLI makes catalogs cheap to build. The registry connects catalogs into a searchable network. Each part raises the value of the others. If Portolan disappeared tomorrow, every file in a catalog would still work in the tools people already use.

## What it isn't

- **Not a platform.** There is nothing to log into and nothing to depend on. Catalogs live in your own storage and work with tools you already have.
- **Not a paid product.** The standard and the tools are open source under Apache-2.0. Your only costs are storage and egress, paid to your cloud provider, not to us.

## Why Portolan

Spatial data infrastructure still assumes servers, databases, and specialists. Portolan doesn't.

- **Open and interoperable.** Everything is open source under Apache-2.0 and built on existing standards: GeoParquet, cloud-optimized GeoTIFF, and STAC. These formats work across DuckDB, BigQuery, Pandas, and desktop GIS like QGIS and ArcGIS, so your data stays useful with or without Portolan.
- **Readable by people and machines alike.** Download portals and one-off APIs were built for one client at a time. A Portolan catalog describes itself in plain text and structured metadata, so a person or an agent can find the data and query it without a bespoke API to learn.
- **Simple.** Traditional spatial data infrastructure needs databases, services, and staff to run them. A Portolan catalog is files in a bucket.
- **Scales with your storage.** The same setup handles megabytes or terabytes. With no servers to run, scaling is your cloud provider's job, not yours.
- **Low cost.** The whole budget is storage plus egress. Sharing public data should not take an operations team, and a popular dataset should not blow a budget.
- **Sovereign.** The full stack can live inside your own jurisdiction. Host on AWS, GCS, Azure, MinIO, Hetzner, Scaleway, or any S3-compatible storage. No foreign vendor sits between your agency and its data.

## Philosophy

Portolan builds on existing standards rather than reinventing them. It is STAC 1.1.0 at its core and reuses established STAC extensions wherever they fit. On top of that, Portolan adds strong requirements on formats, statistics, structure, and documentation, so people and agents can use a catalog directly from storage, with no server in between. The point is a higher quality bar. Working with any Portolan catalog should be a good experience.

The standard is prescriptive where that supports interoperability, and it is meant to evolve as cloud-native tooling matures. Core standards like STAC and GeoParquet were built for long-term stability. Portolan sits on top of them and moves faster. Each version states what the community currently believes a great catalog looks like. Conformance is not a claim you make. It is passing the validator.

Where the current landscape has gaps, Portolan will incubate new standards or write down practices that until now have been informal. Usually that means contributing to STAC extensions or adding new ones.

People and agents are treated as equals throughout. A Portolan catalog should be low-friction for a human analyst and an automated one alike. Building or mirroring a catalog should be easy too, including with AI tools, because lowering the effort to publish is how more good data gets published.

## The registry

The registry is a catalog of catalogs. It is a GitHub repository, so submitting a catalog is a pull request and the whole index stays plain text. Anyone can read or mirror it, and anyone can build an index on top of it.

The registry is what turns individual catalogs into a network. It gives search a place to start, and it makes provenance visible. Every catalog names its producer, its provider, and its host using the STAC provider extension. When the producer and the provider are the same organization, the catalog is official. When they differ, it is a mirror, and the registry shows both, so you can compare copies and choose the source you trust.

Because the registry lives in version control, it works the way open source works. You can open a pull request against a dataset to flag a problem, or submit an example notebook showing what the data is good for. The data stays in the publisher's storage. The knowledge about it accumulates in the open.

## Who is Portolan for

Portolan is for anyone who publishes geospatial data and anyone who uses it.

- **Large publishers.** Most of the people who could use a large archive never touch it, because the portal requires an account and the API requires a client library. A Portolan catalog has neither. You describe the archive once, and analysts and agents can query it without downloading it, asking questions you never planned for.
- **Small publishers.** A city's flood maps and building footprints often go unpublished, because sharing them has meant a server and a budget line to keep it alive. A Portolan catalog is files in a bucket. Nothing runs afterward and the bill rounds to zero, and the registry makes the catalog as findable as a planetary archive.
- **Data users.** Working with spatial data has meant building a new pipeline for every source. A Portolan catalog says what it covers and what its fields mean before you download anything, and the formats let you fetch the two hundred megabytes you need instead of the forty gigabytes around them. You can start working the afternoon you find the data, and an agent can too, because a catalog that explains itself to a person explains itself to a machine.

The stories feed each other. Large publishers give the registry data worth searching. The registry makes small publishers findable the moment they join. Users turn catalogs into analysis and mirrors, and every mirror makes the network more useful to the next publisher deciding whether to join.

## Who is building Portolan

_To confirm._ Radiant Earth, Carto, Planet, Taylor Geospatial, and others. The full contributor and publisher list is pending in the messaging document.

## The future

Spatial data should be easy to find and easy to combine, at any scale, for a person or an agent. The goal is a world where most public spatial data lives in this standard: official sources publish their own catalogs, mirrors carry the data people already rely on, and the registry makes the whole network searchable. The next goal is critical mass, meaning more official publishers and more mirrors of the datasets people depend on.

## Terminology

- **Standard** is the governing noun. Portolan is a standard, plus the tools that make it real. "Ecosystem" describes the result, never the thing.
- The parts are **the standard** (defined in [portolan-spec](https://github.com/portolan-sdi/portolan-spec)), **the validator**, **the CLI**, **the registry**, and **the browser**.
- Name **people and agents together**. Portolan serves both, and neither comes first.
- Canonical links live in [urls.md](urls.md). Do not hardcode variants.
