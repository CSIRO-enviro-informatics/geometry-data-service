from flask import Response, render_template
from pyldapi import Renderer, View
from datetime import datetime
from io import StringIO
import requests
from rdflib import Graph, URIRef, RDF, RDFS, XSD, OWL, Namespace, Literal, BNode
import _config as config
import json
from .mappings import DatasetMappings


SearchResultsView = View("SearchResultsView", "A profile of search results view.", ['text/html', 'application/json'],
                 'text/html', namespace="http://example.org/def/searchresultsview")

class SearchResultsRenderer(Renderer):
    def __init__(self, request, uri, instance, search_html_template, **kwargs):
        self.views = {'searchresultsview': SearchResultsView}
        self.default_view_token = 'searchresultsview'
        super(SearchResultsRenderer, self).__init__(
            request, uri, self.views, self.default_view_token, **kwargs)
        self.instance = instance
        self.search_html_template = search_html_template

    def _render_searchresultsview(self):
        self.headers['Profile'] = 'http://example.org/def/searchresultsview'
        if self.format == "application/json":
            return Response(json.dumps(self.instance),
                            mimetype="application/json", status=200)
        elif self.format == "text/html":
            return Response( render_template(self.search_html_template, **self.instance, uri=self.uri, request=self.request, view=self.view), mimetype="text/html", status=200)

    # All `Renderer` subclasses _must_ implement render
    def render(self):
        response = super(SearchResultsRenderer, self).render()
        if not response and self.view == 'searchresultsview':
            response = self._render_searchresultsview()
        else:
            raise NotImplementedError(self.view)
        return response


if __name__ == '__main__':
    pass
