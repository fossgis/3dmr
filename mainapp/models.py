import re

from django.db import models, transaction
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models.signals import post_save
from django.dispatch import receiver

from .utils import CHANGES

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
    
    @property
    def display_name(self):
        display_name = self.user.social_auth.first().extra_data.get('display_name')
        if display_name is None:
            display_name = self.user.username
        return display_name
    
    # uid is the unique permanent identifier for the user in the OpenStreetMap OAuth2 system
    # It is different from the display_name (at some places referred to as username), which is
    # not guaranteed to be unique and can be changed.
    @property
    def uid(self):
        uid = self.user.social_auth.first().uid
        return uid

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
    source = models.CharField(max_length=255, null=True)
    license = models.IntegerField()
    categories = models.ManyToManyField(Category)
    tags = models.JSONField(default=dict)
    rotation = models.FloatField(default=0.0)
    scale = models.FloatField(default=1.0)
    translation_x = models.FloatField(default=0.0)
    translation_y = models.FloatField(default=0.0)
    translation_z = models.FloatField(default=0.0)
    is_hidden = models.BooleanField(default=False)
    latest = models.BooleanField(default=False)

    @property
    def source_is_url(self):
        regex = r"https?:\/\/[^\s\"'>]+"
        if self.source:
            if re.match(regex, self.source):
                return True
            else:
                return False
        else:
            return False

    class Meta:
        unique_together = ('model_id', 'revision',)

        # UniqueConstraint automatically creates an Index expression
        constraints = [
            models.UniqueConstraint(
                fields=['model_id'],
                condition=models.Q(latest=True),
                name='unique_latest_model_per_id',
            )
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.latest:
                Model.objects.filter(
                    model_id=self.model_id,
                    latest=True
                ).exclude(pk=self.pk).update(latest=False)

            super().save(*args, **kwargs)

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
