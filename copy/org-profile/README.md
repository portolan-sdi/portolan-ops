# Portolan

**Publish geospatial data as plain files in your own storage, connected into a searchable network.**

Portolan publishes geospatial data as plain files in your own storage, with no servers, databases, or accounts. Cloud-optimized formats and structured metadata let people and agents work with and build on the data directly, while the registry links every catalog into a searchable network of open data.

## Why Portolan

- **Open and interoperable.** The standard and the tools are open source under Apache-2.0. Catalogs are built on established open formats: [STAC](https://stacspec.org/en/), [GeoParquet](https://geoparquet.org/), [COG](https://cogeo.org/), [PMTiles](https://docs.protomaps.com/pmtiles/), [COPC](https://copc.io/), and [GeoZarr](https://geozarr.org/). These work today in tools like DuckDB, BigQuery, Pandas, QGIS, and ArcGIS.
- **Ready for people and agents.** A catalog describes itself in plain text and structured metadata. A person can read what the data is and where it came from. An agent can do the same, then query it directly with standard tools, no API or credentials needed.
- **Simple and scalable.** Running spatial data infrastructure normally means GeoServer or an Esri stack, with databases, services, and staff to keep them up. A Portolan catalog has none of that, and it needs no maintenance whether it holds megabytes or terabytes.
- **Cheap and sovereign.** You choose where the data lives, including providers in your own country: AWS, Azure, GCS, MinIO, Hetzner, Scaleway, or any S3-compatible storage. You pay them for storage and bandwidth, and nothing else.

## How it works

The CLI converts local geospatial files (Shapefiles, GeoTIFFs, and more) into cloud-native formats, validates them, and syncs the result to object storage as a STAC catalog:

```bash
portolan init
portolan add demographics/
portolan check --fix
portolan push s3://my-catalog
```

The resulting catalog is browsable at standard URLs and queryable from any tool that speaks Parquet or COG. The validator proves it meets the standard, and the [registry](https://github.com/portolan-sdi/portolan-registry) links it into a searchable network of open data.

## Repositories

### The standard

| Repository | Description |
|---|---|
| [portolan-spec](https://github.com/portolan-sdi/portolan-spec) | The Portolan specification. Ground truth for everything below. |

### Implementations

| Repository | Description | Language |
|---|---|---|
| [portolan-cli](https://github.com/portolan-sdi/portolan-cli) | CLI for building and publishing catalogs | Python |
| [rashid](https://github.com/portolan-sdi/rashid) | Validator for Portolan catalogs | Python |
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
| [portolan-data](https://github.com/portolan-sdi/portolan-data) | Tracking and coordination for official Portolan catalogs and mirrors |
| [portolan-skills](https://github.com/portolan-sdi/portolan-skills) | Claude Code skills for working with Portolan catalogs |
| [portolan-bootstrapper](https://github.com/portolan-sdi/portolan-bootstrapper) | Bootstrapping core open data for local use |
| [portolan-ops](https://github.com/portolan-sdi/portolan-ops) | Org ground truth: copy, branding, norms, CI, templates |

## Get involved

Start by using catalogs. Browse the [registry](https://github.com/portolan-sdi/portolan-registry), query a dataset, and tell us what worked and what didn't. Feedback filed as GitHub issues against a catalog or against the standard is the fastest way to improve both.

If a dataset you rely on isn't in the network, publish a Portolan mirror of it. If you publish data yourself, implement the standard: the CLI does most of the work, the validator tells you when you have met the bar, and the registry makes your data findable the moment you submit it.

## Learn more

Visit [portolan-sdi.org](https://www.portolan-sdi.org/) for the full overview, architecture details, and getting-started guide. Questions and discussion go to the [Portolan Google Group](https://groups.google.com/g/portolan) and the [Portolan channel](https://cloudnativegeo.slack.com/archives/C0A1JBH9529) in the Cloud-Native Geo Slack.
