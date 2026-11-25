## Roadmap

*This roadmap is a concise, high-level summary of the project vision. Detailed work is tracked in linked tickets.*

*Last updated: November 25, 2026*

Portolan aims to make geospatial data easy to share and use through cloud-native formats and high-quality metadata.

The project is still at an early stage. Work continues on the specification, the core tooling, and the reference implementations. Our approach is to learn by doing. We publish useful Portolan catalogs and watch what works across real datasets and publishers. Those lessons then go back into the spec and the tooling. Because we expect breaking changes in the short term, Portolan is currently best suited to early adopters.

The [Portolan registry](https://github.com/portolan-sdi/portolan-registry) is one useful measure of our progress. The more kinds of data, publishers, formats, and use cases represented there, the more confident we can be that Portolan works across the geospatial ecosystem. In November 2026 the registry passed our first goal of roughly 100 reference catalogs. It lists 101 catalogs: 8 official catalogs and 92 mirrors. Our next goal is 25 official catalogs that publishers run themselves.

Other important signs of maturity are spec stability and stable core tooling. We want to reach a point where real-world use no longer routinely exposes gaps that require breaking spec changes, and where publishers can create and maintain conformant catalogs with a stable v1.0 CLI.

After the core reaches that point, we will focus more heavily on expanding the tooling ecosystem and making Portolan accessible to publishers and users who do not work from the command line.

Checked items are done. Items marked **In progress** link to the work we track.

### Near term

- [ ] **In progress:** Publish a diverse set of reference catalogs and use them to test the spec and tooling against real-world data. The registry lists 101 catalogs.
- [x] [Release the Portolan CLI beta](https://github.com/portolan-sdi/portolan-cli/issues/638). The CLI released [v1.0.0b0](https://github.com/portolan-sdi/portolan-cli/releases/tag/v1.0.0b0) on 2026-08-31.
- [ ] Release a v1.0 release candidate of the Portolan CLI.
- [ ] [Publish core Portolan libraries through the `conda` ecosystem](https://github.com/portolan-sdi/portolan-cli/issues/644).
- [ ] **In progress:** Improve catalog documentation and agent guidance so catalogs are easy for both people and software agents to understand and maintain. Tracking: [portolan-skills](https://github.com/portolan-sdi/portolan-skills).
- [ ] **In progress:** Define how catalogs synchronize with [live sources such as ArcGIS servers](https://github.com/portolan-sdi/portolan-data/issues/23). The Portolan CLI resumes ArcGIS extracts from `lastEditDate` ([portolan-cli#546](https://github.com/portolan-sdi/portolan-cli/issues/546)). The [automated-catalog-updates skill](https://github.com/portolan-sdi/portolan-skills/blob/main/skills/automated-catalog-updates/SKILL.md) runs scheduled updates for three reference catalogs.
- [x] Decide whether the specification needs a simple last-updated field. [Spec v0.3.0](https://github.com/portolan-sdi/portolan-spec/releases/tag/v0.3.0) requires sync tools to set `updated` on each mirror catalog and collection they check (`PORTO-CORE-057`). The spec does not require `versions.json` (`PORTO-CORE-012`).
- [ ] **In progress:** Document or build services that expose Portolan catalogs through WMS, WFS, WMTS, XYZ tiles, or OGC API Features. Tracking:
  - [geoserver-portolan](https://github.com/geoverse-dev/geoserver-portolan) creates GeoServer layers from GeoParquet, COG, and PMTiles assets. Its v0.5.0 release came out on 2026-11-20.
  - [fastgeoapi](https://geobeyond.github.io/fastgeoapi/operators/how-to/portolan-ingest/) turns a Portolan catalog into pygeoapi resources for GeoParquet and PMTiles.

### Short term

Community contributors plan this work.

- [x] Define styling for classified rasters. Spec v0.3.0 uses the STAC classification extension (`PORTO-FMT-049` to `PORTO-FMT-059`).
- [ ] Clarify the styling text, make styles more flexible, and [define styling for continuous rasters](https://github.com/portolan-sdi/portolan-spec/issues/41).
- [x] Document best practices for overviews of gridded COGs. Spec v0.3.0 recommends an overview COG for collections of many rasters (`PORTO-FMT-067` to `PORTO-FMT-072`).
- [ ] Document best practices for global overviews of large vector datasets.
- [ ] [Define legend hints](https://github.com/portolan-sdi/portolan-spec/issues/118) that Portolan clients can use.
- [ ] Add item-level STAC GeoParquet search to STAC Browser as an alternative to STAC APIs.
- [ ] Add [collection-level STAC GeoParquet](https://github.com/radiantearth/stac-geoparquet-spec/issues/17). This supports searches across large catalogs and catalog aggregations.
- [ ] Write tutorials for agent queries and data publication.
- [ ] **In progress:** [Add normative Zarr support](https://github.com/portolan-sdi/portolan-spec/issues/132) after the community tests real Zarr catalogs and can define a useful conformance profile. Spec v0.3.0 adds an [incubating Zarr v3 profile](https://github.com/portolan-sdi/portolan-spec/blob/v0.3.0/specs/incubating/zarr.md) outside conformance.

### Medium term

These items need more contributors or further ecosystem work. Some may land after v1.0.

- [ ] [Support cloud-optimized point clouds through COPC](https://github.com/portolan-sdi/portolan-cli/issues/54).
- [ ] Add cloud-native [CityJSON](https://www.cityjson.org/) support through [FlatCityBuf](https://www.cityjson.org/flatcitybuf/) or GeoParquet after a useful conformance profile exists.
- [ ] Evaluate GeoParquet with overviews as a replacement for PMTiles. This work needs wider implementation and tool support.
- [ ] Convert cloud-native files to older formats on demand. Let catalogs offer Shapefile or GeoPackage assets without storing duplicate files.
- [ ] [Define hover and click hints](https://github.com/portolan-sdi/portolan-spec/issues/190) that clients can map to provider-recommended fields.
- [ ] **In progress:** Align with the Apache Ossie specification where the two projects overlap. Tracking: [stac-osi-extension](https://github.com/portolan-sdi/stac-osi-extension).
- [ ] **In progress:** Add Apache Iceberg support and compatibility. Spec v0.3.0 accepts native geospatial Parquet from Iceberg writers (`PORTO-FMT-080`). Tracking: [stac-iceberg-extension](https://github.com/portolan-sdi/stac-iceberg-extension).

### v1.0

- [ ] Reach a stable core specification that does not routinely require breaking changes.
- [ ] Release a stable v1.0 of the Portolan CLI.
- [x] [Browse and import Portolan registry datasets directly from QGIS and GeoLibre](https://github.com/portolan-sdi/portolan-cli/issues/118), giving desktop GIS users an ArcGIS Hub-like way to discover and use Portolan data. The [QGIS registry plugin](https://github.com/portolan-sdi/portolan-registry-qgis) reached v0.3.1 on 2026-10-20. [GeoLibre added a Portolan catalog browser](https://github.com/opengeos/GeoLibre/pull/2371) on 2026-09-13.
- [ ] [Support access-controlled and non-public Portolan data](https://github.com/portolan-sdi/portolan-cli/issues/120).

### Post-v1.0

- [ ] Add QGIS and GeoLibre publication tools, so publishers can create and manage Portolan catalogs from desktop GIS as well as from the CLI.
- [ ] Support syncing changes back to upstream services such as ArcGIS, so Portolan catalogs can stay synchronized with the systems they were created from.
