from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage
from .models import Model

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
def lookup_tag(request, tag, page_id=1):
    key, value = tag.split('=', 2)
    models = Model.objects.filter(tags__contains={key: value}).order_by('model_id')
    return api_paginate(models, page_id)
