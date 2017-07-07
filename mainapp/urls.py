from django.conf.urls import url

from . import views
from . import api

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^logout$', views.logout_user, name='logout'),
    url(r'^docs$', views.docs, name='docs'),
    url(r'^downloads$', views.downloads, name='downloads'),
    url(r'^model/(?P<model_id>[0-9]+)$', views.model, name='model'),
    url(r'^model/(?P<model_id>[0-9]+)/(?P<revision>[0-9]+)$', views.model, name='model'),
    url(r'^search$', views.search, name='search'),
    url(r'^upload$', views.upload, name='upload'),
    url(r'^user/(?P<username>.*)$', views.user, name='user'),
    url(r'^map$', views.map, name='map'),
    url(r'^action/editprofile$', views.editprofile, name='editprofile'),
    url(r'^action/addcomment$', views.addcomment, name='addcomment'),
    
    url(r'^api/info/(?P<model_id>[0-9]+)$', api.get_info, name='get_info'),
    url(r'^api/tag/(?P<tag>.*)/(?P<page_id>[0-9]+)$', api.lookup_tag, name='lookup_tag'),
    url(r'^api/tag/(?P<tag>.*)$', api.lookup_tag, name='lookup_tag'),
    url(r'^api/category/(?P<category>.*)/(?P<page_id>[0-9]+)$', api.lookup_category, name='lookup_category'),
    url(r'^api/category/(?P<category>.*)$', api.lookup_category, name='lookup_category'),
    url(r'^api/author/(?P<username>.*)/(?P<page_id>[0-9]+)$', api.lookup_author, name='lookup_author'),
    url(r'^api/author/(?P<username>.*)$', api.lookup_author, name='lookup_author'),
]
