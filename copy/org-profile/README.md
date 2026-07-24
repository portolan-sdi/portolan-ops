# Portolan

**Publish geospatial data without a portal.**

Portolan is an open standard, plus the tools that make it real, for publishing geospatial data as cloud-native files on object storage. It combines [STAC](https://stacspec.org/), [GeoParquet](https://geoparquet.org/), and [Cloud-Optimized GeoTIFF](https://www.cogeo.org/) so governments and open data publishers can share spatial datasets at low cost. No servers, no databases, no proprietary licenses.

## Why Portolan

- **Open.** Apache-2.0 across the organization, open formats, open governance. Your data stays portable.
- **Low cost.** You pay for storage and egress. Small catalogs run on dollars a month.
- **Sovereign.** Data lives in your buckets on AWS, GCS, Azure, MinIO, or any S3-compatible storage.
- **Tool-agnostic.** Query with DuckDB, Snowflake, BigQuery, Databricks, or Pandas, and with standard GIS tools.
- **For people and agents.** STAC metadata makes catalogs browsable by humans and queryable by LLM agents alike.

## How it works

The CLI converts local geospatial files (Shapefiles, GeoTIFFs, and more) into cloud-native formats, validates them, and syncs the result to object storage as a STAC catalog:

```bash
portolan init
portolan add demographics/
portolan check --fix
portolan push s3://my-catalog
```

The resulting catalog is browsable at standard URLs and queryable from any tool that speaks Parquet or COG.

## Repositories

### The standard

| Repository | Description |
|---|---|
| [portolan-spec](https://github.com/portolan-sdi/portolan-spec) | The Portolan specification. Ground truth for everything below. |

### Implementations

| Repository | Description | Language |
|---|---|---|
| [portolan-cli](https://github.com/portolan-sdi/portolan-cli) | CLI for building and publishing catalogs | Python |
| [reis](https://github.com/portolan-sdi/reis) | Validator for Portolan catalogs | Python |
| [portolan-registry](https://github.com/portolan-sdi/portolan-registry) | Registry of public Portolan catalogs | Python |
| [portolan-browser](https://github.com/portolan-sdi/portolan-browser) | UI for browsing and searching catalogs | JavaScript |
| [portolan-nl-demo](https://github.com/portolan-sdi/portolan-nl-demo) | Demo catalog browser for Netherlands data | JavaScript |

### STAC extensions

| Repository | Description |
|---|---|
| [stac-partition-extension](https://github.com/portolan-sdi/stac-partition-extension) | Hive-style partition metadata for STAC Collections |
| [stac-iceberg-extension](https://github.com/portolan-sdi/stac-iceberg-extension) | Apache Iceberg table access and versioning metadata |
| [stac-osi-extension](https://github.com/portolan-sdi/stac-osi-extension) | Links STAC objects to an OSI (Apache Ossie) semantic model |

### Tooling and coordination

| Repository | Description |
|---|---|
| [portolan-skills](https://github.com/portolan-sdi/portolan-skills) | Claude Code skills for working with Portolan catalogs |
| [portolan-bootstrapper](https://github.com/portolan-sdi/portolan-bootstrapper) | Bootstrapping core open data for local use |
| [portolan-ops](https://github.com/portolan-sdi/portolan-ops) | Org ground truth: copy, branding, norms, CI, templates |

## Learn more

Visit [portolan-sdi.org](https://www.portolan-sdi.org/) for the full overview, architecture details, and getting-started guide. Join the conversation in the [Portolan Google Group](https://groups.google.com/g/portolan).
