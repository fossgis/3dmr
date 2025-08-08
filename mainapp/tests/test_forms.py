from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.test import SimpleTestCase, TestCase

from mainapp.forms import (
    CategoriesField,
    CompatibleFloatField,
    MetadataForm,
    ModelField,
    OriginField,
    TagField,
    UploadFileForm,
    UploadFileMetadataForm,
)


class TagFieldTests(SimpleTestCase):
    def test_valid_tags(self):
        field = TagField()
        value = "shape=pyramidal, building=yes"
        cleaned = field.clean(value)
        self.assertEqual(cleaned, {"shape": "pyramidal", "building": "yes"})

    def test_invalid_tags(self):
        field = TagField()
        with self.assertRaises(ValidationError):
            field.clean("pyramidal building")

    def test_empty_tags(self):
        field = TagField(required=False)
        cleaned = field.clean("")
        self.assertEqual(cleaned, {})


class CategoriesFieldTests(SimpleTestCase):
    def test_cleaned_categories(self):
        field = CategoriesField()
        cleaned = field.clean("monuments, tall")
        self.assertEqual(cleaned, ["monuments", "tall"])

    def test_empty_categories(self):
        field = CategoriesField(required=False)
        cleaned = field.clean("")
        self.assertEqual(cleaned, [])


class OriginFieldTests(SimpleTestCase):
    def test_valid_origin(self):
        field = OriginField()
        cleaned = field.clean("3 -4.5 1.03")
        self.assertEqual(cleaned, [-3.0, 4.5, -1.03])

    def test_comma_decimal(self):
        field = OriginField()
        cleaned = field.clean("3,5 0,2 -1,0")
        self.assertEqual(cleaned, [-3.5, -0.2, 1.0])

    def test_too_many_values(self):
        field = OriginField()
        with self.assertRaises(ValidationError):
            field.clean("1 2")

    def test_empty_origin(self):
        field = OriginField()
        cleaned = field.clean("")
        self.assertEqual(cleaned, [0, 0, 0])


class CompatibleFloatFieldTests(SimpleTestCase):
    def test_valid_float_dot(self):
        field = CompatibleFloatField(
            label="valid_field", required=False, attrs={"value": "3.14"}
        )
        cleaned = field.clean("3.14")
        self.assertEqual(cleaned, 3.14)

    def test_valid_float_comma(self):
        field = CompatibleFloatField(label="valid_field", attrs={"value": "3.14"})
        cleaned = field.clean("3,14")
        self.assertEqual(cleaned, 3.14)

    def test_invalid_float(self):
        field = CompatibleFloatField(
            label="invalid_field", attrs={"value": "notanumber"}
        )
        with self.assertRaises(ValidationError):
            field.clean("notanumber")

    def test_empty_value(self):
        field = CompatibleFloatField(
            label="empty_field", required=False, attrs={"value": ""}
        )
        cleaned = field.clean("")
        self.assertIsNone(cleaned)
        cleaned = field.clean(None)
        self.assertIsNone(cleaned)


class ModelFieldTests(TestCase):
    def test_bad_glb_file(self):
        data = b"not a glb"
        uploaded = SimpleUploadedFile("bad.glb", data, content_type="model/gltf-binary")
        instance = ModelField()
        with self.assertRaises(ValidationError):
            instance.clean(uploaded)


class FormIntegrationTests(SimpleTestCase):
    def test_upload_file_form_missing(self):
        form = UploadFileForm(data={})
        self.assertFalse(form.is_valid())

    def test_upload_file_form_valid(self):
        with open("mainapp/tests/test_files/test_model.glb", "rb") as f:
            data = f.read()
        uploaded = SimpleUploadedFile("model.glb", data, content_type="model/gltf-binary")

        form = UploadFileForm(files={"model_file": uploaded})
        self.assertTrue(form.is_valid())

    def test_metadata_form_valid(self):
        form_data = {
            "title": "Test Model",
            "description": "A model",
            "latitude": "2.294481",
            "longitude": "48.858370",
            "categories": "monuments, tall",
            "tags": "shape=cube",
            "translation": "1 2 3",
            "rotation": "45",
            "scale": "1.2",
            "model_source": "self_created",
            "source": None,
            "license": "0",
        }
        form = MetadataForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned = form.clean()
        self.assertEqual(cleaned["categories"], ["monuments", "tall"])
        self.assertEqual(cleaned["tags"], {"shape": "cube"})
        self.assertEqual(cleaned["translation"], [-1.0, -2.0, -3.0])

    def test_metadata_form_other_source(self):
        form_data = {
            "title": "Test",
            # other source requires a source URL
            "model_source": "other_source",
            "license": "0",
        }

        form = MetadataForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Please specify the other source.", form.errors.get("source", []))

    def test_upload_file_metadata_form_missing(self):
        form = UploadFileMetadataForm(data={})
        self.assertFalse(form.is_valid())

    def test_upload_file_metadata_form_valid(self):
        with open("mainapp/tests/test_files/test_model.glb", "rb") as f:
            data = f.read()
        uploaded = SimpleUploadedFile("model.glb", data, content_type="model/gltf-binary")
        form_data = {
            "title": "Test",
            "description": "",
            "latitude": "",
            "longitude": "",
            "categories": "",
            "tags": "",
            "translation": "",
            "rotation": "",
            "scale": "",
            "model_source": "self_created",
            "license": "0",
        }

        form = UploadFileMetadataForm(data=form_data, files={"model_file": uploaded})
        self.assertTrue(form.is_valid())
