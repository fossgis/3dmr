import math
import json

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, FileResponse, Http404, HttpResponseBadRequest
from django.core.paginator import Paginator, EmptyPage
from .models import Comment, Model
from .utils import get_kv, admin
from django.views.decorators.csrf import csrf_exempt
from social_django.models import UserSocialAuth

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

# decorator for returning 'Access-Control-Allow-Origin' header
def any_origin(f):
    def request(*args, **kwargs):
        response = f(*args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    return request

# Create your views here.
@any_origin
def get_info(request, model_id):
    model = get_object_or_404(Model, latest=True, model_id=model_id)

    if model.is_hidden and not admin(request):
        raise Http404('Model does not exist.')

    if model.location:
        latitude = model.location.latitude
        longitude = model.location.longitude
    else:
        latitude = None
        longitude = None

    comments = Comment.objects.filter(model__model_id=model.model_id)
    if not admin(request):
        comments = comments.filter(is_hidden=False)

    result = {
        'id': model.model_id,
        'revision': model.revision,
        'title': model.title,
        'lat': latitude,
        'lon': longitude,
        'license': model.license,
        'desc': model.description,
        'author': model.author.profile.uid,
        'date': model.upload_date,
        'rotation': model.rotation,
        'scale': model.scale,
        'translation': [model.translation_x, model.translation_y, model.translation_z],
        'tags': model.tags,

        # Note: the [::1] evaluates the query set to a list
        'categories': model.categories.all().values_list('name', flat=True)[::1],
        'comments': [
            (comment.author.profile.uid, comment.comment, comment.datetime)
            for comment in comments
        ],
    }

    return JsonResponse(result)

@any_origin
def get_model(request, model_id, revision=None):
    if not revision:
        model = get_object_or_404(Model, model_id=model_id, latest=True)
        revision = model.revision
    else:
        model = get_object_or_404(Model, model_id=model_id, revision=revision)

    if model.is_hidden and not admin(request):
        raise Http404('Model does not exist.')


    response = FileResponse(open('{}/{}/{}.glb'.format(settings.MODEL_DIR, model_id, revision), 'rb'))
    response['Content-Disposition'] = 'attachment; filename={}_{}.glb'.format(model_id, revision)
    response['Content-Type'] = 'model/gltf-binary'
    response['Cache-Control'] = 'public, max-age=86400'
    return response

@any_origin
def lookup_tag(request, tag, page_id=1):
    key, value = get_kv(tag)
    models = Model.objects.filter(latest=True, tags__contains={key: value}).order_by('model_id')

    if not admin(request):
        models = models.filter(is_hidden=False)

    return api_paginate(models, page_id)

@any_origin
def lookup_category(request, category, page_id=1):
    models = Model.objects.filter(latest=True, categories__name=category)

    if not admin(request):
        models = models.filter(is_hidden=False)

    return api_paginate(models, page_id)

@any_origin
def lookup_author(request, uid, page_id=1):
    user = get_object_or_404(UserSocialAuth, uid=uid).user
    models = user.model_set.filter(latest=True)

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
            location__latitude__gte=min_latitude,
            location__latitude__lte=max_latitude,
            location__longitude__gte=min_longitude,
            location__longitude__lte=max_longitude)

@any_origin
def search_range(request, latitude, longitude, distance, page_id=1):
    # convert parameters to floats
    latitude = float(latitude)
    longitude = float(longitude)
    distance = float(distance)

    models = Model.objects.filter(latest=True)

    if not admin(request):
        models = models.filter(is_hidden=False)

    models = range_filter(models, latitude, longitude, distance)

    return api_paginate(models, page_id)

@any_origin
def search_title(request, title, page_id=1):
    models = Model.objects.filter(latest=True, title__icontains=title)

    if not admin(request):
        models = models.filter(is_hidden=False)

    return api_paginate(models, page_id)

@csrf_exempt # there's no need for this, since no data is modified
@any_origin
def search_full(request):
    body = request.body.decode('UTF-8')
    data = json.loads(body)

    models = Model.objects.filter(latest=True)

    if not admin(request):
        models = models.filter(is_hidden=False)

    if data.get('author'): #uid
        try :
            author = UserSocialAuth.objects.get(uid=data.get('author')).user
            models = models.filter(author=author)
        except UserSocialAuth.DoesNotExist:
            pass

    latitude = data.get('lat')
    longitude = data.get('lon')
    distance = data.get('range')
    if latitude is not None and \
       longitude is not None and \
       distance is not None:
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

    fmt = data.get('format')

    if not fmt:
        return api_paginate(models, page_id)

    paginator = Paginator(models, RESULTS_PER_API_CALL)

    try:
        model_results = paginator.page(page_id)
    except EmptyPage:
        model_results = []

    def result(model):
        output = []

        for string in fmt:
            if string == 'id':
                output.append(model.model_id)
            elif string == 'latitude':
                try:
                    output.append(model.location.latitude)
                except:
                    output.append(None)
            elif string == 'longitude':
                try:
                    output.append(model.location.longitude)
                except:
                    output.append(None)
            elif string == 'title':
                output.append(model.title)
            else:
                raise Exception()

        return output

    try:
        results = [result(model) for model in model_results]
    except:
        return HttpResponseBadRequest('Invalid format specifier')

    return JsonResponse(results, safe=False)
