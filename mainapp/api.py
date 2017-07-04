from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage
from .models import LatestModel
from django.db.models import Max

RESULTS_PER_API_CALL= 20

# returns a paginated json response
def api_paginate(models, page_id):
    paginator = Paginator(models, RESULTS_PER_API_CALL)

    try:
        model_results = paginator.page(page_id)
    except EmptyPage:
        model_results = []

    results = [model.id for model in model_results]

    return JsonResponse(results, safe=False)


# Create your views here.
def get_info(request, model_id):
    model = LatestModel.objects.get(model_id=model_id)

    result = {
        'id': model.model_id,
        'title': model.title,
        'lat': model.latitude,
        'lon': model.longitude,
        'desc': model.description,
        'tags': model.tags,
        'author': model.author.username,
        'date': model.upload_date,

        # Note: the [::1] evaluates the query set to a list
        'categories': model.categories.all().values_list('name', flat=True)[::1],
        'comments': [],
    }
    return JsonResponse(result)

def lookup_tag(request, tag, page_id=1):
    key, value = tag.split('=', 2)
    models = LatestModel.objects.filter(tags__contains={key: value}).order_by('model_id')
    return api_paginate(models, page_id)

def lookup_category(request, category, page_id=1):
    models = LatestModel.objects.filter(categories__name=category)
    return api_paginate(models, page_id)

def lookup_author(request, username, page_id=1):
    models = LatestModel.objects.filter(author__username=username)
    return api_paginate(models, page_id)
