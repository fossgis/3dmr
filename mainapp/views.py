from django.shortcuts import render, get_object_or_404, redirect
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .models import Model, LatestModel, Comment

from .utils import get_kv

import mistune

# Create your views here.
def index(request):
    models = Model.objects.order_by('-pk')[:6]
    context = {
        'models': models,
    }

    return render(request, 'mainapp/index.html', context)

def logout_user(request):
    logout(request)
    return redirect(index)

def docs(request):
    return render(request, 'mainapp/docs.html')

def downloads(request):
    return render(request, 'mainapp/downloads.html')

def model(request, model_id, revision=None):
    if revision:
        model = get_object_or_404(Model, model_id=model_id, revision=revision)
    else:
        model = get_object_or_404(LatestModel, model_id=model_id)

    comments = Comment.objects.filter(model__model_id=model_id).order_by('-datetime')

    context = {
        'model': model,
        'comments': comments,
    }

    return render(request, 'mainapp/model.html', context)

def search(request):
    query = request.GET.get('query', None)
    tag = request.GET.get('tag', None)
    category = request.GET.get('category', None)

    context = {
        'query': query,
        'tag': tag,
        'category': category
    }

    return render(request, 'mainapp/search.html', context)

def upload(request):
    return render(request, 'mainapp/upload.html')

def user(request, username):
    if username == '':
        if request.user:
            username = request.user.username # show our own userpage
        else:
            pass # redirect to index, no user to load

    user = get_object_or_404(User, username=username)
    oauth_user = get_object_or_404(UserSocialAuth, user=user)

    models = user.model_set.order_by('-pk')

    context = {'owner': {
        'username': user.username,
        'avatar': oauth_user.extra_data['avatar'],
        'profile': user.profile,
        'models': models,
    }}

    return render(request, 'mainapp/user.html', context)

def map(request):
    return render(request, 'mainapp/map.html')

def editprofile(request):
    description = request.POST.get('desc')

    request.user.profile.description = description
    request.user.profile.rendered_description = mistune.markdown(description)
    request.user.save()

    return redirect(user, username='')

def addcomment(request):
    comment = request.POST.get('comment')
    model_id = int(request.POST.get('model_id'))
    revision = int(request.POST.get('revision'))

    author = request.user
    rendered_comment = mistune.markdown(comment)
    model_obj = get_object_or_404(Model, model_id=model_id, revision=revision)

    obj = Comment(
        author=author,
        comment=comment,
        rendered_comment=rendered_comment,
        model=model_obj,
    )

    obj.save()

    return redirect(model, model_id, revision)
