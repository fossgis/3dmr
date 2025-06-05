from django.test import TestCase
from django.urls import reverse

from mainapp.tests.mixins import BaseViewTestMixin


class GetModelAPIViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the get_model API view in the mainapp.
    """

    def test_get_model_success_latest_revision(self):
        response = self.client.get(reverse("get_model", args=[self.model1.model_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertEqual(
            response["Content-Disposition"],
            f"attachment; filename={self.model1.revision}.zip",
        )

    def test_get_model_success_specific_revision(self):
        response = self.client.get(reverse("get_model", args=[self.model1.model_id, 1]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"], "attachment; filename=1.zip")

    def test_get_model_hidden_non_admin(self):
        response = self.client.get(reverse("get_model", args=[self.model2.model_id]))
        self.assertEqual(response.status_code, 404)
