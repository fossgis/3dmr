import os
import logging
import mistune

from django.db import transaction
from django.contrib import messages

from .models import Model, LatestModel, Change, Category, Location
from .utils import MODEL_DIR

from mainapp.markdown import markdown

logger = logging.getLogger(__name__)

def upload(model_file, options={}):
    try:
        with transaction.atomic():
            if options.get('revision', False):
                lm = LatestModel.objects.get(model_id=options['model_id'])
                m = Model.objects.get(model_id=lm.model_id, revision=lm.revision)

                location = m.location
                if location is not None:
                    location.pk = None
                    location.id = None
                    location.save()

                m.pk = None
                m.id = None
                m.revision += 1
                m.author = options['author']
                m.location = location
                m.save()

                m.categories.add(*lm.categories.all())
                m.save()
            else:
                # get the model_id for this model.
                try:
                    next_model_id = LatestModel.objects.latest('model_id').model_id + 1
                except LatestModel.DoesNotExist:
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
                    translation_x=-options['translation'][0],
                    translation_y=-options['translation'][1],
                    translation_z=-options['translation'][2],
                    rotation=options['rotation'],
                    scale=options['scale']
                )

                m.save()

                for category_name in options['categories']:
                    try:
                        category = Category.objects.get(name=category_name)
                    except:
                        category = Category(name=category_name)

                    category.save()
                    m.categories.add(category)

                m.save()

            change = Change(
                author=options['author'],
                model=m,
                typeof=1 if options.get('revision') else 0
            )

            change.save()

            filepath = '{}/{}/{}.glb'.format(MODEL_DIR, m.model_id, m.revision)
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
            m.translation_x = options['translation'][0]
            m.translation_y = options['translation'][1]
            m.translation_z = options['translation'][2]
            m.rotation = options['rotation']
            m.scale = options['scale']
            m.license = options['license']

            rendered_description = markdown(options['description'])
            m.rendered_description = rendered_description

            m.categories.clear()
            for category_name in options['categories']:
                try:
                    category = Category.objects.get(name=category_name)
                except:
                    category = Category(name=category_name)
                
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
