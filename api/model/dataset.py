from flask import Response, render_template
from pyldapi import Renderer, View
from rdflib import Graph, URIRef, RDF, RDFS, XSD, OWL, Namespace, Literal, BNode
from rdflib.namespace import NamespaceManager
import _config as config
import json
from pprint import pprint
import os



DefaultView = View("default", "Default dataset view", ['text/html', 'application/json', 'text/turtle', 'text/plain'],
                 'text/html', namespace="http://example.org/def/datasetview")


class DatasetRenderer(Renderer):
    def __init__(self, request, uri, instance, dataset_html_template, **kwargs):
        self.views = {
                       'default': DefaultView
                     }
        self.default_view_token = 'default'
        super(DatasetRenderer, self).__init__(
            request, uri, self.views, self.default_view_token, **kwargs)
        self.instance = instance
        self.dataset_html_template = dataset_html_template
        self.uri = uri
        self.request= request

    def _render_dataset_default_view(self):
        self.headers['Profile'] = 'http://example.org/def/datasetview'
        if self.format == "application/json":
            return Response(json.dumps(self.instance),
                            mimetype="application/json", status=200)
        if self.format == "text/plain":
            return Response(json.dumps(self.instance),
                            mimetype="text/plain", status=200)
        elif self.format == "text/html":
            return Response(render_template(self.dataset_html_template, **self.instance, uri=self.uri, request=self.request, view=self.view), mimetype="text/html", status=200)
        elif self.format == "text/turtle":
            return Response(self.export_rdf(self, rdf_mime='text/turtle'),
                            mimetype="text/turtle", status=200)


    def _render_alternates_view_html(self):
        return Response(
            render_template(
                self.alternates_template or 'alternates.html',
                register_name='Dataset Register',
                class_uri='http://www.opengis.net/ont/geosparql#Dataset',
                instance_uri='',
                default_view_token=self.default_view_token,
                views=self.views
            ),
            headers=self.headers
        )


    def export_rdf(self, model_view='default', rdf_mime='text/turtle'):
        g = Graph()
        s  = URIRef(self.uri)
        DCAT = Namespace("http://www.w3.org/ns/dcat#")
        nsm = NamespaceManager(g)
        nsm.bind('dcat', 'http://www.w3.org/ns/dcat#')
        g.add((s, RDF.type, DCAT.Dataset))     
        return g.serialize(format=self._get_rdf_mimetype(rdf_mime), nsm=nsm)

    # All `Renderer` subclasses _must_ implement render
    def render(self):
        if hasattr(self, 'vf_error'):
            return Response(self.vf_error, status=406, mimetype='text/plain')
        response = super(DatasetRenderer, self).render()
        if not response and self.view == 'default':
            response = self._render_dataset_default_view()
        elif self.view == 'alternates':
            response = self._render_alternates_view_html()
        else:
            raise NotImplementedError(self.view)
        return response


if __name__ == '__main__':
    pass
