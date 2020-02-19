# Geometry data service

The Geometry Data Service (GDS) is a lightweight API that has been developed for serving RESTful geometries over the web. In particular, these were 
the functions the GDS provides:
* minting URIs for geometries to enable Linked Data functionality
* content-negotiation for formats and representations of the geometry
* search by point for relevant geometries across the geometry store
* parameterise the profile of the geometry representation for a Loc-I Feature (geometry of a feature with a resolution in metres, bounding box, centroid, simplified vs. complex geom, projection/CRS)

![Geometry Data Service architecture](images/geometry-data-service.png "Geometry Data Service architecture")

The current Geometry Data Service uses the [pyLDAPI](https://github.com/RDFLib/pyLDAPI) to implement the Linked Data APIs.

## Quickstart 
```
$ cd api
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ export FLASK_APP=app.py
$ export FLASK_ENV=development
$ flask run --port=3000 --host=0.0.0.0
```

Specify env variables for the db connection
```
$ export GSDB_DBNAME=gis
$ export GSDB_HOSTNAME=localhost
$ export GSDB_PORT=5432
$ export GSDB_USER=jon
$ export GSDB_PASS=jon
```

Once flask is running, go to http://localhost:3000 and use links provided

## Deploy using docker

An alternative to the simple flask run is via docker. 

You can use the Docker Hub image at https://hub.docker.com/r/csiroenvinf/geometry-data-service.
```
$ docker pull csiroenvinf/geometry-data-service
```

```
$ docker run --name gservice -d -p 3000:3000 csiroenvinf/geometry-data-service 
```

Or with environment variables
```
$ docker run  -e GSDB_DBNAME=gis -e GSDB_HOSTNAME=localhost -e GSDB_PORT=5432 -e GSDB_USER=user -e GSDB_PASS=pass -p 3000:3000 --network host -it csiroenvinf/geometry-data-service 
```


## Scope

###  Mint URIs for geometries and provide an API for it

* Only store (geo-referenced) geometries
* Scoped to Earth initially

Implies 
* Ability to embed a URI Reference in a Loc-I feature instance 
* Selecting a predicate to associate a feature with the geometry URI reference (GeoSPARQL or something else?)
* Returning the geometry representation from somewhere (from a remote service or local geodatabase cache)
* Content negotiation by profiles


### Out of scope

Performing extensive utility calculations on geometries (i.e. [ArcGIS GeometryService](https://www.arcgis.com/home/item.html?id=2e18b487043641538f02028cc2495c0e)).


## Content negotiation interfaces

The Geometry Data Service implements and extends conneg arrangement proposed by (Regalia et al. 2017). 
Conneg interfaces the GDS implements are shown below:

| MIME Type | Description | Returns |
|--------------|--------------|---------|
|text/html |Web interface |`<!DOCTYPE html><html lang="en">...`|
|text/plain |Well-Known Text |`POLYGON((113.1016 -38.062 ...))`|
|application/json | GeoJSON |`{"type":"Polygon","coordinates":...}`|
|text/turtle | RDF Turtle representation using GeoSPARQL | ```_:geom1 a geo:sfPolygon , geo:Geometry ; geo:asWKT "POLYGON((113.1016 -38.062 ...))"^^geo:wktLiteral .```|

GDS also implements some content profiles (refer to [W3C Conneg by Profile](https://w3c.github.io/dxwg/connegp/)):

| Content profile name | Returns | Notes |
|--------------|--------------|---------|
|geometryview (default) | Provides the geometry as-is | Useful for using the full resolution geometry |
|centroid | Generates the centroid for the geometry | Useful for when you only need the centroid |
|simplifiedgeom | Applies a function to "simplify" the geometry | Useful for rendering the geometry but don't need the full resolution (smaller payload also) |

The combination of the two sets of interfaces allows users to query for the geometry resource
to suit the needs of the application.


## Usage scenarios

### Linking from a description of a feature

Rather than embed a literal to the geometry in the Geosparql Feature instance,
we can use the GDS to mint a URI for the geometry and bind it via a URI.

Example: ASGS 2016 Meshblock Feature
```
<http://linked.data.gov.au/dataset/asgs2016/meshblock/20663970000> a asgs:MeshBlock,
        geo:Feature ;
    geo:hasGeometry <http://gds.loci.cat/dataset/asgs16_mb/20663970000> ;
.
```

It is up to the client/user to resolve the URI ref to the Geometry via standard HTTP plus conneg (by profile and format). 

### Find the respective feature(s) from the geometry

Given a geometry description, we can follow links back to respective geometry.
An example of the RDF/Turtle format response for the Geometry URI 
`http://gds.loci.cat/geometry/asgs16_mb/20663970000`: 
```
<http://gds.loci.cat/geometry/asgs16_mb/20663970000> a geo:Geometry,
        sf:MultiPolygon ;
    geox:isGeometryOf <http://linked.data.gov.au/dataset/asgs2016/meshblock/20663970000> .
```

We can then traverse back to the Feature via the value for the `geox:isGeometryOf` property.


## References and related work

* https://gnis-ld.org/ 
* Regalia et al., Revisiting the Representation of and Need for Raw Geometries on the Linked Data Web, LDOW, 2017, http://ceur-ws.org/Vol-1809/article-04.pdf




