import logging

from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.db import transaction
from .models import Model, LatestModel, Comment, Category, Change, Ban, Location
from .forms import UploadFileForm, UploadFileMetadataForm, MetadataForm
from .utils import get_kv, update_last_page, get_last_page, CHANGES, admin, LICENSES_DISPLAY
import mainapp.database as database
from mainapp.markdown import markdown

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    update_last_page(request)

    MODELS_IN_INDEX_PAGE = 6
    models = LatestModel.objects.order_by('-pk')

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

    comments = Comment.objects.filter(model__model_id=model_id)

    if not admin(request):
        comments = comments.filter(is_hidden=False)

    context = {
        'model': model,
        'comments': comments.order_by('-datetime'),
        'old_comment': request.session.get('comment', ''),
        'license': LICENSES_DISPLAY[model.license]
    }

    return render(request, 'mainapp/model.html', context)

def search(request):
    update_last_page(request)

    RESULTS_PER_PAGE = 6

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

    try:
        if not admin(request):
            filtered_models = filtered_models.filter(is_hidden=False)

        ordered_models = filtered_models.order_by('-pk')
    except UnboundLocalError:
        # filtered_models isn't set, redirect to homepage
        return redirect(index)

    if not ordered_models:
        results = None
        paginator = None
    else:
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

def edit(request, model_id, revision):
    if request.user.is_authenticated and request.user.profile.is_banned:
        messages.error(request, 'You are banned. Editing models is not permitted.')
        return redirect(index)

    m = get_object_or_404(Model, model_id=model_id, revision=revision)

    if request.method == 'POST':
        form = MetadataForm(request.POST, request.FILES)

        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to use this feature.')
            return redirect(index)
        elif request.user != m.author:
            messages.error(request, 'You must be the author of the model to edit it.')
            return redirect(model, model_id=m.model_id, revision=m.revision)
        elif form.is_valid():
            status = database.edit({
                'title': form.cleaned_data['title'].strip(),
                'description': form.cleaned_data['description'].strip(),
                'latitude': form.cleaned_data['latitude'],
                'longitude': form.cleaned_data['longitude'],
                'categories': form.cleaned_data['categories'],
                'tags': form.cleaned_data['tags'],
                'translation': form.cleaned_data['translation'],
                'rotation': form.cleaned_data['rotation'],
                'scale': form.cleaned_data['scale'],
                'license': form.cleaned_data['license'],
                'model_id': model_id,
                'revision': revision
            })

            if status:
                return redirect(model, model_id=m.model_id, revision=m.revision)
            else:
                messages.error(request, 'Server error. Try again later.')
                return redirect(edit, model_id=model_id, revision=m.revision)
    else:
        if not request.user.is_authenticated:
            return redirect(index)
        elif request.user != m.author:
            messages.error(request, 'You must be the author of the model to edit it.')
            return redirect(model, model_id=m.model_id, revision=m.revision)

        tags = []
        for k, v in m.tags.items():
            tags.append("{}={}".format(k, v))

        initial = {
            'title': m.title,
            'description': m.description,
            'tags': ', '.join(tags),
            'categories': ', '.join(m.categories.all().values_list('name', flat=True)[::1]),
            # "+ 0" fixes negative zero float (-0.0)
            'translation': '{} {} {}'.format(-m.translation_x + 0, -m.translation_y + 0, -m.translation_z + 0),
            'rotation': m.rotation,
            'scale': m.scale,
            'license': m.license
        }

        if m.location:
            initial['latitude'] = m.location.latitude
            initial['longitude'] = m.location.longitude

        form = MetadataForm(initial=initial)

    return render(request, 'mainapp/edit.html', {
        'form': form,
        'model': m
    })


def revise(request, model_id):
    if request.user.is_authenticated and request.user.profile.is_banned:
        messages.error(request, 'You are banned. Revising models is not permitted.')
        return redirect(index)

    m = LatestModel.objects.get(model_id=model_id)

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to use this feature.')
            return redirect(index)
        elif request.user != m.author:
            messages.error(request, 'You must be the author of the model to revise it.')
            return redirect(model, model_id=m.model_id, revision=m.revision)
        elif form.is_valid():
            model_file = request.FILES['model_file']

            m = database.upload(model_file, {
                'revision': True,
                'model_id': model_id,
                'author': request.user
            })

            if m:
                return redirect(model, model_id=m.model_id, revision=m.revision)
            else:
                messages.error(request, 'Server error. Try again later.')
                return redirect(revise, model_id=model_id)
    else:
        if not request.user.is_authenticated:
            return redirect(index)
        elif request.user != m.author:
            messages.error(request, 'You must be the author of the model to revise it.')
            return redirect(model, model_id=m.model_id, revision=m.revision)

        form = UploadFileForm()

    return render(request, 'mainapp/revise.html', {
        'form': form,
        'model': m
    })

