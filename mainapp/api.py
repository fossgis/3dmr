import math

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse, FileResponse
from django.core.paginator import Paginator, EmptyPage
from .models import LatestModel, Comment
from .utils import get_kv, MODEL_DIR
from django.db.models import Max

RESULTS_PER_API_CALL= 20

# returns a paginated json response
def api_paginate(models, page_id):
    paginator = Paginator(models, RESULTS_PER_API_CALL)

    try:
        model_results = paginator.page(page_id)
    except EmptyPage:
        model_results = []

    results = [model.model_id for model in model_results]

    return JsonResponse(results, safe=False)


# Create your views here.
def get_info(request, model_id):
    model = LatestModel.objects.get(model_id=model_id)

    result = {
        'id': model.model_id,
        'revision': model.revision,
        'title': model.title,
        'lat': model.latitude,
        'lon': model.longitude,
        'license': model.license,
        'desc': model.description,
        'author': model.author.username,
        'date': model.upload_date,
        'rotation': model.rotation,
        'scale': model.scale,
        'translation': [model.translation_x, model.translation_y, model.translation_z],
        'tags': model.tags,

        # Note: the [::1] evaluates the query set to a list
        'categories': model.categories.all().values_list('name', flat=True)[::1],
        'comments': Comment.objects.filter(model_id=model.model_id).values_list('author__username', 'comment', 'datetime')[::1],
    }
    return JsonResponse(result)

def get_model(request, model_id, revision=None):
    if not revision:
        revision = LatestModel.objects.get(model_id=model_id).revision

    response = FileResponse(open('{}/{}/{}.zip'.format(MODEL_DIR, model_id, revision), 'rb'))
    response['Content-Disposition'] = 'attachment; filename={}.zip'.format(revision)
    response['Content-Type'] = 'application/zip'
    return response

def lookup_tag(request, tag, page_id=1):
    key, value = get_kv(tag)
    models = LatestModel.objects.filter(tags__contains={key: value}).order_by('model_id')
    return api_paginate(models, page_id)

def lookup_category(request, category, page_id=1):
    models = LatestModel.objects.filter(categories__name=category)
    return api_paginate(models, page_id)

def lookup_author(request, username, page_id=1):
    models = LatestModel.objects.filter(author__username=username)
    return api_paginate(models, page_id)

def search_range(request, latitude, longitude, distance, page_id=1):
    # convert parameters to floats
    latitude = float(latitude)
    longitude = float(longitude)
    distance = float(distance)

    # bind latitude and longitude from [min, max] to [-pi, pi] for usage in trigonometry
    latitude = math.radians(latitude)
    longitude = math.radians(longitude)

    PLANETARY_RADIUS = 6371e3 # in meters
    angular_radius = distance / PLANETARY_RADIUS

    min_latitude = latitude - angular_radius
    max_latitude = latitude + angular_radius

    MIN_LATITUDE = -math.pi/2
    MAX_LATITUDE = math.pi/2
    MIN_LONGITUDE = -math.pi
    MAX_LONGITUDE = math.pi

    if min_latitude > MIN_LATITUDE and max_latitude < MAX_LATITUDE:
        d_longitude = math.asin(math.sin(angular_radius)/math.cos(latitude))

        min_longitude = longitude - d_longitude
        if min_longitude < MIN_LONGITUDE:
            min_longitude += 2 * math.pi

        max_longitude = longitude + d_longitude
        if max_longitude > MAX_LONGITUDE:
            max_longitude -= 2 * math.pi
    else:
        min_latitude = max(min_latitude, MIN_LATITUDE)
        max_latitude = min(max_latitude, MAX_LATITUDE)
        min_longitude = MIN_LONGITUDE
        max_longitude = MAX_LONGITUDE

    # bind results back for usage in the repository
    min_latitude = math.degrees(min_latitude)
    max_latitude = math.degrees(max_latitude)
    min_longitude = math.degrees(min_longitude)
    max_longitude = math.degrees(max_longitude)

    models = LatestModel.objects.filter(
            latitude__gte=min_latitude,
            latitude__lte=max_latitude,
            longitude__gte=min_longitude,
            longitude__lte=max_longitude)

    return api_paginate(models, page_id)

def search_title(request, title, page_id=1):
    models = LatestModel.objects.filter(title__icontains=title)

    return api_paginate(models, page_id)
