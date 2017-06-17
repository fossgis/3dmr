from django.shortcuts import render

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

def user(request, user_id):
	return render(request, 'mainapp/user.html')
