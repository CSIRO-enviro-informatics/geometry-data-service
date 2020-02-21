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

import pprint

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
      , {
        "dataset": "landmark",
        "id": "sydney-opera-house",
        "type": "Point",
        "coordinates": [
          151.2153,
          -33.8568
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


def fetch_geom_count_from_db():
   """
   """
   db_name = os.environ['GSDB_DBNAME']
   db_host = os.environ['GSDB_HOSTNAME']
   db_port = os.environ['GSDB_PORT']
   username = os.environ['GSDB_USER']
   passwd = os.environ['GSDB_PASS']
   conn = psycopg2.connect(dbname=db_name, host=db_host, port=db_port, user=username, password=passwd)
   cur = conn.cursor()
   query = 'select geom_total_count from combined_geom_count;'
   try:
      cur.execute(query)
   except Exception as e:
        print(e)
        return None
   res = cur.fetchone()
   count = res[0]
   cur.close()
   conn.close()
   return count

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
   query = 'select id, dataset, ST_AsGeoJSON(ST_Transform(geom,4326)) from combined_geoms where id = \'{id}\' and dataset=\'{dataset}\';'.format(id=geom_id, dataset=dataset)
   backup_query = 'select id, dataset, ST_AsGeoJSON(geom) from combined_geoms where id = \'{id}\' and dataset=\'{dataset}\';'.format(id=geom_id, dataset=dataset)
   try:
      cur.execute(query)
   except Exception as e:
        print(e)
        conn.rollback()
        cur.execute(backup_query)
   (id,dataset,geojson) = cur.fetchone()
   cur.close()
   conn.close()
   o = json.loads(geojson)
   return o


@classes.route('/geometry/')
def geometry_list():
    """
    The Register of Geometries
    :return: HTTP Response
    """
    # get the total register count from the XML API
    try:
        page = request.values.get('page') if request.values.get('page') is not None else 1
        page = int(page)
        per_page = request.values.get('per_page') if request.values.get('per_page') is not None else 20
        per_page=int(per_page)
        items = fetch_geom_items_from_db(page, per_page)
    except Exception as e:
        print(e)
        return Response('The Geometries Register is offline:\n{}'.format(e), mimetype='text/plain', status=500)
    no_of_items = fetch_geom_count_from_db()
    r = pyldapi.RegisterRenderer(
        request,
        request.url,
        'Geometries Register',
        'A register of Geometries',
        items,
        ["http://www.opengis.net/ont/geosparql#Geometry"],
        no_of_items,
        per_page=per_page
    )
    if hasattr(r, 'vf_error'):
        pprint.pprint(r.vf_error)
        return Response('The Geometries Register view is offline due to HTTP headers not able to be handled:\n{}\n\nThis usually happens on a newer version of the Google Chrome browser.\nPlease try a different browser like Firefox or Chrome v78 or earlier.'.format(r.vf_error), mimetype='text/plain', status=500)
    return r.render()


def fetch_geom_items_from_db(page_current, records_per_page):
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
   offset = (page_current - 1) * records_per_page
   s = ""
   s += " SELECT id, dataset"
   s += " FROM combined_geoms"
   s += " ORDER BY dataset,id"
   s += " LIMIT " + str(records_per_page)
   s += " OFFSET " + str(offset)
   results = []
   cur.execute(s)
   record_list = cur.fetchall()
   for record in record_list:
      (id,dataset) = record
      results.append((dataset+ "/"+str(id), dataset+"/"+str(id)))
   cur.close()
   conn.close()
   return results

@classes.route('/dataset/')
def dataset_list():
    """
    The Register of Datasets
    :return: HTTP Response
    """
    # get the total register count from the XML API
    try:
        page = request.values.get('page') if request.values.get('page') is not None else 1
        page = int(page)
        per_page = request.values.get('per_page') if request.values.get('per_page') is not None else 20
        per_page=int(per_page)
        items = fetch_dataset_items_from_db(page, per_page)
    except Exception as e:
        print(e)
        return Response('The Datasets Register is offline:\n{}'.format(e), mimetype='text/plain', status=500)
    no_of_items = fetch_dataset_count_from_db()
    r = pyldapi.RegisterRenderer(
        request,
        request.url,
        'Datasets Register',
        'A register of Datasets',
        items,
        ["http://www.w3.org/ns/dcat#Dataset"],
        no_of_items,
        per_page=per_page
    )
    if hasattr(r, 'vf_error'):
        pprint.pprint(r.vf_error)
        return Response('The Datasets Register view is offline due to HTTP headers not able to be handled:\n{}\n\nThis usually happens on a newer version of the Google Chrome browser.\nPlease try a different browser like Firefox or Chrome v78 or earlier.'.format(r.vf_error), mimetype='text/plain', status=500)
    return r.render()

def fetch_dataset_items_from_db(page_current, records_per_page):
   """
   Assumes there is a Postgis database with connection config specified in system environment variables.
   Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
   This function connects to the DB, and queries for the datasets.
   """
   db_name = os.environ['GSDB_DBNAME']
   db_host = os.environ['GSDB_HOSTNAME']
   db_port = os.environ['GSDB_PORT']
   username = os.environ['GSDB_USER']
   passwd = os.environ['GSDB_PASS']
   conn = psycopg2.connect(dbname=db_name, host=db_host, port=db_port, user=username, password=passwd)
   cur = conn.cursor()
   offset = (page_current - 1) * records_per_page
   s = ""
   s += " SELECT DISTINCT dataset"
   s += " FROM combined_geoms"
   s += " ORDER BY dataset"
   s += " LIMIT " + str(records_per_page)
   s += " OFFSET " + str(offset)
   results = []
   cur.execute(s)
   record_list = cur.fetchall()
   for record in record_list:
      (dataset) = record
      results.append((dataset[0], dataset[0]))
   cur.close()
   conn.close()
   return results

def fetch_dataset_count_from_db():
   """
   """
   db_name = os.environ['GSDB_DBNAME']
   db_host = os.environ['GSDB_HOSTNAME']
   db_port = os.environ['GSDB_PORT']
   username = os.environ['GSDB_USER']
   passwd = os.environ['GSDB_PASS']
   conn = psycopg2.connect(dbname=db_name, host=db_host, port=db_port, user=username, password=passwd)
   cur = conn.cursor()
   query = 'SELECT count(DISTINCT dataset) FROM combined_geoms;'
   try:
      cur.execute(query)
   except Exception as e:
        print(e)
        return None
   res = cur.fetchone()
   count = res[0]
   cur.close()
   conn.close()
   return count
