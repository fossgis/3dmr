from django.db import models
from django.contrib.postgres import fields
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_pgviews import view as pg

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
    tags = fields.HStoreField(default={})
    rotation = models.FloatField(default=0.0)
    scale = models.FloatField(default=1.0)
    translation_x = models.FloatField(default=0.0)
    translation_y = models.FloatField(default=0.0)
    translation_z = models.FloatField(default=0.0)

    class Meta:
        app_label = 'mainapp'

class LatestModel(pg.MaterializedView):
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
    tags = fields.HStoreField(default={})
    rotation = models.FloatField(default=0.0)
    scale = models.FloatField(default=1.0)
    translation_x = models.FloatField(default=0.0)
    translation_y = models.FloatField(default=0.0)
    translation_z = models.FloatField(default=0.0)

    concurrent_index = 'id'
    sql = """
        SELECT
            latest.id AS id,
            latest.model_id AS model_id,
            latest.revision AS revision,
            latest.title AS title,
            latest.description AS description,
            latest.rendered_description AS rendered_description,
            latest.upload_date AS upload_date,
            latest.latitude AS latitude,
            latest.longitude AS longitude,
            latest.license AS license,
            latest.rotation AS rotation,
            latest.scale AS scale,
            latest.translation_x AS translation_x,
            latest.translation_y AS translation_y,
            latest.translation_z AS translation_z,
            latest.author_id AS author_id,
            latest.tags AS tags
        FROM mainapp_model latest
            LEFT JOIN mainapp_model older
                ON latest.model_id = older.model_id AND
                   latest.revision < older.revision
        WHERE older.revision is NULL
    """

    class Meta:
        app_label = 'mainapp'
        db_table = 'mainapp_latestmodel'
        managed = False

# View for the categories field above
class ModelCategories(pg.View):
    sql = """
        SELECT
            id AS id,
            model_id AS latestmodel_id,
            category_id AS category_id
        FROM mainapp_model_categories
    """

    class Meta:
        app_label = 'mainapp'
        db_table = 'mainapp_latestmodel_categories'
        managed = False

@receiver(post_save, sender=Model)
def model_saved(sender, action=None, instance=None, **kwargs):
    LatestModel.refresh(concurrently=True)

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

class Ban(models.Model):
    # note: the models.PROTECT means that admin accounts who
    # have banned other users cannot be removed from the database.
    admin = models.ForeignKey(User, models.PROTECT, related_name='admin')
    banned_user = models.ForeignKey(User, models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=1024)
