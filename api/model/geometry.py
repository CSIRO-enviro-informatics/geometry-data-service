from flask import Response, render_template
from pyldapi import Renderer, View
from rdflib import Graph, URIRef, RDF, RDFS, XSD, OWL, Namespace, Literal, BNode
from rdflib.namespace import NamespaceManager
import _config as config
import json
from shapely.geometry import shape

GeometryView = View("GeometryView", "A profile of geometry.", ['text/html', 'application/json', 'text/turtle', 'text/plain'],
                 'text/html', namespace="http://example.org/def/geometryview")

class GeometryRenderer(Renderer):
    def __init__(self, request, uri, instance, geom_html_template, **kwargs):
        self.views = {'geometryview': GeometryView}
        self.default_view_token = 'geometryview'
        super(GeometryRenderer, self).__init__(
            request, uri, self.views, self.default_view_token, **kwargs)
        self.instance = instance
        self.geom_html_template = geom_html_template
        self.uri = uri
        self.request= request

    def _render_geometryview(self):
        self.headers['Profile'] = 'http://example.org/def/geometryview'
        if self.format == "application/json":
            return Response(json.dumps(self.instance),
                            mimetype="application/json", status=200)
        if self.format == "text/plain":
            return Response(self._geojson_to_wkt(),
                            mimetype="text/plain", status=200)
        elif self.format == "text/html":
            return Response(render_template(self.geom_html_template, **self.instance, uri=self.uri, request=self.request))
        elif self.format == "text/turtle":
            return Response(self.export_rdf(self, rdf_mime='text/turtle'),
                            mimetype="application/json", status=200)

    def export_rdf(self, model_view='geometryview', rdf_mime='text/turtle'):
        g = Graph()
        s  = URIRef(self.uri)
        GEO = Namespace("http://www.opengis.net/ont/geosparql#")  
        SF = Namespace("http://www.opengis.net/ont/sf#")  
        nsm = NamespaceManager(g)
        nsm.bind('geo', 'http://www.opengis.net/ont/geosparql#')
        nsm.bind('sf', 'http://www.opengis.net/ont/sf#')

        g.add((s, RDF.type, GEO.Geometry))     

        list_of_geometry_types = ("Point", "Polygon", "LineString", "MultiPoint", "MultiLineString", "MultiPolygon")
        if self.instance['type'] in list_of_geometry_types:
            g.add((s, RDF.type, URIRef("http://www.opengis.net/ont/sf#{geomType}".format(geomType=self.instance['type'])) )) 
            wkt = self._geojson_to_wkt()
            g.add( (s, GEO.asWKT, Literal(wkt , datatype=GEO.wktLiteral) ))

        return g.serialize(format=self._get_rdf_mimetype(rdf_mime), nsm=nsm)


    def _geojson_to_wkt(self):
        g2 = shape(self.instance)
        return g2.wkt


    def _get_rdf_mimetype(self, rdf_mime):
        return self.RDF_SERIALIZER_MAP[rdf_mime]

    # All `Renderer` subclasses _must_ implement render
    def render(self):
        response = super(GeometryRenderer, self).render()
        if not response and self.view == 'geometryview':
            response = self._render_geometryview()
        else:
            raise NotImplementedError(self.view)
        return response


if __name__ == '__main__':
    pass
