## Roadmap

*This roadmap is a concise, high-level summary of the project vision. Detailed work is tracked in linked tickets.*

*Last updated: September 2, 2026*

Portolan aims to make geospatial data easy to share and use through cloud-native formats and high-quality metadata.

The project is still at an early stage. We are developing the specification, core tooling, and reference implementations. Our approach is to learn by doing: publish useful Portolan catalogs, see what works across real datasets and publishers, and feed those lessons back into the spec and tooling. Because we expect breaking changes in the short term, Portolan is currently best suited to early adopters.

The Portolan registry is one useful measure of our progress. The more kinds of data, publishers, formats, and use cases represented there, the more confident we can be that Portolan works across the geospatial ecosystem. Our initial goal is roughly 100 reference catalogs, including both official catalogs and useful mirrors.

Other important signs of maturity are spec stability and stable core tooling. We want to reach a point where real-world use no longer routinely exposes gaps that require breaking spec changes, and where publishers can create and maintain conformant catalogs with a stable v1.0 CLI.

After the core reaches that point, we will focus more heavily on expanding the tooling ecosystem and making Portolan accessible to publishers and users who do not work from the command line.

### Near term

* Publish a diverse set of reference catalogs and use them to test the spec and tooling against real-world data.
* [Release the Portolan CLI beta](https://github.com/portolan-sdi/portolan-cli/issues/638).
* [Publish core Portolan libraries through the `conda` ecosystem](https://github.com/portolan-sdi/portolan-cli/issues/644).
* Improve catalog documentation and agent guidance so catalogs are easy for both people and software agents to understand and maintain.

### Short term

Community contributors plan this work.

* Clarify the styling text, make styles more flexible, and [define raster styling](https://github.com/portolan-sdi/portolan-spec/issues/41).
* Document best practices for global dataset overviews. Cover large vector datasets and gridded COGs.
* [Define legend hints](https://github.com/portolan-sdi/portolan-spec/issues/118) that Portolan clients can use.
* Add item-level STAC GeoParquet search to STAC Browser as an alternative to STAC APIs.
* Add [collection-level STAC GeoParquet](https://github.com/radiantearth/stac-geoparquet-spec/issues/17). This supports searches across large catalogs and catalog aggregations.
* Write tutorials for agent queries and data publication.
* Define how catalogs synchronize with [live sources such as ArcGIS servers](https://github.com/portolan-sdi/portolan-data/issues/23). Decide whether the specification needs a simple last-updated field. The Portolan CLI keeps `versions.json` outside the specification while we test more catalogs.

### Medium term

These items need more contributors or further ecosystem work. Some may land after v1.0.

* [Add normative Zarr support](https://github.com/portolan-sdi/portolan-spec/issues/132) after the community tests real Zarr catalogs and can define a useful conformance profile.
* [Support cloud-optimized point clouds through COPC](https://github.com/portolan-sdi/portolan-cli/issues/54).
* Add cloud-native [CityJSON](https://www.cityjson.org/) support through [FlatCityBuf](https://www.cityjson.org/flatcitybuf/) or GeoParquet after a useful conformance profile exists.
* Evaluate GeoParquet with overviews as a replacement for PMTiles. This work needs wider implementation and tool support.
* Convert cloud-native files to older formats on demand. Let catalogs offer Shapefile or GeoPackage assets without storing duplicate files.
* Document or build services that expose Portolan catalogs through WMS, WFS, WMTS, XYZ tiles, or OGC API Features.
* [Define hover and click hints](https://github.com/portolan-sdi/portolan-spec/issues/190) that clients can map to provider-recommended fields.

### v1.0

* Reach a stable core specification that does not routinely require breaking changes.
* Release a stable v1.0 of the Portolan CLI.
* [Browse and import Portolan registry datasets directly from QGIS and GeoLibre](https://github.com/portolan-sdi/portolan-cli/issues/118), giving desktop GIS users an ArcGIS Hub-like way to discover and use Portolan data.
* [Support access-controlled and non-public Portolan data](https://github.com/portolan-sdi/portolan-cli/issues/120).

### Post-v1.0

* Align with the Apache Ossie specification where the two projects overlap.
* Add QGIS and GeoLibre publication tools, so publishers can create and manage Portolan catalogs from desktop GIS as well as from the CLI.
* [Support syncing changes back to upstream services such as ArcGIS](https://github.com/portolan-sdi/portolan-cli/issues/546), so Portolan catalogs can stay synchronized with the systems they were created from.
* Iceberg support / compatibility.
