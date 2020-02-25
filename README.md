[![](https://images.microbadger.com/badges/version/csiroenvinf/geometry-data-service.svg)](https://hub.docker.com/repository/docker/csiroenvinf/geometry-data-service/)
 [![Docker Pulls](https://img.shields.io/docker/pulls/csiroenvinf/geometry-data-service)](https://hub.docker.com/repository/docker/csiroenvinf/geometry-data-service/)

# Geometry data service

The Geometry Data Service (GDS) provides APIs for serving (spatial) geometries as RESTful separable first-class objects to spatial features over the web. The GDS provides access to multiple views of spatial geometries for the relevant reporting geographies included in Loc-I as Linked Data. Geometry data is provided in different forms (e.g. geometry as-is, centroid, metadata-only) and formats/serialisations (e.g. WKT, GeoJSON, SHP, RDF/GeoSPARQL). The GDS achieves this via Content Negotiation on spatial features stored in the Loc-I Geo-database, which hosts the geometries. This allows spatial features in Loc-I to embed URI-references to the geometry instead of embedding a geometry literal, optimising the RDF graph store for semantic queries rather than geospatial.

Background to the GDS can be found at the [original geometry data service github issue](https://github.com/CSIRO-enviro-informatics/loci.cat/issues/39#issue-535488760).

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


## Deploy Quickstart 
```
$ cd api
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ export FLASK_APP=app.py
$ export FLASK_ENV=development
$ flask run --port=3000 --host=0.0.0.0
```

Some toy examples are included in the repo. Once flask is running, go to http://localhost:3000 and use links provided

## Deploy using docker

An alternative to the simple flask run is via docker. 

To use docker, you'll need to install `docker` and `docker-compose`.

You can then deploy via
```
$ docker-compose up -d
```

If you would like to deploy to a port other than 3000, you can also set the `PORT` parameter in a `.env` file like so:
```
PORT=3111
```

Running `docker-compose up -d` will pick up the .env file settings.

Otherwise, you can use the Docker Hub image at https://hub.docker.com/r/csiroenvinf/geometry-data-service.
```
docker pull csiroenvinf/geometry-data-service
```

Run with environment variables
```
$ docker run  -e GSDB_DBNAME=gis -e GSDB_HOSTNAME=localhost -e GSDB_PORT=5432 -e GSDB_USER=user -e GSDB_PASS=pass -p 3000:3000 --network host -it csiroenvinf/geometry-data-service 
```


### Configure geometry_data_service with a Postgis DB endpoint

You can add variables in a .env file to override defaults in the docker-compose.yml file:
```
GSDB_DBNAME=gis
GSDB_HOSTNAME=db
GSDB_PORT=5432
GSDB_USER=jon
GSDB_PASS=jon
```

## Deploy with a Postgis DB using docker 

In cases, where there isn't an existing Postgis and you would like to populate a Postgis DB with
some geometries, you can use the following to set one up.

The following command will setup a postgis database alongside the geometry API
```
$ docker-compose -f docker-compose.yml -f docker-compose.postgis.yml up -d
```

This currently uses the `kartoza/postgis` docker image (see https://github.com/kartoza/docker-postgis).
You can use `psql` or other tools to populate the geometries into that DB.

The only requirement from the geometry_data_service of the Postgis DB 
is to have a table or view called `combined_geoms` with the structure:
```
 Column  |       Type        | Collation | Nullable | Default 
---------+-------------------+-----------+----------+---------
 id      | character varying |           |          | 
 geom    | geometry          |           |          | 
 dataset | text              |           |          | 
```

Where `id` is the local identifier for the geometry, `dataset` is the label for the dataset it comes from (e.g. asgs2016_sa1),
and `geom` is the actual geometry.


The following command will bring down the containers:
```
$ docker-compose -f docker-compose.yml -f docker-compose.postgis.yml down 
```
