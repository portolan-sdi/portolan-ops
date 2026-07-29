# Portolan

**Publish geospatial data as plain files in your own storage, connected into a searchable network.**

Portolan publishes geospatial data as plain files in your own storage, with no servers, databases, or accounts. Cloud-optimized formats and structured metadata let people and agents work with and build on the data directly, while the registry links every catalog into a searchable network of open data.

## Why Portolan

Spatial data infrastructure still assumes servers, databases, and specialists. Portolan doesn't.

- **Open and interoperable.** Everything is Apache-2.0 and built on existing standards: [STAC](https://stacspec.org/en/), [GeoParquet](https://geoparquet.org/), [COG](https://cogeo.org/), [PMTiles](https://docs.protomaps.com/pmtiles/), [COPC](https://copc.io/), and [GeoZarr](https://geozarr.org/). These formats work across DuckDB, BigQuery, Pandas, and desktop GIS like QGIS and ArcGIS, so your data stays useful with or without Portolan.
- **Readable by people and machines alike.** A catalog describes itself in plain text and structured metadata, so a person or an agent can find the data and query it without a bespoke API to learn.
- **Simple.** A Portolan catalog is files in a bucket. Nothing runs, so nothing needs maintenance.
- **Low cost.** The whole budget is storage plus egress, paid to your cloud provider, not to us.
- **Sovereign.** Host on AWS, GCS, Azure, MinIO, Hetzner, Scaleway, or any S3-compatible storage. No foreign vendor sits between your agency and its data.

## How it works

The CLI converts local geospatial files (Shapefiles, GeoTIFFs, and more) into cloud-native formats, validates them, and syncs the result to object storage as a STAC catalog:

```bash
portolan init
portolan add demographics/
portolan check --fix
portolan push s3://my-catalog
```

The resulting catalog is browsable at standard URLs and queryable from any tool that speaks Parquet or COG. The same setup handles megabytes or terabytes, and passing the validator is what conformance means.

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

## Learn more

Visit [portolan-sdi.org](https://www.portolan-sdi.org/) for the full overview, architecture details, and getting-started guide. Questions and discussion go to the [Portolan Google Group](https://groups.google.com/g/portolan) and the [Portolan channel](https://cloudnativegeo.slack.com/archives/C0A1JBH9529) in the Cloud-Native Geo Slack.
