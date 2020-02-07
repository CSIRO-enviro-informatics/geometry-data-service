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
from model.search_results import SearchResultsRenderer
from model.mappings import DatasetMappings 
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


@classes.route('/search/latlng/<string:latlng>')
def search_by_latlng(latlng):
    crs = 4326
    if 'crs' in request.args:
       crs = request.args.get('crs','4326')
    list_results = find_geometry_by_latlng(latlng, crs=crs)
    if list_results is None:
        return Response("Not Found", status=404)   
    list_results['latlng'] = latlng
    list_results['crs'] = crs
    renderer = SearchResultsRenderer(request, request.base_url, list_results, 'page_searchresults.html')
    return renderer.render()

@classes.route('/search/latlng/<string:latlng>/dataset/<string:dataset>')
def search_by_latlng_and_dataset(latlng, dataset):
    crs = 4326
    if 'crs' in request.args:
       crs = request.args.get('crs','4326')
    list_results = find_geometry_by_latlng(latlng, crs=crs, dataset=dataset)
    if list_results is None:
        return Response("Not Found", status=404)   
    list_results['latlng'] = latlng
    list_results['crs'] = crs
    list_results['dataset'] = dataset
    renderer = SearchResultsRenderer(request, request.base_url, list_results, 'page_searchresults.html')
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
   query = 'SELECT id, dataset, ST_AsGeoJSON(ST_Transform(geom,4326)) FROM combined_geoms WHERE id = %s AND dataset=%s;'
   backup_query = 'SELECT id, dataset, ST_AsGeoJSON(geom) FROM combined_geoms WHERE id = %s and dataset=%s;'
   try:
      cur.execute(query, (geom_id, dataset))
   except Exception as e:
        print(e)
        conn.rollback()
        cur.execute(backup_query, (str(geom_id), str(dataset)))
   (id,dataset,geojson) = cur.fetchone()
   cur.close()
   conn.close()
   o = json.loads(geojson)
   return o


def find_geometry_by_latlng(latlng, dataset=None, crs='4326'):
   """
   Assumes there is a Postgis database with connection config specified in system environment variables.
   Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
   This function connects to the DB, and queries for matching geoms based on input latlng parameters.
   Default CRS is WGS84 (4326)
   """
   if latlng is None or not("," in latlng):
     return { 'count': -1, 'res': None, 'errcode': 1}
   arrData = latlng.split(',')
   db_name = os.environ['GSDB_DBNAME']
   db_host = os.environ['GSDB_HOSTNAME']
   db_port = os.environ['GSDB_PORT']
   username = os.environ['GSDB_USER']
   passwd = os.environ['GSDB_PASS']
   conn = psycopg2.connect(dbname=db_name, host=db_host, port=db_port, user=username, password=passwd)
   cur = conn.cursor()
   query_list = []
   #query 1: no dataset specified so query all
   query_list.append('SELECT id, dataset FROM combined_geoms WHERE ST_Intersects( ST_Transform(ST_SetSRID(ST_Point(%s, %s), %s),3577) , geom);')
   #query 2: dataset _is_ specified so query by dataset
   query_list.append('SELECT id, dataset FROM combined_geoms WHERE dataset = %s and ST_Intersects( ST_Transform(ST_SetSRID(ST_Point(%s, %s), %s),3577) , geom);')
   if dataset is None: 
      try:
         cur.execute(query_list[0], (str(arrData[0]), str(arrData[1]), str(crs)))
      except Exception as e:
           print(e)
           conn.rollback()
           cur.close()
           conn.close()
           return { 'count': -1, 'res': [], 'errcode': 2}
   else:
      try:
         cur.execute(query_list[1], (str(dataset), str(arrData[0]), str(arrData[1]), str(crs)))
      except Exception as e:
           print(e)
           conn.rollback()
           cur.close()
           conn.close()
           return { 'count': -1, 'res': [], 'errcode': 3, 'x': str(arrData[0]), 'y': str(arrData[1])}
      
   results = cur.fetchall()
   cur.close()
   conn.close()
   if results == None:
     return { 'count': -1, 'res': []}
   #print(results)
   fmt_results = []
   for r in results:
      r_obj = {}
      r_obj['id'] = r[0]
      r_obj['dataset'] = r[1]
      r_obj['geometry'] = request.host_url + "geometry/{dataset}/{id}".format(dataset=r_obj['dataset'],id=r_obj['id'])
      r_obj['feature'] = DatasetMappings.find_resource_uri(r_obj['dataset'],r_obj['id'])
      fmt_results.append(r_obj)
   return { 'count': len(fmt_results), 'res': fmt_results }



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
        items = fetch_items_from_db(page, per_page)
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


def fetch_items_from_db(page_current, records_per_page):
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

   #print(s)
   #print(len(results))
   cur.close()
   conn.close()
   return results
