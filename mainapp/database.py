import os
import logging
import shutil

from django.db import transaction
from django.conf import settings
from django.contrib import messages

from .models import Model, Change, Category, Location

from mainapp.markdown import markdown

logger = logging.getLogger(__name__)

def upload(model_file, options={}):
    try:
        with transaction.atomic():
            if options.get('revision', False):
                m = Model.objects.get(model_id=options['model_id'], latest=True)

                categories = m.categories.all()

                location = m.location
                if location is not None:
                    location.pk = None
                    location.id = None
                    location._state.adding = True
                    location.save()

                m.pk = None
                m.id = None
                m.revision += 1
                m.author = options['author']
                m.location = location
                m.latest = True
                m._state.adding = True
                m.save()
                m.categories.set(categories)
            else:
                # get the model_id for this model.
                try:
                    next_model_id = Model.objects.latest('model_id').model_id + 1
                except Model.DoesNotExist:
                    next_model_id = 1 # no models in db

                rendered_description = markdown(options['description'])

                latitude = options['latitude']
                longitude = options['longitude']

                if latitude and longitude:
                    location = Location(
                        latitude=latitude,
                        longitude=longitude
                    )
                    location.save()
                else:
                    location = None


                m = Model(
                    model_id=next_model_id,
                    revision=1,
                    title=options['title'],
                    description=options['description'],
                    rendered_description=rendered_description,
                    tags=options['tags'],
                    location=location,
                    license=options['license'],
                    author=options['author'],
                    source=options['source'],
                    latest=True
                )

                m.save()

                for category_name in options['categories']:
                    category, created = Category.objects.get_or_create(name=category_name)
                    m.categories.add(category)

            change = Change(
                author=options['author'],
                model=m,
                typeof=1 if options.get('revision') else 0
            )

            change.save()

            filepath = '{}/{}/{}.glb'.format(settings.MODEL_DIR, m.model_id, m.revision)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb+') as destination:
                for chunk in model_file.chunks():
                    destination.write(chunk)

            return m
    except:
        # We reach here when any of the following happens:
        # 1) Database constraint is violated
        # 2) File is not saved correctly to the specified directory
        # 3) Unknown

        # We should have verified everything to do with 1) earlier,
        # and notified the user if there was any error. Thus, it's
        # unlikely to be 1). 

        # Thus, we can assume that 2) and 3) are server errors, and that
        # the user can do nothing about them. Thus, report this.
        logger.exception('Fatal server error when uploading model.')

        return None

# Edits the metadata of a model, returns True when successful, and False otherwise
def edit(options):
    try:
        with transaction.atomic():
            m = Model.objects.get(model_id=options['model_id'], revision=options['revision'])

            m.title = options['title']
            m.description = options['description']
            m.tags = options['tags']
            m.source = options['source']
            m.license = options['license']

            rendered_description = markdown(options['description'])
            m.rendered_description = rendered_description

            m.categories.clear()
            for category_name in options['categories']:
                category, created = Category.objects.get_or_create(name=category_name)
                category.save()
                m.categories.add(category)

            latitude = options['latitude']
            longitude = options['longitude']

            if latitude and longitude:
                if m.location:
                    m.location.latitude = latitude
                    m.location.longitude = longitude
                    m.location.save()
                else:
                    location = Location(
                        latitude=latitude,
                        longitude=longitude
                    )
                    location.save()
                    m.location = location
            elif m.location:
                location = m.location
                m.location = None
                location.delete()

            m.save()
            
            return True
    except:
        logger.exception('Fatal server error when editing metadata.')

        return False

def delete(model_id):
    try:
        with transaction.atomic():
            models = Model.objects.filter(model_id=model_id)
            changes = Change.objects.filter(model__model_id=model_id)

            if not models.exists():
                logger.exception(None, 'Model does not exist.')
                return False
            
            for m in models:
                path = '{}/{}'.format(settings.MODEL_DIR, m.model_id)
                if os.path.exists(path):
                    shutil.rmtree(path)
            
            changes.delete()
            models.delete()
            
            logger.info('Model deleted successfully.')
            return True
    except Exception as e:
        logger.exception('Fatal server error when deleting model.')
        return False