def upload(request):
    update_last_page(request)

    if request.user.is_authenticated and request.user.profile.is_banned:
        messages.error(request, 'You are banned. Uploading models is not permitted.')
        return redirect(index)

    if request.method == 'POST':
        form = UploadFileMetadataForm(request.POST, request.FILES)

        if not request.user.is_authenticated:
            # Show error in form, but don't redirect anywhere
            messages.error(request, 'You must be logged in to use this feature.')

            # Store form data in session, to use after login
            request.session['post_data'] = request.POST
        elif form.is_valid():
            model_file = request.FILES['model_file']

            m = database.upload(model_file, {
                'title': form.cleaned_data['title'].strip(),
                'description': form.cleaned_data['description'].strip(),
                'latitude': form.cleaned_data['latitude'],
                'longitude': form.cleaned_data['longitude'],
                'categories': form.cleaned_data['categories'],
                'tags': form.cleaned_data['tags'],
                'translation': form.cleaned_data['translation'],
                'rotation': form.cleaned_data['rotation'],
                'scale': form.cleaned_data['scale'],
                'license': form.cleaned_data['license'],
                'author': request.user
                })

            if m:
                return redirect(model, model_id=m.model_id, revision=m.revision)
            else:
                messages.error(request, 'Server error. Try again later.')
                request.session['post_data'] = request.POST
                return redirect(upload)
    else:
        if not request.user.is_authenticated:
            return redirect(index)

        post_data = request.session.get('post_data', None)
        if post_data: # if there's post_data in our session
            form = UploadFileMetadataForm(post_data)

            # clear previous errors in model_file
            form.errors['model_file'] = form.error_class()
            # add a single error to this field
            form.add_error('model_file', 'You must reupload your file.')

            del request.session['post_data']
        else: # otherwise
            form = UploadFileMetadataForm()

    return render(request, 'mainapp/upload.html', {'form': form})

def user(request, username):
    update_last_page(request)

    RESULTS_PER_PAGE = 6

    if username == '':
        if request.user:
            username = request.user.username # show our own userpage
        else:
            pass # redirect to index, no user to load

    user = get_object_or_404(User, username=username)

    models = user.latestmodel_set.order_by('-pk')

    if not admin(request):
        models = models.filter(is_hidden=False)

    changes = user.change_set.order_by('-pk')[:10] # get the 10 latest changes

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
            'avatar': user.profile.avatar,
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
    if not request.user.is_authenticated:
        return redirect(index)

    if request.user.profile.is_banned:
        messages.error(request, 'You are banned. Editing your profile is not permitted.')
        return redirect(index)

    description = request.POST.get('desc')

    request.user.profile.description = description
    request.user.profile.rendered_description = markdown(description)
    request.user.save()

    return redirect(user, username='')

def addcomment(request):
    def error(ajax, msg, redirect_page=index, *args, **kwargs):
        if ajax == 'false':
            messages.error(request, msg)
            return redirect(redirect_page, **kwargs)
        else:
            response = {
                'success': 'no',
                'error': msg
            }
            return JsonResponse(response)

    if not request.user.is_authenticated:
        return redirect(index)

    ajax = request.POST.get('ajax')

    if request.user.profile.is_banned:
        return error(ajax, 'You are banned. Commenting is not permitted.')

    comment = request.POST.get('comment').strip()
    model_id = int(request.POST.get('model_id'))
    revision = int(request.POST.get('revision'))

    if len(comment) == 0:
        return error(ajax, 'Comment must not be empty.')
    elif len(comment) > 1024:
        request.session['comment'] = comment
        return error(ajax, 'Comment too long.', model, model_id=model_id, revision=revision)

    author = request.user
    rendered_comment = markdown(comment)
    model_obj = get_object_or_404(Model, model_id=model_id, revision=revision)

    obj = Comment(
        author=author,
        comment=comment,
        rendered_comment=rendered_comment,
        model=model_obj,
    )

    obj.save()

    if request.session.get('comment'):
        del request.session['comment']

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

def hide_model(request):
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

def hide_comment(request):
    if not admin(request):
        return redirect(index)

    model_id = request.POST.get('model_id')
    revision = request.POST.get('revision')

    if not model_id or not revision:
        return redirect(index)

    comment_id = request.POST.get('comment_id')

    if not comment_id:
        return redirect(model, model_id=model_id, revision=revision)
    
    comment = Comment.objects.get(pk=comment_id)

    action = request.POST.get('type')

    try:
        if action == 'hide':
            comment.is_hidden = True
        elif action == 'unhide':
            comment.is_hidden = False
        else:
            raise ValueError('Invalid argument for action.')

        comment.save()
    except ValueError:
        messages.error(request, 'An error occurred. Please try again.')

    return redirect(model, model_id=model_id, revision=revision)
