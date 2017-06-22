from django.shortcuts import render, get_object_or_404
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User

# Create your views here.
def index(request):
	return render(request, 'mainapp/index.html')

def docs(request):
	return render(request, 'mainapp/docs.html')

def downloads(request):
	return render(request, 'mainapp/downloads.html')

def model(request, model_id):
	return render(request, 'mainapp/model.html')

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
	}}

	return render(request, 'mainapp/user.html', context)
