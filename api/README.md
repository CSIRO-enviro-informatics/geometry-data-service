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
