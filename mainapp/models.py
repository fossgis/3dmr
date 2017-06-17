from django.db import models

# Create your models here.
class User(models.Model):
	osm_id = models.IntegerField()
	name = models.CharField(max_length=64)
	description = models.CharField(max_length=2048)
	rendered_description = models.CharField(max_length=4096)
	avatar_url = models.CharField(max_length=256)
	admin = models.BooleanField()
	banned = models.BooleanField()

class Category(models.Model):
	name = models.CharField(max_length=256)

class Model(models.Model):
	model_id = models.IntegerField()
	revision = models.IntegerField()
	description = models.CharField(max_length=512)
	upload_date = models.DateField()
	latitude = models.FloatField()
	longitude = models.FloatField()
	license = models.IntegerField()
	categories = models.ManyToManyField(Category)

class Change(models.Model):
	author = models.ForeignKey(User, models.CASCADE)
	model = models.ForeignKey(Model, models.CASCADE)
	typeof = models.IntegerField()
	datetime = models.DateTimeField()

class Comment(models.Model):
	author = models.ForeignKey(User, models.CASCADE)
	model = models.ForeignKey(Model, models.CASCADE)
	comment = models.CharField(max_length=1024)
	datetime = models.DateTimeField()

class TagKey(models.Model):
	name = models.CharField(max_length=256)

class TagValue(models.Model):
	name = models.CharField(max_length=256)

# ternary relationship between Model, TagValue and TagKey
class ModelTagValueTagKey(models.Model):
	model = models.ForeignKey(Model, models.CASCADE)
	tag_key = models.ForeignKey(TagKey, models.CASCADE)
	tag_value = models.ForeignKey(TagValue, models.CASCADE)
