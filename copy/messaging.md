# Portolan messaging

This is the single source of truth for how Portolan describes itself. All collective public copy derives from it, written in the voice defined by [VOICE.md](../VOICE.md). It wins over any older copy anywhere in the org.

Every claim here comes from the shipped website and the launch post. When the site changes, change this file with it.

## One-liner

> Portolan makes geospatial data easy to share and use.

## One paragraph

> Portolan is an open-source specification and toolkit that combines cloud-native file formats with clear metadata and documentation so that people and agents can publish and use data at any scale. A catalog is plain files in object storage, with no servers, databases, or accounts. A registry links every catalog into a network anyone can search.

## What is Portolan?

A Portolan catalog is a directory of open-format data on any S3-compatible bucket, described so that a person or an agent can understand it and query it directly. Publishing works the same way whether a satellite company releases a planetary archive or a city releases its cadastral data. Neither needs a server, a database, or an account.

Underneath, Portolan is an opinionated specification for cloud-native geospatial catalogs, plus the tooling that makes it real. Catalogs use [GeoParquet](https://geoparquet.org/) and [PMTiles](https://docs.protomaps.com/pmtiles/) for vector data and [COG](https://cogeo.org/) for raster, organized with [STAC](https://stacspec.org/en/) metadata. Support for `Zarr` and [COPC](https://copc.io/) is planned rather than shipped. Every part is open source under Apache-2.0, and each one raises the value of the others:

- The specification defines what a good catalog looks like.
- `rashid`, the validator, proves a catalog meets it.
- The CLI makes catalogs straightforward to build.
- The agent skills orchestrate publication from start to finish.
- The registry links every catalog into a searchable network.
- The browser lets anyone explore a catalog in the open.

Portolan also requires documentation. Every catalog and collection carries a README and an `AGENTS.md` file, so the caveats, access patterns, and appropriate uses live next to the data rather than in the heads of domain experts. The requirement takes inspiration from [FAIR](https://www.go-fair.org/fair-principles/) and [Candid Core](https://lettersfromthreadedfoundry.substack.com/p/candid-core-framework).

## Why Portolan?

**Open and interoperable.** Portolan builds on open standards, so data drop straight into QGIS, ArcGIS, Pandas, DuckDB, or BigQuery. Nothing about a published catalog depends on Portolan tooling to read it.

**Simple, cheap, scalable, sovereign.** Your data live in any S3-compatible cloud storage, in any jurisdiction you choose. Catalogs scale from megabytes to petabytes with no servers, databases, or custom APIs. Your only costs are what you pay your cloud provider.

**Built for people and agents.** Catalogs are structured, formatted, and documented so that both can find, understand, and use them. Browse the registry yourself, or point an agent at it and see what it does.

## How it works

The CLI and the agent skills turn existing data into a catalog in four steps.

1. **Convert.** Shapefiles, GeoPackages, a WFS endpoint, or an Esri service become GeoParquet and PMTiles for vector, and COG for raster.
2. **Catalog.** The cloud-optimized data are organized as a STAC catalog with metadata and documentation.
3. **Publish.** The catalog goes to any S3-compatible storage, such as AWS, GCS, Hetzner, or MinIO. Nothing runs afterward.
4. **Use.** The data open in QGIS, ArcGIS, or Python, or the catalog URL goes to an agent.

## Portolan philosophy

Portolan builds on existing standards rather than reinventing them. It is STAC at its core and reuses established STAC extensions wherever they fit. On top of that it adds requirements on formats, statistics, catalog structure, and documentation. Those requirements are what let people and agents use a catalog directly from storage, with no server in between.

Portolan is opinionated because the alternative fails quietly. GeoParquet published without bbox structs and spatial ordering makes spatial queries far slower. Data hosted without CORS cannot be read by a web app at all. The specification writes down which choices work, and `rashid` checks them against the bytes rather than against the metadata alone.

The specification is prescriptive where that supports interoperability. Core standards like STAC and GeoParquet were built for long-term stability, and Portolan sits on top of them and moves faster. Each version states what the community currently believes a good catalog looks like. Requirements will tighten or relax as cloud-native tooling matures.

Portolan is AI-ready, not AI-first. Agents are a means and people are the end. A catalog should be as easy for an agent to use as it is for a person.

## The registry

The registry is a catalog of independently hosted catalogs, and the first step toward a federated network for geospatial data. It is a GitHub repository. Submitting a catalog takes a pull request, and the registry itself is plain JSON that anyone can read, mirror, or build on.

The registry makes catalogs from many publishers searchable in one place while the data stay distributed. The underlying bytes never leave the publisher's storage, and users query them directly from the source. If the registry disappeared tomorrow, every registered catalog would keep working.

It also makes provenance visible. Every catalog names its producer, provider, and host through the STAC provider extension. A catalog whose producer and provider are the same organization is official. Where they differ, it is a mirror. The registry shows both, so you can compare copies and choose the source you trust.

Because the registry lives in version control, it works the way open source works. You can open a pull request against a dataset to flag a problem, or submit an example notebook showing how the data can be used. The data stay in the publisher's storage while knowledge about them accumulates in public.

## Who is Portolan for?

Portolan is for anyone who publishes geospatial data and anyone who uses it. The same specification covers a few files and a few billion.

### Large publishers

Large archives, such as satellite imagery or national-scale geoportals, are expensive to store and hard to maintain. Portolan cuts the recurring cost close to storage and transfer alone, because there is no serving layer sized for peak demand. A self-describing catalog also reaches past the users willing to learn a bespoke API. [Fields of the World](https://fieldsofthe.world) publishes 369 TB of agricultural field boundaries this way, and served 106.6 TB in the 28 days ending August 27, 2026.

### Small publishers

Many city governments, NGOs, and smaller producers cannot afford the cost or complexity of publishing with GeoServer or an Esri stack. Portolan removes the requirement. A small agency can put files in a bucket, run the CLI, and publish a catalog that passes the same validator a planetary archive passes. Data that sat on internal drives for lack of a budget line can be public.

### Data users

Most geospatial data is scattered, poorly documented, and stored in ways that make it hard to use. Portolan requires clear metadata and documentation, uses formats designed for direct access, and provides a central registry. Datasets that once needed a specialist pipeline become catalogs you can browse, query, or open in QGIS, DuckDB, or a notebook. An analyst can also hand a question to an agent and let it find the catalogs, query them, and return an answer.

### How the audiences reinforce each other

Large publishers give the registry data worth searching, which makes it worth joining for everyone else. Small publishers become findable the moment they join. Every consumer who mirrors or builds on a catalog adds another reason for the next publisher to show up.

## Common questions

**Isn't this just STAC and cloud-optimized formats?** Those standards deliberately leave implementation choices open. Portolan defines and validates a quality floor. It requires GeoParquet to be spatially ordered, with statistics that let clients skip row groups. COGs must carry overviews and embedded statistics. Hosted assets must support HTTP range requests and CORS.

**Why not GeoServer, PostGIS, or an OGC API?** For public, read-heavy data, a dedicated serving layer is usually unnecessary. DuckDB queries remote GeoParquet with filtering, joins, and spatial operations. PMTiles serves interactive maps with no tile server. You can still add an API or a database when a use case needs one. Portolan removes the requirement that every dataset depend on one to be reachable at all.

**What does conformance guarantee?** A catalog does not conform because it declares the Portolan extension. It conforms if it passes `rashid`, which inspects the data itself, not only the metadata.

**Does this trade one proprietary platform for another?** Portolan standardizes the published catalog, not the cloud provider, the workflow, the interface, the engine, or the vendor. If a commercial product builds your catalog and you stop using that product, the catalog still works and another tool can take over.

**Does it standardize my data model?** No. Portolan standardizes how data are packaged, documented, hosted, and accessed. Semantic standards and shared schemas sit on top where they are useful.

**Why are agents part of a publishing specification?** Agents inspect and query many datasets quickly, so Portolan assumes catalogs will be read by software at scale. The `AGENTS.md` requirement exists for that. Agents are not required to publish or consume Portolan data.

**What can Portolan not do yet?** Access-controlled data is planned for v1.0. Transactional editing is not supported. Normative support for `Zarr` and COPC is still a gap. Portolan is early stage and breaking changes remain possible, so it currently suits early adopters.

## How to get involved

Publish data as a Portolan catalog and tell us how it went. Feedback on what worked and what did not is the fastest way to improve the specification and the tooling. It matters most when your implementation differs from the catalogs that already exist.

If a dataset you rely on is not in the network, publish a mirror of it. National and global datasets are especially valuable, and the provider extension keeps the provenance clear. If you build something on a catalog, submit an example notebook so the next person starts where you left off.

If you publish data, implement the specification. The CLI does most of the work of building a catalog, `rashid` tells you whether you met the bar, and the [registry](https://github.com/portolan-sdi/portolan-registry) makes your data findable the moment you submit it. When an agency publishes the official catalog for a dataset it is authoritative for, that catalog becomes the copy everyone else builds on.

Contributions to the specification and the tooling are welcome as bug reports, feature requests, and pull requests. The community meets weekly on Fridays at 10am CET. Join the [#portolan channel](https://cloudnativegeo.slack.com/archives/C0A1JBH9529) in the Cloud-Native Geospatial Forum Slack, or the [Google Group](https://groups.google.com/g/portolan).

## What is the future for Portolan?

The goal is for Portolan to become the default way of publishing geospatial data. If mapping agencies, cities, researchers, NGOs, and global providers publish catalogs in the same basic shape, datasets can stay distributed across thousands of publishers. They become searchable and directly usable across organizational and geographic boundaries.

The near-term work is to expand the set of reference catalogs, stabilize the core specification, and reach a stable v1.0 CLI. The initial target is roughly one hundred reference catalogs covering a range of use cases and geographic extents. After that, the focus moves to reaching publishers and users who do not work from the command line.

Success means an ecosystem forms around the specification rather than Portolan depending on the tools we build ourselves. Community and commercial implementations should add capabilities, and existing GIS tools should read Portolan metadata directly.

## Terminology

- **Specification** is the governing noun. There is the Portolan specification, plus the tools that make it real. "Ecosystem" describes the result, never the thing itself.
- The parts are **the specification** (defined in [portolan-spec](https://github.com/portolan-sdi/portolan-spec)), **rashid** (the validator), **the CLI**, **the skills**, **the registry**, and **the browser**. Name the validator `rashid` rather than "the validator" alone.
- Say Portolan **uses** GeoParquet, PMTiles, COG, and STAC. Say support for `Zarr` and COPC is **planned**. Do not list them among the formats a catalog is built on.
- Name **people and agents together**. Portolan serves both, and neither comes first.
- Canonical links live in [urls.md](urls.md). Do not hardcode variants.
