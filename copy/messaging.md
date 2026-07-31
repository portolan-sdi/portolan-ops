# Portolan messaging

This is the single source of truth for how Portolan describes itself. All collective public copy derives from it, written in the voice defined by [VOICE.md](../VOICE.md). It wins over any older copy anywhere in the org. Sections marked _to confirm_ are the known open items.

## One-liner

> Publish geospatial data as plain files in your own storage, connected into a searchable network.

## One paragraph

> Portolan publishes geospatial data as plain files in your own storage, with no servers, databases, or accounts. Cloud-optimized formats and structured metadata let people and agents work with and build on the data directly, while the registry links every catalog into a searchable network of open data.

## What is Portolan?

Portolan makes geospatial data easy to publish and easy to use. A catalog is plain files in your own storage, described so that a person or an agent can understand the data and query it directly. Publishing works the same way whether you are a satellite company releasing a planetary archive or a city publishing local cadastral data, and it requires no servers, databases, or accounts.

Under the hood, Portolan is an opinionated standard for cloud-native geospatial catalogs, plus the tooling around it. A catalog is a directory of open-format data on any S3-compatible bucket, described by structured [STAC](https://stacspec.org/en/) metadata and built on [COG](https://cogeo.org/), [GeoParquet](https://geoparquet.org/), [PMTiles](https://docs.protomaps.com/pmtiles/), [COPC](https://copc.io/), and [GeoZarr](https://geozarr.org/). The standard and the tools are open source under Apache-2.0. Each part raises the value of the others:

- The standard defines what a great catalog looks like.
- The validator proves a catalog meets it.
- The CLI makes catalogs easy to build.
- The registry links every catalog into a searchable network.

Your only costs are storage and egress, paid to your cloud provider. If Portolan disappeared tomorrow, every file in a catalog would still work in the tools you already use.

## Why Portolan?

**Open and interoperable.** Catalogs are built on established open formats like GeoParquet, COG, and STAC metadata. These work today in tools like DuckDB, BigQuery, Pandas, QGIS, and ArcGIS.

**Ready for people and agents.** A catalog describes itself in plain text and structured metadata. A person can read what the data is and where it came from. An agent can do the same, then query it directly with standard tools, no API or credentials needed. Because every catalog is described the same way, an agent can find a city's parcel data and a satellite archive, join them, and answer a question no single dataset could.

**Simple and scalable.** Running spatial data infrastructure normally means GeoServer or an Esri stack, with databases, services, and staff to keep them up. A Portolan catalog has none of that. Building one still takes work, which is what the CLI and validator are for, but once published it needs no maintenance, whether it holds megabytes or terabytes.

**Cheap and sovereign.** You choose where the data lives, including providers in your own country: AWS, Azure, GCS, MinIO, Hetzner, Scaleway, or any S3-compatible storage. You pay them for storage and bandwidth, and nothing else. No one sits between your organization and its data.

## Portolan philosophy

Portolan builds on existing standards rather than reinventing them. It is STAC 1.1.0 at its core and reuses established STAC extensions wherever they fit. On top of that, Portolan adds strong requirements on formats, statistics, catalog structure, and documentation. Those requirements let people and agents use a catalog directly from storage, with no server in between, and they set a higher quality bar than STAC alone requires.

The standard is prescriptive where that supports interoperability. Core standards like STAC and GeoParquet were built for long-term stability; Portolan sits on top of them and moves faster. Each version states what the community currently believes a great catalog looks like, and requirements will tighten or relax as cloud-native tooling matures.

Where the current landscape has gaps, Portolan writes down practices that until now have been informal. Usually that means contributing to STAC extensions or adding new ones. Sometimes it means a small, independent specification.

Portolan is AI-ready, not AI-first. Agents are the means, people are the ends. Best practices for working with agents are changing quickly, but the aim is fixed: a catalog should be as easy for an agent to use as it is for a person.

## The registry

The registry is a catalog of catalogs. It's a simple GitHub repository, so submitting a catalog just requires a pull request, and the registry itself is plain JSON. Anyone can read it, mirror it, or build on top of it.

The registry turns individual catalogs into a network. It gives search a place to start, so a person or an agent can find every registered dataset from one entry point. It also makes provenance visible: every catalog names its producer, its provider, and its host using the STAC provider extension. When the producer and the provider are the same organization, the catalog is official. When they differ, it is a mirror, and the registry shows both, meaning you can compare copies and choose the source you trust.

Because the registry lives in version control, it works the way open source works. For example, you can open a pull request against a dataset to flag a problem or suggest an improvement, or you can submit an example notebook showing how the data might be used. The data stays in the publisher's storage while the knowledge about it accumulates in the registry, in public.

## Who is Portolan for?

Portolan is for anyone who publishes geospatial data and anyone who uses it. The same standard covers a few files or a few billion.

### Publishers at scale

If you already run a large archive, Portolan cuts what it costs to operate and widens who can use it. With no services to maintain, the cost of publishing drops to storage. And a self-describing catalog reaches past the users willing to learn your API: analysts query it directly with standard tools, and agents can work with it unattended.

### New publishers

If running a server has kept your data unpublished, Portolan removes that requirement. A city or a small agency can put files in a bucket, run the CLI, and publish a catalog that passes the same validator a planetary archive passes. Nothing runs afterward, and the only recurring cost is storage. Data that stayed on internal drives for lack of a budget line can be public.

### Data consumers

Datasets that once required a specialist and a pipeline, like global building footprints, become catalogs you can browse, query, and open in QGIS, DuckDB, or a notebook. An analyst can also hand a question to an agent and let it find the relevant catalogs, query them, and return an answer. Getting the data and using the data are no longer separate projects.

### How the audiences reinforce each other

Large publishers give the registry data worth searching, which makes it worth joining for everyone else. Small publishers become findable the moment they join. And every consumer who mirrors or builds on a catalog adds another reason for the next publisher to show up.

## Who is building Portolan?

_To confirm. Do not name these organizations in public copy until this marker is removed._ Radiant Earth, Carto, Planet, Taylor Geospatial, and others. The full contributor list, and who is publishing with Portolan today, is pending in the messaging document.

## How to get involved

Start by using catalogs. Browse the registry, query a dataset, and tell us what worked and what didn't. Feedback filed as GitHub issues against a catalog or against the standard is the fastest way to improve both.

If a dataset you rely on isn't in the network, publish a Portolan mirror of it. National and global datasets are especially valuable, and the provider extension keeps provenance clear. If you build something with a catalog, submit an example notebook so the next person starts where you left off.

If you publish data, implement the standard. The CLI does most of the work of building a catalog, the validator tells you when you have met the bar, and the [registry](https://github.com/portolan-sdi/portolan-registry) makes your data findable the moment you submit it. If your agency is the authoritative source for a dataset, an official catalog from you becomes the copy everyone else builds on, and any community mirrors point back to it.

## What is the future for Portolan?

Portolan's goal is to make it easy for people and agents to find, combine, and use spatial data at any scale. We envision a world where most public geospatial data lives in cloud-optimized, well-documented Portolan catalogs. That critical mass will make hard analyses simple and new applications possible.

The [Finland SDI demo](https://jatorre.github.io/carto-ogc-helsinki/webapp/index.html) is an early example. Because the underlying data lives in Portolan catalogs, an autonomous agent can run assessments for data center and electrification planning on its own, combining national- and EU-scale datasets like building footprints, flood hazard zones, and population grids.

As we develop Portolan, we will encourage official publishers to adopt it and support unofficial mirrors of key datasets that many users depend on. We will improve guidance for agents as we build, and keep evolving the standard with the community as we learn what makes a great spatial data product.

## Terminology

- **Standard** is the governing noun. Portolan is a standard, plus the tools that make it real. "Ecosystem" describes the result, never the thing.
- The parts are **the standard** (defined in [portolan-spec](https://github.com/portolan-sdi/portolan-spec)), **the validator**, **the CLI**, **the registry**, and **the browser**.
- Name **people and agents together**. Portolan serves both, and neither comes first.
- Canonical links live in [urls.md](urls.md). Do not hardcode variants.
