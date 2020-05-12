from flask import Response, render_template
from pyldapi import Renderer, View
from rdflib import Graph, URIRef, RDF, RDFS, XSD, OWL, Namespace, Literal, BNode
from rdflib.namespace import NamespaceManager
from rdflib.serializer import Serializer
import _config as config
import json
from shapely.geometry import shape
from pprint import pprint
import psycopg2
import os
from .mappings import DatasetMappings


GeometryView = View("GeometryView", "A profile of geometry.", ['text/html', 'application/json', 'text/turtle', 'text/plain'],
                 'text/html', namespace="http://example.org/def/geometryview")

CentroidView = View("CentroidView", "A profile of geometry's centroid.", ['text/html', 'application/json', 'text/turtle', 'text/plain'],
                 'text/html', namespace="http://example.org/def/centroidview")

SimplifiedGeomView = View("SimplifiedGeomView", "A profile of the geometry that has been simplified.", ['text/html', 'application/json', 'text/turtle', 'text/plain'],
                 'text/html', namespace="http://example.org/def/simplifiedgeomview")

SchemaOrgView = View("SchemaOrg", "A schema.org profile of the geometry.", ['text/html', 'application/ld+json'],
                 'text/html', namespace="http://example.org/def/schemaorg")


class GeometryRenderer(Renderer):
    DATASET_RESOURCE_BASE_URI_LOOKUP = DatasetMappings.DATASET_RESOURCE_BASE_URI_LOOKUP
    def __init__(self, request, uri, instance, geom_html_template, **kwargs):
        self.views = {
                       'geometryview': GeometryView,
                       'centroid': CentroidView,
                       'simplifiedgeom': SimplifiedGeomView,
                       'schemaorg': SchemaOrgView
                     }
        self.default_view_token = 'geometryview'
        super(GeometryRenderer, self).__init__(
            request, uri, self.views, self.default_view_token, **kwargs)
        self.instance = instance
        self.geom_html_template = geom_html_template
        self.uri = uri
        self.request= request
        self.instance['feature'] = self._find_resource_uris()

    def _render_geometryview(self):
        self.headers['Profile'] = 'http://example.org/def/geometryview'
        if self.format == "application/json":
            return Response(json.dumps(self.instance),
                            mimetype="application/json", status=200)
        if self.format == "text/plain":
            return Response(self._geojson_to_wkt(),
                            mimetype="text/plain", status=200)
        elif self.format == "text/html":
            return Response(render_template(self.geom_html_template, **self.instance, uri=self.uri, request=self.request, view=self.view), mimetype="text/html", status=200)
        elif self.format == "text/turtle":
            return Response(self.export_rdf(self, rdf_mime='text/turtle'),
                            mimetype="text/turtle", status=200)

    def _render_centroidview(self):
        self.headers['Profile'] = 'http://example.org/def/centroidview'
        self._fetch_geom_centroid_from_db()
        if self.format == "application/json":
            return Response(json.dumps(self.instance),
                            mimetype="application/json", status=200)
        if self.format == "text/plain":
            return Response(self._geojson_to_wkt(),
                            mimetype="text/plain", status=200)
        elif self.format == "text/html":
            return Response(render_template(self.geom_html_template, **self.instance, uri=self.uri, request=self.request, view=self.view), mimetype="text/html", status=200)
        elif self.format == "text/turtle":
            return Response(self.export_rdf(self, rdf_mime='text/turtle'),
                            mimetype="text/turtle", status=200)

    def _render_simplifiedgeomview(self):
        self.headers['Profile'] = 'http://example.org/def/simplifiedgeomview'
        self._fetch_simplified_geom_from_db()
        if self.format == "application/json":
            return Response(json.dumps(self.instance),
                            mimetype="application/json", status=200)
        if self.format == "text/plain":
            return Response(self._geojson_to_wkt(),
                            mimetype="text/plain", status=200)
        elif self.format == "text/html":
            return Response(render_template(self.geom_html_template, **self.instance, uri=self.uri, request=self.request, view=self.view), mimetype="text/html", status=200)
        elif self.format == "text/turtle":
            return Response(self.export_rdf(self, rdf_mime='text/turtle'),
                            mimetype="text/turtle", status=200)
    
    def _render_schemaorgview(self):
        self.headers['Profile'] = 'http://example.org/def/schemaorg'
        if self.format == "application/ld+json":
            return Response(self.export_schemaorg_jsonld(),
                            mimetype="application/json", status=200)
        elif self.format == "text/html":
            return Response(render_template(self.geom_html_template, **self.instance, uri=self.uri, request=self.request, view=self.view), mimetype="text/html", status=200)

    def _render_alternates_view_html(self):
        return Response(
            render_template(
                self.alternates_template or 'alternates.html',
                register_name='Geometry Register',
                class_uri='http://www.opengis.net/ont/geosparql#Geometry',
                instance_uri='',
                default_view_token=self.default_view_token,
                views=self.views
            ),
            headers=self.headers
        )


    def export_rdf(self, rdf_mime='text/turtle'):
        (g,nsm) = self.get_graph()
        return g.serialize(format=self._get_rdf_mimetype(rdf_mime), nsm=nsm)
    
    def export_schemaorg_jsonld(self):
        (g,nsm) = self.get_so_graph(include_geom=False)
        #use elfie/selfie context
        context = [
            "https://opengeospatial.github.io/ELFIE/json-ld/elf.jsonld",
            "https://opengeospatial.github.io/ELFIE/json-ld/elf-network.jsonld"
        ]
        fallback_context = {
            "schema": "http://schema.org/",
            "skos": "https://www.w3.org/TR/skos-reference/",
            "gsp": "http://www.opengis.net/ont/geosparql#",
            "description": "schema:description",
            "geo": "schema:geo",
            "hasGeometry": "gsp:hasGeometry",
            "asWKT": "gsp:asWKT",
            "image": {
            "@id": "schema:image",
            "@type": "@id"
            },
            "name": "schema:name",
            "sameAs": "schema:sameAs",
            "related": "skos:related"
        }
        res = None
        from urllib.error import HTTPError
        try:
            res = g.serialize(format='json-ld', context=context, auto_compact=True)
        except HTTPError as he:
            #use fallback context instead
            res = g.serialize(format='json-ld', context=fallback_context, auto_compact=True)
        return res

    def get_graph(self, include_geom=True):
        g = Graph()
        s  = URIRef(self.uri)
        GEO = Namespace("http://www.opengis.net/ont/geosparql#")  
        SF = Namespace("http://www.opengis.net/ont/sf#")  
        GEOX = Namespace("http://linked.data.gov.au/def/geox#")
        nsm = NamespaceManager(g)
        nsm.bind('geo', 'http://www.opengis.net/ont/geosparql#')
        nsm.bind('sf', 'http://www.opengis.net/ont/sf#')
        nsm.bind('geox', 'http://linked.data.gov.au/def/geox#')

        g.add((s, RDF.type, GEO.Geometry))     

        list_of_geometry_types = ("Point", "Polygon", "LineString", "MultiPoint", "MultiLineString", "MultiPolygon")
        if self.instance['type'] in list_of_geometry_types:
            g.add((s, RDF.type, URIRef("http://www.opengis.net/ont/sf#{geomType}".format(geomType=self.instance['type'])) )) 
            resource_uri = self._find_resource_uris()
            if resource_uri is not None:
                g.add((s, GEOX.isGeometryOf, URIRef(resource_uri)))
            if include_geom:
                wkt = self._geojson_to_wkt()
                g.add( (s, GEO.asWKT, Literal(wkt , datatype=GEO.wktLiteral) ))
        return (g, nsm)

    def get_so_graph(self, include_geom=True):
        g = Graph()
        s  = URIRef(self.uri)
        GEO = Namespace("http://www.opengis.net/ont/geosparql#")  
        SF = Namespace("http://www.opengis.net/ont/sf#")  
        GEOX = Namespace("http://linked.data.gov.au/def/geox#")
        SCHEMA = Namespace("http://schema.org/")
        nsm = NamespaceManager(g)
        nsm.bind('geo', 'http://www.opengis.net/ont/geosparql#')
        nsm.bind('sf', 'http://www.opengis.net/ont/sf#')
        nsm.bind('geox', 'http://linked.data.gov.au/def/geox#')

        g.add((s, RDF.type, GEO.Geometry))     

        list_of_geometry_types = ("Point", "Polygon", "LineString", "MultiPoint", "MultiLineString", "MultiPolygon")
        if self.instance['type'] in list_of_geometry_types:
            g.add((s, RDF.type, URIRef("http://www.opengis.net/ont/sf#{geomType}".format(geomType=self.instance['type'])) )) 
            resource_uri = self._find_resource_uris()
            if resource_uri is not None:
                g.add((s, GEOX.isGeometryOf, URIRef(resource_uri)))
                g.add((s, SCHEMA.subjectOf, URIRef(resource_uri)))
            if include_geom:
                wkt = self._geojson_to_wkt()
                g.add( (s, GEO.asWKT, Literal(wkt , datatype=GEO.wktLiteral) ))
        return (g, nsm)
    def _find_resource_uris(self):
        dataset = self.instance["dataset"]
        id = self.instance["id"]
        prefix = GeometryRenderer.DATASET_RESOURCE_BASE_URI_LOOKUP.get(dataset)
        if prefix is None:
            return None
        return "{0}/{1}".format(prefix, id)
        
    def _geojson_to_wkt(self):
        g2 = shape(self.instance)
        return g2.wkt


    def _get_rdf_mimetype(self, rdf_mime):
        return self.RDF_SERIALIZER_MAP[rdf_mime]

    def _fetch_geom_centroid_from_db(self):
      """
         Assumes there is a Postgis database with connection config specified in system environment variables.
         Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
         This function connects to the DB, and queries for the geom as geojson based on input dataset and geom_id parameters.
      """
      geom_id = self.instance['id']
      dataset = self.instance['dataset']
      db_name = os.environ['GSDB_DBNAME']
      db_host = os.environ['GSDB_HOSTNAME']
      db_port = os.environ['GSDB_PORT']
      username = os.environ['GSDB_USER']
      passwd = os.environ['GSDB_PASS']
      conn = psycopg2.connect(dbname=db_name, host=db_host, port=db_port, user=username, password=passwd)
      cur = conn.cursor()
      query = 'select id, dataset, ST_AsGeoJSON( ST_Centroid(ST_Transform(geom,4326)) ) from combined_geoms where id = \'{id}\' and dataset=\'{dataset}\';'.format(id=geom_id, dataset=dataset)
      backup_query = 'select id, dataset, ST_AsGeoJSON( ST_Centroid(geom) ) from combined_geoms where id = \'{id}\' and dataset=\'{dataset}\';'.format(id=geom_id, dataset=dataset)
      try:
         cur.execute(query)
      except Exception as e:
           print(e)
           conn.rollback()
           cur.execute(backup_query)
      (id,dataset,geojson) = cur.fetchone()
      o = json.loads(geojson)
      o['id'] = geom_id
      o['dataset'] = dataset
      self.instance = o
      cur.close()
      conn.close()
      return o

    def _fetch_simplified_geom_from_db(self):
      """
         Assumes there is a Postgis database with connection config specified in system environment variables.
         Also assumes there is a table/view called 'combined_geoms' with structure (id, dataset, geom).
         This function connects to the DB, and queries for the geom as geojson based on input dataset and geom_id parameters.
      """
      geom_id = self.instance['id']
      dataset = self.instance['dataset']
      db_name = os.environ['GSDB_DBNAME']
      db_host = os.environ['GSDB_HOSTNAME']
      db_port = os.environ['GSDB_PORT']
      username = os.environ['GSDB_USER']
      passwd = os.environ['GSDB_PASS']
      conn = psycopg2.connect(dbname=db_name, host=db_host, port=db_port, user=username, password=passwd)
      cur = conn.cursor()
      query = 'select id, dataset, ST_AsGeoJSON( ST_Transform( ST_Simplify(geom, 100, true),4326) ) from combined_geoms where id = \'{id}\' and dataset=\'{dataset}\';'.format(id=geom_id, dataset=dataset)
      backup_query = 'select id, dataset, ST_AsGeoJSON( ST_Simplify(geom, 100) ) from combined_geoms where id = \'{id}\' and dataset=\'{dataset}\';'.format(id=geom_id, dataset=dataset)
      try:
         cur.execute(query)
      except Exception as e:
           print(e)
           conn.rollback()
           cur.execute(backup_query)
      print(query)
      (id,dataset,geojson) = cur.fetchone()
      o = json.loads(geojson)
      o['id'] = geom_id
      o['dataset'] = dataset
      self.instance = o
      cur.close()
      conn.close()
      return o


    # All `Renderer` subclasses _must_ implement render
    def render(self):
        if hasattr(self, 'vf_error'):
            return Response(self.vf_error, status=406, mimetype='text/plain')
        response = super(GeometryRenderer, self).render()
        if not response and self.view == 'geometryview':
            response = self._render_geometryview()
        elif not response and self.view == 'simplifiedgeom':
            response = self._render_simplifiedgeomview()
        elif not response and self.view == 'centroid':
            response = self._render_centroidview()
        elif not response and self.view == 'schemaorg':
            response = self._render_schemaorgview()
        elif self.view == 'alternates':
            response = self._render_alternates_view_html()
        else:
            raise NotImplementedError(self.view)
        return response


if __name__ == '__main__':
    pass
