from django.shortcuts import render

# Create your views here.
def index(request):
	return render(request, 'mainapp/index.html')

def docs(request):
	return render(request, 'mainapp/docs.html')

def downloads(request):
	return render(request, 'mainapp/downloads.html')

def model(request):
	return render(request, 'mainapp/model.html')
