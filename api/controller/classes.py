"""
This file contains all the HTTP routes for classes from the IGSN model, such as Samples and the Sample Register
"""
from flask import Blueprint, request, Response
import _config as config
import pyldapi
import requests
from io import BytesIO
from lxml import etree
from model.geometry import GeometryRenderer
from model.pet import PetRenderer


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
        return Response("Not Found", status=404)
    renderer = GeometryRenderer(request, request.base_url, instance, 'page_geometry.html')
    return renderer.render()

