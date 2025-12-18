import json
import os
from unittest import mock
from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
from django.utils.dateformat import format

from .mixins import BaseViewTestMixin as BaseTestMixin
from mainapp.models import Model


class NightlyDumpCommandTest(BaseTestMixin, TestCase):
    """Test cases for the nightly dump command."""

    @mock.patch("mainapp.management.commands.nightly.open", new_callable=mock.mock_open)
    @mock.patch("mainapp.management.commands.nightly.ZipFile")
    def test_handle_generates_info_json_and_zip(self, mock_zipfile, mock_open):
        mock_zip = mock.Mock()
        mock_zipfile.return_value = mock_zip

        call_command('nightly')

        mock_open.assert_called_with('info.json', 'w')
        mock_zipfile.assert_called_with('3dmr-nightly.zip', 'w')

        mock_open().write.assert_any_call('{\n')
        for model in Model.objects.filter(latest=True, is_hidden=False):
            mock_open().write.assert_any_call(
                f'''"{model.model_id}": {
                    json.dumps({
                        'author': model.author.profile.uid,
                        'revision': model.revision,
                        'title': model.title,
                        'description': model.description,
                        'upload_date': format(model.upload_date, 'U'),
                        'latitude': model.location.latitude,
                        'longitude': model.location.longitude,
                        'license': model.license,
                        'categories': model.categories.all().values_list('name', flat=True)[::1],
                        'tags': model.tags,
                        'rotation': model.rotation,
                        'scale': model.scale,
                        'translation': [
                            model.translation_x,
                            model.translation_y,
                            model.translation_z
                        ]
                    })}\n'''
            )
            mock_open().write.assert_any_call(',')
            model_path = '{}/{}/{}'.format(settings.MODEL_DIR, model.model_id, model.revision)
            mock_zip.write.assert_any_call(f"{model_path}.glb", f"models/{model.model_id}.glb")

        mock_open().write.assert_any_call('}')
        mock_zip.write.assert_any_call('info.json')

        mock_zip.close.assert_called_once()
        mock_open().close.assert_called_once()
