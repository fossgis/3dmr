import os
import logging

from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .models import Model, LatestModel, Comment, Category, Change, Ban
from .forms import UploadForm
from django.contrib import messages
from django.db import transaction

from .utils import get_kv, update_last_page, get_last_page, MODEL_DIR, CHANGES, admin

import mistune

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    update_last_page(request)

    MODELS_IN_INDEX_PAGE = 6
    models = Model.objects.order_by('-pk')

    if not admin(request):
        models = models.filter(is_hidden=False)

    context = {
            'models': models[:MODELS_IN_INDEX_PAGE],
    }

    return render(request, 'mainapp/index.html', context)

def login(request):
    last_page = get_last_page(request)
    return redirect(last_page)

def logout_user(request):
    logout(request)
    return redirect(index)

def docs(request):
    update_last_page(request)

    return render(request, 'mainapp/docs.html')

def downloads(request):
    update_last_page(request)

    return render(request, 'mainapp/downloads.html')

def model(request, model_id, revision=None):
    update_last_page(request)

    if revision:
        model = get_object_or_404(Model, model_id=model_id, revision=revision)
    else:
        model = get_object_or_404(LatestModel, model_id=model_id)

    if model.is_hidden and not admin(request):
        raise Http404('Model does not exist.')

    comments = Comment.objects.filter(model__model_id=model_id).order_by('-datetime')

    context = {
        'model': model,
        'comments': comments,
    }

    return render(request, 'mainapp/model.html', context)

def search(request):
    update_last_page(request)

    RESULTS_PER_PAGE = 1

    query = request.GET.get('query', None)
    tag = request.GET.get('tag', None)
    category = request.GET.get('category', None)
    try:
        page_id = int(request.GET.get('page', 1))
    except ValueError:
        page_id = 1

    url_params = '?'

    if query:
        url_params += 'query=' + query
    if tag:
        url_params += 'tag=' + tag
    if category:
        url_params += 'category=' + category

    models = Model.objects

    if tag:
        try:
            key, value = get_kv(tag)
        except ValueError:
            return redirect(index)
        filtered_models = models.filter(tags__contains={key: value})
    elif category:
        filtered_models = models.filter(categories__name=category)
    elif query:
        filtered_models = \
            models.filter(title__icontains=query) | \
            models.filter(description__icontains=query)

    if not admin(request):
        filtered_models = filtered_models.filter(is_hidden=False)

    try:
        ordered_models = filtered_models.order_by('-pk')
    except UnboundLocalError:
        # filtered_models isn't set, redirect to homepage
        return redirect(index)


    paginator = Paginator(ordered_models, RESULTS_PER_PAGE)
    try:
        results = paginator.page(page_id)
    except EmptyPage:
        results = []

    context = {
        'query': query,
        'tag': tag,
        'category': category,
        'models': results,
        'paginator': paginator,
        'page_id': page_id,
        'url_params': url_params
    }

    return render(request, 'mainapp/search.html', context)

def upload(request):
    update_last_page(request)

    if request.user.profile.is_banned:
        messages.error(request, 'You are banned. Uploading models is not permitted.')
        return redirect(index)

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)

        if not request.user.is_authenticated():
            # Show error in form, but don't redirect anywhere
            messages.error(request, 'You must be logged in to use this feature.')

            # Store form data in session, to use after login
            request.session['post_data'] = request.POST
        elif form.is_valid():
            title = form.cleaned_data['title']
            tags = form.cleaned_data['tags']
            categories = form.cleaned_data['categories']
            description = form.cleaned_data['description']
            latitude = form.cleaned_data['latitude']
            longitude = form.cleaned_data['longitude']
            license = form.cleaned_data['license']
            model_file = request.FILES['model_file']

            try:
                with transaction.atomic():
                    # get the model_id for this model.
                    # we can only do it this way because we're in a transaction.
                    try:
                        next_model_id = LatestModel.objects.latest('model_id').model_id + 1
                    except LatestModel.DoesNotExist:
                        next_model_id = 1 # no models in db

                    rendered_description = mistune.markdown(description)

                    m = Model(
                        model_id=next_model_id,
                        revision=1,
                        title=title,
                        description=description,
                        rendered_description=rendered_description,
                        tags=tags,
                        longitude=longitude,
                        latitude=latitude,
                        license=license,
                        author=request.user,
                    )

                    m.save()

                    for category_name in categories:
                        try:
                            category = Category.objects.get(name=category_name)
                        except:
                            category = Category(name=category_name)

                        category.save()
                        m.categories.add(category)

                    m.save()

                    change = Change(
                        author=request.user,
                        model=m,
                        typeof=0, # TODO: find better way to express this (Enum?)
                    )

                    change.save()

                    filepath = MODEL_DIR + f'/{m.model_id}/{m.revision}.zip'
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'wb+') as destination:
                        for chunk in model_file.chunks():
                            destination.write(chunk)
            except:
                # We reach here when any of the following happens:
                # 1) Database constraint is violated
                # 2) File is not saved correctly to the specified directory
                # 3) Unknown

                # We should have verified everything to do with 1) earlier,
                # and notified the user if there was any error. Thus, it's
                # unlikely to be 1). 

                # Thus, we can assume that 2) and 3) are server errors, and that
                # the user can do nothing about them. Thus, report this.
                logger.exception('Fatal server error when uploading model.')
                messages.error(request, 'Fatal server error. Try again later.')

                request.session['post_data'] = request.POST
                return redirect(upload)

            return redirect(model, model_id=m.model_id, revision=m.revision)
    else:
        if not request.user.is_authenticated():
            return redirect(index)

        post_data = request.session.get('post_data', None)
        if post_data: # if there's post_data in our session
            form = UploadForm(post_data)

            # clear previous errors in model_file
            form.errors['model_file'] = form.error_class()
            # add a single error to this field
            form.add_error('model_file', 'You must reupload your file.')

            del request.session['post_data']
        else: # otherwise
            form = UploadForm()

    return render(request, 'mainapp/upload.html', {'form': form})

