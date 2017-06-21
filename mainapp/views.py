from django.shortcuts import render
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

def user(request, user_id=None):
	if user_id:
		# we're querying an user
		user = User.objects.filter(username=user_id)
		if len(user) != 1:
			pass # error
		user = user[0] # there's only a single user in the query at this point

		oauth_user = UserSocialAuth.objects.filter(user=user)
		if len(oauth_user) != 1:
			pass # error
		oauth_user = oauth_user[0] # same as above

		context = {'user': {
			'username': user.username,
			'avatar': oauth_user.extra_data['avatar'],
		}}
	else:
		# returning current user's profile
		pass # TODO

	return render(request, 'mainapp/user.html', context)
