from flask import Response, render_template
from pyldapi import Renderer, View
from datetime import datetime
from io import StringIO
import requests
from rdflib import Graph, URIRef, RDF, RDFS, XSD, OWL, Namespace, Literal, BNode
import _config as config
import json


MyPetView = View("PetView", "A profile of my pet.", ['text/html', 'application/json', 'text/turtle'],
                 'text/html', namespace="http://example.org/def/mypetview")

class PetRenderer(Renderer):
    def __init__(self, request, uri, instance, pet_html_template, **kwargs):
        self.views = {'mypetview': MyPetView}
        self.default_view_token = 'mypetview'
        super(PetRenderer, self).__init__(
            request, uri, self.views, self.default_view_token, **kwargs)
        self.instance = instance
        self.pet_html_template = pet_html_template

    def _render_mypetview(self):
        self.headers['Profile'] = 'http://example.org/def/mypetview'
        if self.format == "application/json":
            return Response(json.dumps(self.instance),
                            mimetype="application/json", status=200)
        elif self.format == "text/html":
            return Response(render_template(self.pet_html_template, **self.instance))
        elif self.format == "text/turtle":
            return Response(self.export_rdf(self, rdf_mime='text/turtle'),
                            mimetype="application/json", status=200)

    def export_rdf(self, model_view='petview', rdf_mime='text/turtle'):
        g = Graph()
        s  = URIRef(self.uri)
        n = Namespace("http://example.org/pets#")        

        g.add((s, RDF.type, URIRef('http://dbpedia.org/resource/Dog')))
        g.add((s, n.breed, Literal(self.instance['breed'])))
        g.add((s, n.age, Literal(self.instance['age'], datatype=XSD.integer)))
        g.add((s, n.color, Literal(self.instance['color'])))
        return g.serialize(format=self._get_rdf_mimetype(rdf_mime))


    def _get_rdf_mimetype(self, rdf_mime):
        return self.RDF_SERIALIZER_MAP[rdf_mime]

    # All `Renderer` subclasses _must_ implement render
    def render(self):
        response = super(PetRenderer, self).render()
        if not response and self.view == 'mypetview':
            response = self._render_mypetview()
        else:
            raise NotImplementedError(self.view)
        return response


if __name__ == '__main__':
    pass