def user(request, username):
    update_last_page(request)

    RESULTS_PER_PAGE = 3

    if username == '':
        if request.user:
            username = request.user.username # show our own userpage
        else:
            pass # redirect to index, no user to load

    user = get_object_or_404(User, username=username)
    oauth_user = get_object_or_404(UserSocialAuth, user=user)

    models = user.model_set.order_by('-pk')

    if not admin(request):
        models = models.filter(is_hidden=False)

    changes = user.change_set.order_by('-pk')

    try:
        page_id = int(request.GET.get('page', 1))
    except ValueError:
        page_id = 1

    paginator = Paginator(models, RESULTS_PER_PAGE)
    try:
        results = paginator.page(page_id)
    except EmptyPage:
        results = []

    context = {
        'owner': {
            'username': user.username,
            'avatar': oauth_user.extra_data['avatar'],
            'profile': user.profile,
            'models': results,
            'changes': changes,
            'ban': user.ban_set.all().first()
        },
        'paginator': paginator,
        'page_id': page_id,
        'changes': CHANGES,
    }

    return render(request, 'mainapp/user.html', context)

def modelmap(request):
    update_last_page(request)

    return render(request, 'mainapp/map.html')

def editprofile(request):
    if not request.user.is_authenticated():
        return redirect(index)

    if request.user.profile.is_banned:
        messages.error(request, 'You are banned. Editing your profile is not permitted.')
        return redirect(index)

    description = request.POST.get('desc')

    request.user.profile.description = description
    request.user.profile.rendered_description = mistune.markdown(description)
    request.user.save()

    return redirect(user, username='')

def addcomment(request):
    if not request.user.is_authenticated():
        return redirect(index)

    ajax = request.POST.get('ajax')

    if request.user.profile.is_banned:
        if ajax == 'false':
            messages.error(request, 'You are banned. Commenting is not permitted.')
            return redirect(index)
        else:
            response = {
                'success': 'no',
                'error': 'You are banned. Commenting is not permitted.'
            }
            return JsonResponse(response)

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

    if ajax == 'false':
        return redirect(model, model_id=model_id, revision=revision)

    response = {
        'comment': rendered_comment,
        'author': author.username,
        'datetime': obj.datetime,
        'success': 'yes'
    }

    return JsonResponse(response)

def ban(request):
    if not admin(request):
        return redirect(index)

    username = request.POST.get('username')
    reason = request.POST.get('reason')

    if not username:
        return redirect(index)

    banned_user = User.objects.get(username=username)
    
    action = request.POST.get('type')

    if action == 'ban':
        if not reason or len(reason) == 0:
            messages.error(request, 'No reason for ban was specified.')
            return redirect(user, username=username)
        
        with transaction.atomic():
            if banned_user.profile.is_banned:
                messages.error(request, 'User is already banned.')
            else:
                ban = Ban(
                    admin=request.user,
                    banned_user=banned_user,
                    reason=reason
                )

                ban.save()
            return redirect(user, username=username)
    elif action == 'unban':
        ban = banned_user.ban_set.first()
        if ban:
            ban.delete()
        else:
            messages.error(request, 'User is not banned.')
        return redirect(user, username=username)

    messages.error(request, 'An error occurred. Please try again.')
    return redirect(user, username=username)

def hide(request):
    if not admin(request):
        return redirect(index)

    model_id = request.POST.get('model_id')
    revision = request.POST.get('revision')

    if not model_id or not revision:
        return redirect(index)
    
    hidden_model = Model.objects.get(model_id=model_id, revision=revision)

    action = request.POST.get('type')

    try:
        if action == 'hide':
            hidden_model.is_hidden = True
        elif action == 'unhide':
            hidden_model.is_hidden = False
        else:
            raise ValueError('Invalid argument for action.')

        hidden_model.save()
    except ValueError:
        messages.error(request, 'An error occurred. Please try again.')

    return redirect(model, model_id=model_id, revision=revision)
