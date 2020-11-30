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
from model.dataset import DatasetRenderer
from model.pet import PetRenderer
from model.search_results import SearchResultsRenderer
from model.mappings import DatasetMappings 
import psycopg2
from psycopg2 import pool
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


def establish_dbpool() :
   dbpool = None
   db_name = os.environ['GSDB_DBNAME']
   db_host = os.environ['GSDB_HOSTNAME']
   db_port = os.environ['GSDB_PORT']
   username = os.environ['GSDB_USER']
   passwd = os.environ['GSDB_PASS']
   max_connections_in_pool = 25
   if 'GSDB_CLIENT_MAX_CONN_POOL' in os.environ:
     max_connections_in_pool = os.environ['GSDB_CLIENT_MAX_CONN_POOL']
   try:
      dbpool = psycopg2.pool.SimpleConnectionPool(1, max_connections_in_pool,
                   user = username,
                   password = passwd,
                   host = db_host,
                   port = db_port,
                   database = db_name
                   )
      if(dbpool):
         print("Connection pool created successfully with {} max conns in pool".format(max_connections_in_pool) )
   except (Exception, psycopg2.DatabaseError) as error :
      print ("Error while connecting to PostgreSQL", error)
      if (dbpool):
         dbpool.closeall
         print("PostgreSQL connection pool is closed")                  
   return dbpool

dbpool = None
dbpool = establish_dbpool() 


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

@classes.route('/search/wkt', methods = ['POST'])
def search_by_wkt():
    crs = 4326
    if 'crs' in request.args:
       crs = request.args.get('crs','4326')
    wkt = request.form.get('wkt')
    dataset = request.form.get('dataset')
    operation = request.form.get('operation')
    if operation is None:
       list_results = find_geometry_by_wkt(wkt, crs=crs, dataset=dataset)
    else:
       list_results = find_geometry_by_wkt(wkt, crs=crs, dataset=dataset, operation=operation)
    if list_results is None:
        return Response("Not Found", status=404)   
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
   global dbpool
   count = None
   try:
      if dbpool is None:
         dbpool = establish_dbpool()
      conn = dbpool.getconn()
      conn.set_session(readonly=True, autocommit=True)
      cur = conn.cursor()
      query = 'select geom_total_count from combined_geom_count;'
      cur.execute(query)
      res = cur.fetchone()
      count = res[0]
      cur.close()
      conn.commit()
   except Exception as e:
      print(e)
      cur.close()
      conn.commit()
   finally:
      dbpool.putconn(conn)
   return count

def fetch_geom_from_db(dataset, geom_id):
   """
   Assumes there is a Postgis database with connection config specified in system environment variables.
   Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
   This function connects to the DB, and queries for the geom as geojson based on input dataset and geom_id parameters.
   """
   global dbpool
   query = 'SELECT id, dataset, ST_AsGeoJSON(ST_Transform(geom,4326)) FROM combined_geoms WHERE id = %s AND dataset=%s;'
   backup_query = 'SELECT id, dataset, ST_AsGeoJSON(geom) FROM combined_geoms WHERE id = %s and dataset=%s;'
   o = None
   try:
      if dbpool is None:
         dbpool = establish_dbpool()
      conn = dbpool.getconn()
      conn.set_session(readonly=True, autocommit=True)
      cur = conn.cursor()
      cur.execute(query, (geom_id, dataset))
      (id,dataset,geojson) = cur.fetchone()
      cur.close()
      conn.commit()
      o = json.loads(geojson)
   except Exception as e:
        print(e)
        conn.rollback()
        cur.execute(backup_query, (str(geom_id), str(dataset)))
        (id,dataset,geojson) = cur.fetchone()
        cur.close()
        conn.commit()
        o = json.loads(geojson)
   finally:
      dbpool.putconn(conn)
   return o


def find_geometry_by_latlng(latlng, dataset=None, crs='4326'):
   """
   Assumes there is a Postgis database with connection config specified in system environment variables.
   Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
   This function connects to the DB, and queries for matching geoms based on input latlng parameters.
   Default CRS is WGS84 (4326)
   """
   global dbpool
   if latlng is None or not("," in latlng):
     return { 'count': -1, 'res': None, 'errcode': 1}
   arrData = latlng.split(',')
   query_list = []
   #query 1: no dataset specified so query all
   query_list.append('SELECT id, dataset FROM combined_geoms WHERE ST_Intersects( ST_Transform(ST_SetSRID(ST_Point(%s, %s), %s),3577) , geom);')
   #query 2: dataset _is_ specified so query by dataset
   query_list.append('SELECT id, dataset FROM combined_geoms WHERE dataset = %s and ST_Intersects( ST_Transform(ST_SetSRID(ST_Point(%s, %s), %s),3577) , geom);')
   fmt_results = []
   r_obj = {}
   try:
      if dbpool is None:
         dbpool = establish_dbpool()
      conn = dbpool.getconn()
      conn.set_session(readonly=True, autocommit=True)
      cur = conn.cursor()
      if dataset is None: 
         cur.execute(query_list[0], (str(arrData[0]), str(arrData[1]), str(crs)))
      else:
         cur.execute(query_list[1], (str(dataset), str(arrData[0]), str(arrData[1]), str(crs)))
      
      results = cur.fetchall()
      cur.close()
      conn.commit()
      if results == None:
         r_obj = { 'count': -1, 'res': []}
      else:
         for r in results:
            r_obj = {}
            r_obj['id'] = r[0]
            r_obj['dataset'] = r[1]
            r_obj['geometry'] = request.host_url + "geometry/{dataset}/{id}".format(dataset=r_obj['dataset'],id=r_obj['id'])
            r_obj['feature'] = DatasetMappings.find_resource_uri(r_obj['dataset'],r_obj['id'])
            fmt_results.append(r_obj)
         r_obj = { 'count': len(fmt_results), 'res': fmt_results }
   except Exception as e:
      print(e)
      conn.rollback()
      cur.close()
      conn.commit()
      r_obj = { 'count': -1, 'res': [], 'errcode': 2}
   finally:
      dbpool.putconn(conn)
   return { 'count': len(fmt_results), 'res': fmt_results }

