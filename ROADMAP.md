## Roadmap

*This roadmap is a concise, high-level summary of the project vision. Detailed work is tracked in linked tickets.*

*Last updated: September 1, 2026*

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

These are things that people directly in our community are committed to working on soon.

 * Improvements to Styling - clarify the text and make styles more flexible, and [define raster styling](https://github.com/portolan-sdi/portolan-spec/issues/41) (and potentially encourage more standardization of styling).
 * Recommendations / best practices for global data set overviews - ie show aggregations for huge vector datasets and generate global overviews for gridded COG's.
 * Formalization of legend practices - styles can be used to generate some legends, but we should have a more formal way to specify legend hints for portolan consumers, see [this issue for discussion](https://github.com/portolan-sdi/portolan-spec/issues/118)
 * Tooling support in STAC Browser to enable item level search of stac-geoparquet as an alternative to STAC API's
 * [Collection level STAC GeoParquet](https://github.com/radiantearth/stac-geoparquet-spec/issues/17) and tooling support so that portolan browser and others can do full collection search of large Portolan catalogs (or aggregations of catalogs.
 * Tutorials for 1) using AI agent to query with portolan data 2) publishing data to Portolan.

### Medium Term

Not all of these may land before 1.0, as our current core community likely does not have the resources for them, but they are
things we see as important and hope to find people to help us with. Some depend on the overall geospatial ecosystems maturing
more, as we want Portolan to not be only for those on the bleeding edge.

 * [Add normative Zarr support](https://github.com/portolan-sdi/portolan-spec/issues/132) once we have enough experience with real Zarr catalogs and the surrounding conventions and tooling are mature enough to define a useful conformance profile.
 * [Support cloud-optimized point clouds through COPC](https://github.com/portolan-sdi/portolan-cli/issues/54).
 * Add Cloud-native [CityJSON](https://www.cityjson.org/) ([FlatCityBuf](https://www.cityjson.org/flatcitybuf/) / GeoParquet) support once we can get a useful conformance profile.
 * GeoParquet with overviews as a complete replacement for PMTiles. There's lots of discussion and experiments here, but it needs to coalesce and mature, and get wide tooling support.
 * Tooling to automatically convert from cloud-native formats to older formats (shapefile, geopackage, etc) on the fly, with easy integration into existing catalogs (ie they can offer more assets, but assets are generated on the fly), so users can just store their data in cloud-native formats but enable download in lots of different formats.
 * Easy to install / use tooling provide WMS/WFS/WMTS/XYZ tiles/Features API from portolan catalogs - may just be tutorials, or encouraging other tools to fully support Portolan.
 * [Hover / click hints](https://github.com/portolan-sdi/portolan-spec/issues/190) so that aware clients (like portolan browser) can enable mouse over / clicks with the provider recommended fields.

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
