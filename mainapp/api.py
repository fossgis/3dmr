import math
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse, FileResponse, Http404
from django.core.paginator import Paginator, EmptyPage
from .models import LatestModel, Comment, Model
from .utils import get_kv, MODEL_DIR, admin
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
    model = get_object_or_404(LatestModel, model_id=model_id)

    if model.is_hidden and not admin(request):
        raise Http404('Model does not exist.')

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
        revision = get_object_or_404(LatestModel, model_id=model_id).revision

    model = get_object_or_404(Model, model_id=model_id, revision=revision)

    if model.is_hidden and not admin(request):
        raise Http404('Model does not exist.')


    response = FileResponse(open('{}/{}/{}.zip'.format(MODEL_DIR, model_id, revision), 'rb'))
    response['Content-Disposition'] = 'attachment; filename={}.zip'.format(revision)
    response['Content-Type'] = 'application/zip'
    return response

def lookup_tag(request, tag, page_id=1):
    key, value = get_kv(tag)
    models = LatestModel.objects.filter(tags__contains={key: value}).order_by('model_id')

    if not admin(request):
        models = models.filter(is_hidden=False)

    return api_paginate(models, page_id)

def lookup_category(request, category, page_id=1):
    models = LatestModel.objects.filter(categories__name=category)

    if not admin(request):
        models = models.filter(is_hidden=False)

    return api_paginate(models, page_id)

def lookup_author(request, username, page_id=1):
    models = LatestModel.objects.filter(author__username=username)

    if not admin(request):
        models = models.filter(is_hidden=False)

    return api_paginate(models, page_id)

def range_filter(models, latitude, longitude, distance):
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

    return models.filter(
            latitude__gte=min_latitude,
            latitude__lte=max_latitude,
            longitude__gte=min_longitude,
            longitude__lte=max_longitude)

def search_range(request, latitude, longitude, distance, page_id=1):
    # convert parameters to floats
    latitude = float(latitude)
    longitude = float(longitude)
    distance = float(distance)

    models = LatestModel.objects.all()

    if not admin(request):
        models = models.filter(is_hidden=False)

    models = range_filter(models, latitude, longitude, distance)

    return api_paginate(models, page_id)

def search_title(request, title, page_id=1):
    models = LatestModel.objects.filter(title__icontains=title)

    if not admin(request):
        models = models.filter(is_hidden=False)

    return api_paginate(models, page_id)

def search_full(request):
    body = request.body.decode('UTF-8')
    data = json.loads(body)

    models = LatestModel.objects.all()

    if not admin(request):
        models = models.filter(is_hidden=False)

    author = data.get('author')
    if author:
        models = models.filter(author__username=author)

    latitude = data.get('lat')
    longitude = data.get('lon')
    distance = data.get('range')
    if latitude and longitude:
        models = range_filter(models, latitude, longitude, distance)

    title = data.get('title')
    if title:
        models = models.filter(title__icontains=title)

    tags = data.get('tags')
    if tags:
        for key, value in tags.items():
            models = models.filter(tags__contains={key:value})

    categories = data.get('categories')
    if categories:
        for category in categories:
            models = models.filter(categories__name=category)

    models = models.order_by('model_id')

    page_id = int(data.get('page', 1))

    return api_paginate(models, page_id)