def find_geometry_by_wkt(wkt, dataset=None, crs='4326', operation='intersects'):
   """
   Assumes there is a Postgis database with connection config specified in system environment variables.
   Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
   This function connects to the DB, and queries for matching geoms based on input wkt.
   Default CRS is WGS84 (4326)
   """
   global dbpool
   if wkt is None:
     return { 'count': -1, 'res': None, 'errcode': 1}
   postgis_op = None
   if operation == 'intersects':
      postgis_op = "ST_Intersects"
   elif operation == 'contains':
      postgis_op = "ST_Contains"
   elif operation == 'overlaps':
      postgis_op = "ST_Overlaps"
   else:  
     return { 'count': -1, 'res': None, 'errcode': 2}
   query_list = []
   #query 1: no dataset specified so query all
   query_list.append('SELECT id, dataset FROM combined_geoms WHERE {} ( ST_Transform(ST_GeomFromText(%s, %s),3577) , geom);'.format(postgis_op))
   #query 2: dataset _is_ specified so query by dataset
   query_list.append('SELECT id, dataset FROM combined_geoms WHERE dataset = %s and ST_Intersects( ST_Transform(ST_GeomFromText(%s, %s),3577) , geom);'.format(postgis_op))
   fmt_results = []
   r_obj = {}
   try:
      if dbpool is None:
         dbpool = establish_dbpool()
      conn = dbpool.getconn()
      conn.set_session(readonly=True, autocommit=True)
      cur = conn.cursor()
      if dataset is None: 
         cur.execute(query_list[0], (str(wkt), str(crs)))
      else:
         cur.execute(query_list[1], (str(dataset), str(wkt), str(crs)))
      results = cur.fetchall()
      cur.close()
      conn.commit()
      if results == None:
         r_obj = { 'count': -1, 'res': []}
      else:
         for r in results:
            r_obj = {}
            r_obj['id'] = r[0]
            r_obj['dataset'] = r[1]
            r_obj['geometry'] = request.host_url + "geometry/{dataset}/{id}".format(dataset=r_obj['dataset'],id=r_obj['id'])
            r_obj['feature'] = DatasetMappings.find_resource_uri(r_obj['dataset'],r_obj['id'])
            fmt_results.append(r_obj)
         r_obj = { 'count': len(fmt_results), 'res': fmt_results }
   except Exception as e:
      print(e)
      conn.rollback()
      cur.close()
      conn.commit()
      r_obj = { 'count': -1, 'res': [], 'errcode': 2}
   finally:
      dbpool.putconn(conn)
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
        items = fetch_geom_items_from_db(page, per_page)
    except Exception as e:
        print(e)
        return Response('The Geometries Register is offline:\n{}'.format(e), mimetype='text/plain', status=500)
    no_of_items = fetch_geom_count_from_db()
    if no_of_items is None:
       no_of_items = 0
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
   global dbpool
   results = []
   try:
      if dbpool is None:
         dbpool = establish_dbpool()
      conn = dbpool.getconn()
      conn.set_session(readonly=True, autocommit=True)
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
      conn.commit()
   except Exception as e:
       print(e)
   finally:
      dbpool.putconn(conn)
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

@classes.route('/dataset/<string:dataset_id>')
def dataset_instance(dataset_id):
    instance = None
    instance = { "id": dataset_id }
    renderer = DatasetRenderer(request, request.base_url, instance, 'page_dataset.html')
    return renderer.render()

def fetch_dataset_items_from_db(page_current, records_per_page):
   """
   Assumes there is a Postgis database with connection config specified in system environment variables.
   Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
   This function connects to the DB, and queries for the datasets.
   """
   global dbpool
   results = []
   try:
      if dbpool is None:
         dbpool = establish_dbpool()
      conn = dbpool.getconn()
      conn.set_session(readonly=True, autocommit=True)
      cur = conn.cursor()
      offset = (page_current - 1) * records_per_page
      s = ""
      s += " SELECT DISTINCT dataset"
      s += " FROM combined_geoms"
      s += " ORDER BY dataset"
      s += " LIMIT " + str(records_per_page)
      s += " OFFSET " + str(offset)
      cur.execute(s)
      record_list = cur.fetchall()
      for record in record_list:
         (dataset) = record
         results.append((dataset[0], dataset[0]))
      cur.close()
      conn.commit()
   except Exception as e:
       print(e)
   finally:
      dbpool.putconn(conn)
   return results

def fetch_dataset_count_from_db():
   """
   """
   global dbpool
   count = -1
   try:
      if dbpool is None:
         dbpool = establish_dbpool()
      conn = dbpool.getconn()
      conn.set_session(readonly=True, autocommit=True)
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
      conn.commit()
   except Exception as e:
       print(e)
   finally:
      dbpool.putconn(conn)
   return count
