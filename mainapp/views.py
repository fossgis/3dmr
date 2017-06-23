from django.shortcuts import render, get_object_or_404, redirect
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from .models import Model

import mistune

# Create your views here.
def index(request):
	models = Model.objects.order_by('pk')[:6]
	context = {
		'models': models,
	}

	return render(request, 'mainapp/index.html', context)

def docs(request):
	return render(request, 'mainapp/docs.html')

def downloads(request):
	return render(request, 'mainapp/downloads.html')

def model(request, model_id):
	model = Model.objects.filter(model_id=model_id).order_by('revision')[0]
	context = {
		'model': model,
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

	# query user
	user = get_object_or_404(User, username=username)
	oauth_user = get_object_or_404(UserSocialAuth, user=user)

	context = {'owner': {
		'username': user.username,
		'avatar': oauth_user.extra_data['avatar'],
		'profile': user.profile,
	}}

	return render(request, 'mainapp/user.html', context)

def editprofile(request):
	description = request.POST.get('desc')

	request.user.profile.description = description
	request.user.profile.rendered_description = mistune.markdown(description)
	request.user.save()

	return redirect(user, username='')
