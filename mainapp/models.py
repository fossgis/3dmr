from django.db import models
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .utils import CHANGES

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=2048, default='Your description...')
    rendered_description = models.CharField(max_length=4096, default='<p>Your description...</p>')
    is_admin = models.BooleanField(default=False)

    @property
    def is_banned(self):
        return self.user.ban_set.all().first() != None

    @property
    def avatar(self):
        avatar = self.user.social_auth.first().extra_data.get('avatar')
        if avatar is None:
            avatar = staticfiles_storage.url('mainapp/images/default_avatar.svg')
        return avatar

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Category(models.Model):
    name = models.CharField(max_length=256)

class Location(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()

class Model(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    model_id = models.IntegerField()
    revision = models.IntegerField()
    title = models.CharField(max_length=32)
    description = models.CharField(max_length=512)
    rendered_description = models.CharField(max_length=1024)
    upload_date = models.DateField(auto_now_add=True)
    location = models.OneToOneField(Location, null=True, default=None, on_delete=models.CASCADE)
    license = models.IntegerField()
    categories = models.ManyToManyField(Category)
    tags = models.JSONField(null=True)
    rotation = models.FloatField(default=0.0)
    scale = models.FloatField(default=1.0)
    translation_x = models.FloatField(default=0.0)
    translation_y = models.FloatField(default=0.0)
    translation_z = models.FloatField(default=0.0)
    is_hidden = models.BooleanField(default=False)

class LatestModel(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    model_id = models.IntegerField()
    revision = models.IntegerField()
    title = models.CharField(max_length=32)
    description = models.CharField(max_length=512)
    rendered_description = models.CharField(max_length=1024)
    upload_date = models.DateField(auto_now_add=True)
    location = models.OneToOneField(Location, null=True, default=None, on_delete=models.CASCADE)
    license = models.IntegerField()
    categories = models.ManyToManyField(Category)
    tags = models.JSONField(null=True)
    rotation = models.FloatField(default=0.0)
    scale = models.FloatField(default=1.0)
    translation_x = models.FloatField(default=0.0)
    translation_y = models.FloatField(default=0.0)
    translation_z = models.FloatField(default=0.0)
    is_hidden = models.BooleanField(default=False)

@receiver(post_save, sender=Model)
def model_saved(sender, instance, created, **kwargs):
    latest = Model.objects.filter(model_id=instance.model_id).order_by('-revision').first()
    # Confirm if the updated instance is the latest model. If not,
    # it implies the update is trigerred on some other version by
    # dev and we don't want to trigger signal in such case
    if latest == instance: 
        with transaction.atomic():
            lm, created = LatestModel.objects.update_or_create(
                model_id=instance.model_id,
                defaults={
                    'author': instance.author,
                    'revision': instance.revision,
                    'title': instance.title,
                    'description': instance.description,
                    'rendered_description': instance.rendered_description,
                    'upload_date': instance.upload_date,
                    'location': instance.location,
                    'license': instance.license,
                    'tags': instance.tags,
                    'rotation': instance.rotation,
                    'scale': instance.scale,
                    'translation_x': instance.translation_x,
                    'translation_y': instance.translation_y,
                    'translation_z': instance.translation_z,
                    'is_hidden': instance.is_hidden
                }
            )

            lm.categories.clear()
            lm.categories.add(*instance.categories.all())

class Change(models.Model):
    author = models.ForeignKey(User, models.CASCADE)
    model = models.ForeignKey(Model, models.CASCADE)
    typeof = models.IntegerField()
    datetime = models.DateTimeField(auto_now_add=True)

    @property
    def typeof_text(self):
        return CHANGES[self.typeof]

class Comment(models.Model):
    author = models.ForeignKey(User, models.CASCADE)
    model = models.ForeignKey(Model, models.CASCADE)
    comment = models.CharField(max_length=1024)
    rendered_comment = models.CharField(max_length=2048)
    datetime = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField(default=False)

class Ban(models.Model):
    # note: the models.PROTECT means that admin accounts who
    # have banned other users cannot be removed from the database.
    admin = models.ForeignKey(User, models.PROTECT, related_name='admin')
    banned_user = models.ForeignKey(User, models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=1024)
