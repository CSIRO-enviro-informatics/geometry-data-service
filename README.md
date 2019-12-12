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

An alternative to the simple flask run is via docker. To use docker, you'll need to install `docker` and `docker-compose`.

You can then deploy via
```
$ docker-compose up -d
```

If you would like to deploy to a port other than 3000, you can also set the `PORT` parameter in a `.env` file like so:
```
PORT=3111
```

Running `docker-compose up -d` will pick up the .env file settings.
