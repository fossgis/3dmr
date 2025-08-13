from django.urls import re_path

from . import views
from . import api

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^login$', views.login, name='login'),
    re_path(r'^logout$', views.logout_user, name='logout'),
    re_path(r'^docs$', views.docs, name='docs'),
    re_path(r'^downloads$', views.downloads, name='downloads'),
    re_path(r'^model/(?P<model_id>[0-9]+)$', views.model, name='model'),
    re_path(r'^model/(?P<model_id>[0-9]+)/(?P<revision>[0-9]+)$', views.model, name='model'),
    re_path(r'^search$', views.search, name='search'),
    re_path(r'^upload$', views.upload, name='upload'),
    re_path(r'^revise/(?P<model_id>[0-9]+)$', views.revise, name='revise'),
    re_path(r'^edit/(?P<model_id>[0-9]+)/(?P<revision>[0-9]+)$', views.edit, name='edit'),
    re_path(r'^user/(?P<uid>[0-9]+)?$', views.user, name='user'),
    re_path(r'^map$', views.modelmap, name='map'),
    re_path(r'^action/editprofile$', views.editprofile, name='editprofile'),
    re_path(r'^action/ban$', views.ban, name='ban'),
    re_path(r'^action/hide_model$', views.hide_model, name='hide_model'),

    re_path(r'^api/info/(?P<model_id>[0-9]+)$', api.get_info, name='get_info'),

    re_path(r'^api/model/(?P<model_id>[0-9]+)/(?P<revision>[0-9]+)$', api.get_model, name='get_model'),
    re_path(r'^api/model/(?P<model_id>[0-9]+)$', api.get_model, name='get_model'),

    re_path(r'^api/tag/(?P<tag>.*)/(?P<page_id>[0-9]+)$', api.lookup_tag, name='lookup_tag'),
    re_path(r'^api/tag/(?P<tag>.*)$', api.lookup_tag, name='lookup_tag'),
    re_path(r'^api/category/(?P<category>.*)/(?P<page_id>[0-9]+)$', api.lookup_category, name='lookup_category'),
    re_path(r'^api/category/(?P<category>.*)$', api.lookup_category, name='lookup_category'),
    re_path(r'^api/author/(?P<uid>[0-9]+)/(?P<page_id>[0-9]+)$', api.lookup_author, name='lookup_author'),
    re_path(r'^api/author/(?P<uid>[0-9]+)$', api.lookup_author, name='lookup_author'),

    re_path(r'^api/search/?(?P<latitude>-?[0-9]+(\.[0-9]+)?)/(?P<longitude>-?[0-9]+(\.[0-9]+)?)/(?P<distance>[0-9]+(\.[0-9]+)?)/(?P<page_id>[0-9]+)$', api.search_range, name='lookup_range'),
    re_path(r'^api/search/(?P<latitude>-?[0-9]+(\.[0-9]+)?)/(?P<longitude>-?[0-9]+(\.[0-9]+)?)/(?P<distance>[0-9]+(\.[0-9]+)?)$', api.search_range, name='lookup_range'),
    re_path(r'^api/search/title/(?P<title>.*)/(?P<page_id>[0-9]+)$', api.search_title, name='search_title'),
    re_path(r'^api/search/title/(?P<title>.*)$', api.search_title, name='search_title'),
    re_path(r'^api/search/full$', api.search_full, name='search_full'),
]
