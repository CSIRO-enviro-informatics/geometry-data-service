"""
This file contains all the HTTP routes for classes used in this service
"""
from flask import Blueprint, request, Response
import _config as config
import pyldapi
import requests
from io import BytesIO
from lxml import etree
from model.geometry import GeometryRenderer
from model.pet import PetRenderer
import psycopg2
import json
import os


classes = Blueprint('classes', __name__)


dogs = [
    {
        "name": "Rex",
        "breed": "Dachshund",
        "age": 7,
        "color": "brown",
    }, {
        "name": "Micky",
        "breed": "Alsatian",
        "age": 3,
        "color": "black",
    }
]


@classes.route('/pet/dog/<string:dog_id>')
def dog_instance(dog_id):
    instance = None
    for d in dogs:
        if d['name'] == dog_id:
            instance = d
            break
    if instance is None:
        return Response("Not Found", status=404)
    renderer = PetRenderer(request, request.base_url, instance, 'page_dog.html')
    return renderer.render()


geom_list = [
    {
        "dataset": "victoria-places",
        "id": "queens-park",
        "type": "Point",
        "coordinates": [
          144.9241733551025,
          -37.76223344864045
        ]
      }
      , {
        "dataset": "victoria-places",
        "id": "moonee-valley-racecourse",
        "type": "Point",
        "coordinates": [
          144.93318557739258,
          -37.7661010374548
        ]
      }
]

@classes.route('/geometry/<string:dataset>/<string:geom_id>')
def geom_instance(dataset, geom_id):
    instance = None
    for g in geom_list:
        if g['dataset'] == dataset and g['id'] == geom_id:
            instance = g
            break
    if instance is None:
        geojson = fetch_geom_from_db(dataset,geom_id)
        if geojson is None:
           return Response("Not Found", status=404)
   
        geojson['id'] = geom_id
        geojson['dataset'] = dataset
        instance = geojson
    renderer = GeometryRenderer(request, request.base_url, instance, 'page_geometry.html')
    return renderer.render()


def fetch_geom_from_db(dataset, geom_id):
   """
   Assumes there is a Postgis database with connection config specified in system environment variables.
   Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
   This function connects to the DB, and queries for the geom as geojson based on input dataset and geom_id parameters.
   """
   db_name = os.environ['GSDB_DBNAME']
   db_host = os.environ['GSDB_HOSTNAME']
   db_port = os.environ['GSDB_PORT']
   username = os.environ['GSDB_USER']
   passwd = os.environ['GSDB_PASS']
   conn = psycopg2.connect(dbname=db_name, host=db_host, port=db_port, user=username, password=passwd)
   cur = conn.cursor()

   query = 'select id, dataset, ST_AsGeoJSON(geom) from combined_geoms where id = \'{id}\' and dataset=\'{dataset}\';'.format(id=geom_id, dataset=dataset)
   cur.execute(query)
   (id,dataset,geojson) = cur.fetchone()

   o = json.loads(geojson)

   return o
