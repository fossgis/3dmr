from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=2048, default='Your description...')
    rendered_description = models.CharField(max_length=4096, default='<p>Your description...</p>')
    admin = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.profile.save()

class Category(models.Model):
    name = models.CharField(max_length=256)

class Model(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
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
