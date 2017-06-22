from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^docs$', views.docs, name='docs'),
    url(r'^downloads$', views.downloads, name='downloads'),
    url(r'^model/(?P<model_id>[0-9]+)$', views.model, name='model'),
    url(r'^search$', views.search, name='search'),
    url(r'^upload$', views.upload, name='upload'),
    url(r'^user/(?P<username>.*)$', views.user, name='user'),
    url(r'^action/editprofile$', views.editprofile, name='editprofile'),
]
