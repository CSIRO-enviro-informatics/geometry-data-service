# Geometry data service

The Geometry Data Service (GDS) provides APIs for serving (spatial) geometries as RESTful separable first-class objects to spatial features over the web. The GDS provides access to multiple views of spatial geometries for the relevant reporting geographies included in Loc-I as Linked Data. Geometry data is provided in different forms (e.g. geometry as-is, centroid, metadata-only) and formats/serialisations (e.g. WKT, GeoJSON, SHP, RDF/GeoSPARQL). The GDS achieves this via Content Negotiation on spatial features stored in the Loc-I Geo-database, which hosts the geometries. This allows spatial features in Loc-I to embed URI-references to the geometry instead of embedding a geometry literal, optimising the RDF graph store for semantic queries rather than geospatial.

Background to the GDS can be found at the [original geometry data service github issue](https://github.com/CSIRO-enviro-informatics/loci.cat/issues/39#issue-535488760).

See this link to the [API](/api/) for the OpenAPI spec.

## Views supported

| MIME Type | Description | Returns |
|--------------|--------------|---------|
|text/html |Web interface |`<!DOCTYPE html><html lang="en">...`|
|text/plain |Well-Known Text |`POLYGON((113.1016 -38.062 ...))`|
|application/json | GeoJSON |`{"type":"Polygon","coordinates":...}`|
|text/turtle | RDF Turtle representation using GeoSPARQL | ```_:geom1 a geo:sfPolygon , geo:Geometry ; geo:asWKT "POLYGON((113.1016 -38.062 ...))"^^geo:wktLiteral .```|

Future work:

| MIME Type | Description | Returns |
|--------------|--------------|---------|
|application/geo+json | GeoJSON |`{"type":"Polygon","coordinates":...}`|
|application/gml+xml | GML |`<gml:Polygon><gml:Exterior>...`|
|application/octet-stream | Well-Known Binary | `01 06 00 00 20 E6 10 00 00 01...`|

Note: The above views extend a specification proposed by Regalia et al. 2017*.

* Regalia et al., Revisiting the Representation of and Need for Raw Geometries on the Linked Data Web, LDOW, 2017, http://ceur-ws.org/Vol-1809/article-04.pdf




