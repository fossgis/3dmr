import io
import zipfile
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


def _make_zip(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buffer.seek(0)
    return buffer.read()


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

    @patch("mainapp.forms.ModelExtractor")
    @patch("mainapp.forms.Wavefront")
    def test_valid_zip_single_obj(self, mock_wavefront, mock_extractor):
        files = {"model.obj": "o Cube\nv 0 0 0"}
        data = _make_zip(files)
        uploaded = SimpleUploadedFile("model.zip", data, content_type="application/zip")
        instance = ModelField()
        mock_cm = mock_extractor.return_value.__enter__.return_value
        mock_cm.__getitem__.return_value = "path/to/model.obj"
        mock_wavefront.return_value = object()
        cleaned = instance.validate(uploaded)
        self.assertIsNone(cleaned)

    @patch("mainapp.forms.ModelExtractor")
    def test_no_obj_in_zip(self, mock_extractor):
        files = {"readme.txt": "no model here"}
        data = _make_zip(files)
        uploaded = SimpleUploadedFile("noobj.zip", data, content_type="application/zip")
        instance = ModelField()
        with self.assertRaises(ValidationError):
            instance.clean(uploaded)

    @patch("mainapp.forms.ModelExtractor")
    def test_multiple_objs_in_zip(self, mock_extractor):
        files = {"a.obj": "o A", "b.obj": "o B"}
        data = _make_zip(files)
        uploaded = SimpleUploadedFile("multi.zip", data, content_type="application/zip")
        instance = ModelField()
        with self.assertRaises(ValidationError):
            instance.clean(uploaded)

    def test_bad_zip_file(self):
        data = b"not a zip"
        uploaded = SimpleUploadedFile("bad.zip", data, content_type="application/zip")
        instance = ModelField()
        with self.assertRaises(ValidationError):
            instance.clean(uploaded)

    @patch("mainapp.forms.ModelExtractor")
    @patch("mainapp.forms.Wavefront", side_effect=Exception("parse error"))
    def test_invalid_obj_parsing(self, mock_wavefront, mock_extractor):
        files = {"model.obj": "corrupt content"}
        data = _make_zip(files)
        uploaded = SimpleUploadedFile(
            "corrupt.zip", data, content_type="application/zip"
        )
        instance = ModelField()
        mock_cm = mock_extractor.return_value.__enter__.return_value
        mock_cm.__getitem__.return_value = "path/to/model.obj"
        with self.assertRaises(ValidationError):
            instance.clean(uploaded)


class FormIntegrationTests(SimpleTestCase):
    def test_upload_file_form_missing(self):
        form = UploadFileForm(data={})
        self.assertFalse(form.is_valid())

    @patch("mainapp.forms.ModelExtractor")
    @patch("mainapp.forms.Wavefront")
    def test_upload_file_form_valid(self, mock_wavefront, mock_extractor):
        files = {"model.obj": "o Cube\nv 0 0 0"}
        data = _make_zip(files)
        uploaded = SimpleUploadedFile("model.zip", data, content_type="application/zip")

        mock_cm = mock_extractor.return_value.__enter__.return_value
        mock_cm.__getitem__.return_value = "mock/path/to/model.obj"
        mock_wavefront.return_value = object()

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
            "license": "0",
        }
        form = MetadataForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned = form.clean()
        self.assertEqual(cleaned["categories"], ["monuments", "tall"])
        self.assertEqual(cleaned["tags"], {"shape": "cube"})
        self.assertEqual(cleaned["translation"], [-1.0, -2.0, -3.0])

    def test_upload_file_metadata_form_missing(self):
        form = UploadFileMetadataForm(data={})
        self.assertFalse(form.is_valid())

    @patch("mainapp.forms.ModelExtractor")
    @patch("mainapp.forms.Wavefront")
    def test_upload_file_metadata_form_valid(self, mock_wavefront, mock_extractor):
        files = {"model.obj": "o Cube\nv 0 0 0"}
        data = _make_zip(files)
        uploaded = SimpleUploadedFile("model.zip", data, content_type="application/zip")
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
            "license": "0",
        }

        mock_cm = mock_extractor.return_value.__enter__.return_value
        mock_cm.__getitem__.return_value = "mock/path/to/model.obj"
        mock_wavefront.return_value = object()

        form = UploadFileMetadataForm(data=form_data, files={"model_file": uploaded})
        self.assertTrue(form.is_valid())
