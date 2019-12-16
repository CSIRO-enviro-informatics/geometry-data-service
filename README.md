# Geometry data service

This implements a geometry data service for serving RESTful geometries over the web

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
