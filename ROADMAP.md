## Roadmap

*This roadmap is a concise, high-level summary of the project vision. Detailed work is tracked in linked tickets.*

*Last updated: August 17, 2026*

Portolan aims to make geospatial data easy to share and use through cloud-native formats and high-quality metadata.

The project is still at an early stage. We are developing the specification, core tooling, and reference implementations. Our approach is to learn by doing: publish useful Portolan catalogs, see what works across real datasets and publishers, and feed those lessons back into the spec and tooling. Because we expect breaking changes in the short term, Portolan is currently best suited to early adopters.

The Portolan registry is one useful measure of our progress. The more kinds of data, publishers, formats, and use cases represented there, the more confident we can be that Portolan works across the geospatial ecosystem. Our initial goal is roughly 100 reference catalogs, including both official catalogs and useful mirrors.

Other important signs of maturity are spec stability and stable core tooling. We want to reach a point where real-world use no longer routinely exposes gaps that require breaking spec changes, and where publishers can create and maintain conformant catalogs with a stable v1.0 CLI.

After the core reaches that point, we will focus more heavily on expanding the tooling ecosystem and making Portolan accessible to publishers and users who do not work from the command line.

### Near term

* Publish a diverse set of reference catalogs and use them to test the spec and tooling against real-world data.
* [Release the Portolan CLI beta](https://github.com/portolan-sdi/portolan-cli/issues/638).
* [Publish core Portolan libraries through the `conda` ecosystem](https://github.com/portolan-sdi/portolan-cli/issues/644).
* Develop repository templates that make it easy for publishers to follow Portolan best practices.
* Improve catalog documentation and agent guidance so catalogs are easy for both people and software agents to understand and maintain.

### v1.0

* Reach a stable core specification that does not routinely require breaking changes.
* Release a stable v1.0 of the Portolan CLI.
* [Browse and import Portolan registry datasets directly from QGIS and GeoLibre](https://github.com/portolan-sdi/portolan-cli/issues/118), giving desktop GIS users an ArcGIS Hub-like way to discover and use Portolan data.
* [Support access-controlled and non-public Portolan data](https://github.com/portolan-sdi/portolan-cli/issues/120).

### Post-v1.0

* [Add normative Zarr support](https://github.com/portolan-sdi/portolan-spec/issues/132) once we have enough experience with real Zarr catalogs and the surrounding conventions and tooling are mature enough to define a useful conformance profile.
* [Support cloud-optimized point clouds through COPC](https://github.com/portolan-sdi/portolan-cli/issues/54).
* Align with the Apache Ossie specification where the two projects overlap.
* Add QGIS and GeoLibre publication tools, so publishers can create and manage Portolan catalogs from desktop GIS as well as from the CLI.
* [Support syncing changes back to upstream services such as ArcGIS](https://github.com/portolan-sdi/portolan-cli/issues/546), so Portolan catalogs can stay synchronized with the systems they were created from.
