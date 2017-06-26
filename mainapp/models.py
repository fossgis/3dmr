from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=2048, default='Your description...')
    rendered_description = models.CharField(max_length=4096, default='<p>Your description...</p>')
    is_admin = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    ban_date = models.DateField(default=None, null=True)

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
    title = models.CharField(max_length=32)
    description = models.CharField(max_length=512)
    rendered_description = models.CharField(max_length=1024)
    upload_date = models.DateField(auto_now_add=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    license = models.IntegerField()
    categories = models.ManyToManyField(Category)
    rotation = models.FloatField(default=0.0)
    scale = models.FloatField(default=1.0)
    translation_x = models.FloatField(default=0.0)
    translation_y = models.FloatField(default=0.0)
    translation_z = models.FloatField(default=0.0)

class Change(models.Model):
    author = models.ForeignKey(User, models.CASCADE)
    model = models.ForeignKey(Model, models.CASCADE)
    typeof = models.IntegerField()
    datetime = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    author = models.ForeignKey(User, models.CASCADE)
    model = models.ForeignKey(Model, models.CASCADE)
    comment = models.CharField(max_length=1024)
    rendered_comment = models.CharField(max_length=2048)
    datetime = models.DateTimeField(auto_now_add=True)

class TagKey(models.Model):
    name = models.CharField(max_length=256)

class TagValue(models.Model):
    name = models.CharField(max_length=256)

# ternary relationship between Model, TagValue and TagKey
class ModelTagValueTagKey(models.Model):
    model = models.ForeignKey(Model, models.CASCADE)
    tag_key = models.ForeignKey(TagKey, models.CASCADE)
    tag_value = models.ForeignKey(TagValue, models.CASCADE)
