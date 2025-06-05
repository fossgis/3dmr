from django.test import TestCase
from django.urls import reverse

from mainapp.tests.mixins import BaseViewTestMixin


class GetFileAPIViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the get file and get file list API view in the mainapp.
    """

    def test_get_filelist_success(self):
        response = self.client.get(reverse("get_list", args=[self.model3.model_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        content = response.content.decode()
        self.assertIn(".mtl", content)
        self.assertIn(".obj", content)
        self.assertIn(".jpg", content)

    def test_get_file_success(self):
        response = self.client.get(
            reverse("get_file", args=[self.model3.model_id, "3Ddata.obj"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"], "attachment; filename=3Ddata.obj"
        )

    def test_get_file_non_existent_in_zip(self):
        with self.assertRaises(KeyError):
            self.client.get(
                reverse(
                    "get_file", args=[self.model3.model_id, "nonexistentfile.extension"]
                )
            )
