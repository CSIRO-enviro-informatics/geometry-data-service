"""
This file contains all the HTTP routes for search (usually HTML)
"""
from flask import Blueprint, render_template, request
import _config as config


pages = Blueprint('controller', __name__)


@pages.route('/search')
def search():
    """
    Search endpoint
    """
    return render_template(
        'page_index.html',
        api_endpoint=config.API_ENDPOINT,
        request=request
    )

    instance = None
    for d in dogs:
        if d['name'] == dog_id:
            instance = d
            break
    if instance is None:
        return Response("Not Found", status=404)
    renderer = PetRenderer(request, request.base_url, instance, 'page_dog.html')
    return renderer.render()


