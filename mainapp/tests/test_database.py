import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from mainapp import database
from mainapp.markdown import markdown
from mainapp.models import Category, Change, Location, Model


User = get_user_model()


@override_settings(
    MODEL_DIR=tempfile.mkdtemp(prefix="3dmr_", )
)
class DatabaseTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="userpassword"
        )

        Category.objects.create(name="ExistingCategory1")

    def tearDown(self):
        shutil.rmtree(settings.MODEL_DIR)

    def _create_dummy_file(self, name="test_model.glb"):
        with open("mainapp/tests/test_files/test_model.glb", "rb") as f:
            self.model_file = f.read()
        return SimpleUploadedFile(name, self.model_file, content_type="model/gltf-binary")

    def test_upload_new_model_first_ever(self):
        model_file = self._create_dummy_file()
        options = {
            "title": "Test Model 1",
            "description": "This is a test description.",
            "tags": {"shape": "pyramidal", "building": "yes", "test": "yes"},
            "categories": ["TestCategory1", "ExistingCategory1"],
            "latitude": 10.0,
            "longitude": 20.0,
            "source": None,
            "license": 1,
            "author": self.user,
            "translation": [1.0, 2.0, 3.0],
            "rotation": 90.0,
            "scale": 1.5,
            "revision": False,
        }

        created_model = database.upload(model_file, options)

        self.assertIsNotNone(created_model, "Model creation should not return None")
        self.assertEqual(created_model.title, options["title"])
        self.assertEqual(created_model.author, options["author"])
        self.assertEqual(
            created_model.rendered_description, markdown(options["description"])
        )
        self.assertEqual(created_model.translation_x, -options["translation"][0])
        self.assertEqual(created_model.translation_y, -options["translation"][1])
        self.assertEqual(created_model.translation_z, -options["translation"][2])
        self.assertEqual(created_model.license, options["license"])
        self.assertEqual(created_model.revision, 1)

        latest_model = Model.objects.get(model_id=created_model.model_id, latest=True)
        self.assertEqual(latest_model.revision, created_model.revision)
        self.assertEqual(latest_model.title, options["title"])
        self.assertEqual(latest_model.author, options["author"])

        change_record = Change.objects.get(model=created_model)
        expected_typeof = 1 if options["revision"] else 0
        self.assertEqual(change_record.author, options["author"])
        self.assertEqual(change_record.typeof, expected_typeof)

        expected_category_set = set(options["categories"])
        self.assertEqual(created_model.categories.count(), len(expected_category_set))
        for cat_name in expected_category_set:
            self.assertTrue(created_model.categories.filter(name=cat_name).exists())

        self.assertIsNotNone(created_model.location)
        self.assertEqual(created_model.location.latitude, options["latitude"])
        self.assertEqual(created_model.location.longitude, options["longitude"])

        expected_filepath = os.path.join(
            settings.MODEL_DIR, str(created_model.model_id), f"{created_model.revision}.glb"
        )
        self.assertTrue(os.path.exists(expected_filepath))

    def test_upload_new_model_increments_model_id(self):
        opts1 = {
            "title": "Model A",
            "description": "A",
            "tags": {},
            "categories": ["CatA"],
            "latitude": None,
            "longitude": None,
            "source": None,
            "license": 8,
            "author": self.user,
            "translation": [0, 0, 0],
            "rotation": 0,
            "scale": 1,
            "revision": False,
        }
        m1 = database.upload(self._create_dummy_file(name="a.glb"), opts1)
        self.assertEqual(m1.model_id, 1)

        opts2 = {
            "title": "Model B",
            "description": "B",
            "tags": {},
            "categories": ["CatB"],
            "latitude": None,
            "longitude": None,
            "source": None,
            "license": 9,
            "author": self.user,
            "translation": [0, 0, 0],
            "rotation": 0,
            "scale": 1,
            "revision": False,
        }
        m2 = database.upload(self._create_dummy_file(name="b.glb"), opts2)
        self.assertEqual(
            m2.model_id, 2, "Model ID should increment for the second model"
        )

        self.assertEqual(m1.title, opts1["title"])
        self.assertEqual(m2.title, opts2["title"])

    def test_upload_new_model_no_location(self):
        model_file = self._create_dummy_file()
        options = {
            "title": "No Location Model",
            "description": "Desc.",
            "tags": {},
            "categories": ["NoLocationCat"],
            "latitude": None,
            "longitude": None,
            "source": None,
            "license": 2,
            "author": self.user,
            "translation": [0, 0, 0],
            "rotation": 0,
            "scale": 1.0,
            "revision": False,
        }

        created_model = database.upload(model_file, options)

        self.assertIsNotNone(created_model)
        self.assertIsNone(created_model.location)
        self.assertEqual(Category.objects.count(), 2)

    def test_upload_revision_model(self):
        initial_user = User.objects.create_user(
            username="initial_author", password="password123"
        )
        initial_options = {
            "title": "Initial Model",
            "description": "Initial.",
            "tags": {},
            "categories": ["VersionCat"],
            "latitude": 30.0,
            "longitude": 40.0,
            "license": 3,
            "author": initial_user,
            "translation": [1, 1, 1],
            "rotation": 0,
            "source": None,
            "scale": 1,
            "revision": False,
        }
        initial_file = self._create_dummy_file(name="initial.glb")
        initial_model = database.upload(initial_file, initial_options)

        self.assertIsNotNone(initial_model)
        self.assertEqual(initial_model.model_id, 1)
        self.assertEqual(initial_model.revision, 1)
        self.assertEqual(initial_model.author, initial_user)
        initial_location_pk = initial_model.location.pk

        revision_author = User.objects.create_user(
            username="revised_author", password="password123"
        )
        revision_file = self._create_dummy_file(name="revision.glb")
        revision_options = {
            "model_id": initial_model.model_id,
            "author": revision_author,
            "revision": True,
        }

        revised_model = database.upload(revision_file, revision_options)

        self.assertIsNotNone(revised_model, "Revision creation should not return None")
        self.assertEqual(revised_model.model_id, initial_model.model_id)
        self.assertEqual(revised_model.revision, 2, "Revision number should increment")
        self.assertEqual(
            revised_model.author,
            revision_author,
            "Author should be updated for the new revision",
        )
        self.assertEqual(revised_model.title, initial_model.title)
        self.assertEqual(revised_model.license, initial_model.license)

        latest_model = Model.objects.get(model_id=initial_model.model_id, latest=True)
        self.assertEqual(latest_model.revision, 2)
        self.assertEqual(latest_model.title, initial_model.title)
        self.assertEqual(latest_model.author, revision_author)

        change_record = Change.objects.get(model=revised_model)
        self.assertEqual(change_record.author, revision_author)
        self.assertEqual(change_record.typeof, 1)

        self.assertEqual(revised_model.categories.count(), 1)
        self.assertTrue(revised_model.categories.filter(name="VersionCat").exists())
        self.assertEqual(latest_model.categories.count(), 1)
        self.assertTrue(latest_model.categories.filter(name="VersionCat").exists())

        self.assertIsNotNone(revised_model.location)
        self.assertNotEqual(
            revised_model.location.pk,
            initial_location_pk,
            "Location should be a new instance for new revision",
        )
        self.assertEqual(
            revised_model.location.latitude, initial_model.location.latitude
        )
        self.assertEqual(Location.objects.count(), 2)

        expected_filepath_rev = os.path.join(
            settings.MODEL_DIR, str(revised_model.model_id), f"{revised_model.revision}.glb"
        )
        self.assertTrue(os.path.exists(expected_filepath_rev))

    def test_edit_model_metadata(self):
        uploader = User.objects.create_user(username="uploader", password="password123")
        initial_options = {
            "title": "Editable Model",
            "description": "Old Description.",
            "tags": {},
            "categories": ["OldCat", "KeepCat"],
            "latitude": "50.0",
            "longitude": "60.0",
            "source": None,
            "license": 4,
            "author": uploader,
            "translation": [1, 2, 3],
            "rotation": 45,
            "scale": 2.0,
            "revision": False,
        }
        model_to_edit = database.upload(self._create_dummy_file(), initial_options)
        self.assertIsNotNone(model_to_edit)
        original_location_pk = model_to_edit.location.pk
        self.assertEqual(Category.objects.count(), 3)

        edit_options = {
            "model_id": model_to_edit.model_id,
            "revision": model_to_edit.revision,
            "title": "Updated Model Title",
            "description": "New Shiny Description!",
            "tags": {},
            "categories": ["NewCat1", "KeepCat", "NewCat2"],
            "latitude": 55.5,
            "longitude": 66.6,
            "source": "https://3dmr.eu/",
            "license": 5,
            "translation": [-5.0, -6.0, -7.0],
            "rotation": 180.0,
            "scale": 0.5,
        }

        result = database.edit(edit_options)
        self.assertTrue(result, "Edit function should return True on success")

        edited_model = Model.objects.get(pk=model_to_edit.pk)
        self.assertEqual(edited_model.title, edit_options["title"])
        self.assertEqual(edited_model.description, edit_options["description"])
        self.assertEqual(
            edited_model.rendered_description, markdown(edit_options["description"])
        )
        self.assertEqual(edited_model.tags, edit_options["tags"])
        self.assertEqual(edited_model.license, edit_options["license"])
        self.assertEqual(edited_model.translation_x, edit_options["translation"][0])
        self.assertEqual(edited_model.translation_y, edit_options["translation"][1])
        self.assertEqual(edited_model.translation_z, edit_options["translation"][2])
        self.assertEqual(edited_model.rotation, edit_options["rotation"])
        self.assertEqual(edited_model.scale, edit_options["scale"])

        self.assertEqual(edited_model.categories.count(), 3)
        self.assertTrue(edited_model.categories.filter(name="NewCat1").exists())
        self.assertTrue(edited_model.categories.filter(name="KeepCat").exists())
        self.assertTrue(edited_model.categories.filter(name="NewCat2").exists())
        self.assertFalse(edited_model.categories.filter(name="OldCat").exists())
        self.assertEqual(Category.objects.count(), 5)

        self.assertIsNotNone(edited_model.location)
        self.assertEqual(
            edited_model.location.pk,
            original_location_pk,
            "Location should be updated, not recreated",
        )
        self.assertEqual(edited_model.location.latitude, edit_options["latitude"])
        self.assertEqual(edited_model.location.longitude, edit_options["longitude"])
        self.assertEqual(Location.objects.count(), 1)

        latest_edited_model = Model.objects.get(
            model_id=edited_model.model_id,
            latest=True
        )
        self.assertEqual(latest_edited_model.title, edit_options["title"])
        self.assertEqual(latest_edited_model.source, edit_options["source"])
        self.assertEqual(latest_edited_model.license, edit_options["license"])

    def test_edit_model_add_location(self):
        """Test editing a model to add a location where it previously had none."""
        model_options = {
            "title": "Needs Location",
            "description": "No loc.",
            "tags": {"loc": "add"},
            "categories": ["LocAddCat"],
            "latitude": None,
            "longitude": None,
            "source": None,
            "license": 6,
            "author": self.user,
            "translation": [0, 0, 0],
            "rotation": 0,
            "scale": 1,
            "revision": False,
        }
        model_to_edit = database.upload(self._create_dummy_file(), model_options)
        self.assertIsNone(model_to_edit.location)
        self.assertEqual(Location.objects.count(), 0)

        edit_options = {
            "model_id": model_to_edit.model_id,
            "revision": model_to_edit.revision,
            "title": model_to_edit.title,
            "description": model_to_edit.description,
            "tags": model_to_edit.tags,
            "categories": ["LocAddCat"],
            "latitude": 70.0,
            "longitude": 80.0,
            "source": None,
            "license": model_to_edit.license,
            "translation": [0, 0, 0],
            "rotation": 0,
            "scale": 1,
        }
        result = database.edit(edit_options)
        self.assertTrue(result)

        edited_model = Model.objects.get(pk=model_to_edit.pk)
        self.assertIsNotNone(edited_model.location)
        self.assertEqual(edited_model.location.latitude, edit_options["latitude"])
        self.assertEqual(edited_model.location.longitude, edit_options["longitude"])
        self.assertEqual(Location.objects.count(), 1)

    def test_edit_model_remove_location(self):
        model_options = {
            'title': 'Loses Location', 'description': 'Has loc.', 'tags': {'loc': 'remove'},
            'categories': ['LocRemoveCat'], 'latitude': '90.0', 'longitude': '100.0',
            'source': None, 'license': 7, 'author': self.user, 'translation': [0,0,0],
            'rotation': 0, 'scale': 1, 'revision': False
        }
        model_to_edit = database.upload(self._create_dummy_file(), model_options)
        self.assertIsNotNone(model_to_edit.location)
        self.assertEqual(Location.objects.count(), 1)

        edit_options = {
            'model_id': model_to_edit.model_id, 'revision': model_to_edit.revision,
            'title': model_to_edit.title, 'description': model_to_edit.description,
            'tags': model_to_edit.tags, 'categories': ['LocRemoveCat'],
            'latitude': None, 'longitude': None, 'source': None,
            'license': model_to_edit.license, 'translation': [0,0,0],
            'rotation': 0, 'scale': 1
        }
        result = database.edit(edit_options)

        self.assertTrue(result)

        edited_model = Model.objects.get(pk=model_to_edit.pk)
        self.assertIsNone(edited_model.location, "Location should have been removed")
        self.assertEqual(Location.objects.count(), 0, "Location record should be deleted")

    def test_delete_model(self):
        model_file = self._create_dummy_file()
        options = {
            "title": "Model to Delete",
            "description": "This model will be deleted.",
            "tags": {"delete": "yes"},
            "categories": ["DeleteCat"],
            "latitude": 20.0,
            "longitude": 30.0,
            "source": None,
            "license": 8,
            "author": self.user,
            "translation": [0, 0, 0],
            "rotation": 0,
            "scale": 1,
            "revision": False,
        }

        created_model = database.upload(model_file, options)
        self.assertIsNotNone(created_model)

        delete_result = database.delete(created_model.model_id)
        self.assertTrue(delete_result, "Delete should return True on success")

        with self.assertRaises(Model.DoesNotExist):
            Model.objects.get(pk=created_model.pk)

        expected_path = os.path.join(
            settings.MODEL_DIR, str(created_model.model_id)
        )
        self.assertFalse(os.path.exists(expected_path), "Model file should be deleted")

        self.assertEqual(Change.objects.filter(model=created_model).count(), 0)
