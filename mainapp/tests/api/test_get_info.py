from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware

from mainapp.models import Model
from mainapp.tests.mixins import BaseViewTestMixin


class GetInfoAPIViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the get_info API view in the mainapp.
    """

    def setUp(self):
        super().setUp()
        self.hidden_model = self.model2

    def test_get_info_success(self):
        response = self.client.get(reverse("get_info", args=[self.model1.model_id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["id"], self.model1.model_id)
        self.assertEqual(data["revision"], self.model1.revision)
        self.assertEqual(data["title"], self.model1.title)
        self.assertEqual(data["lat"], self.model1.location.latitude)
        self.assertEqual(data["lon"], self.model1.location.longitude)
        self.assertEqual(data["license"], self.model1.license)
        self.assertEqual(data["desc"], self.model1.description)
        self.assertEqual(data["author"], self.model1.author.profile.uid)
        self.assertIsInstance(data["author"], str)
        self.assertEqual(data["rotation"], self.model1.rotation)
        self.assertEqual(data["scale"], self.model1.scale)
        self.assertEqual(
            data["translation"],
            [
                self.model1.translation_x,
                self.model1.translation_y,
                self.model1.translation_z,
            ],
        )
        self.assertEqual(data["tags"], self.model1.tags)
        self.assertIn(self.cat1.name, data["categories"])

    def test_get_info_hidden_model_non_admin(self):
        response = self.client.get(
            reverse("get_info", args=[self.hidden_model.model_id])
        )
        self.assertEqual(response.status_code, 404)

    def test_get_info_hidden_model_admin(self):
        self.login_user(user_type="admin")
        response = self.client.get(
            reverse("get_info", args=[self.hidden_model.model_id])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.hidden_model.model_id)

    def test_get_info_not_found(self):
        response = self.client.get(reverse("get_info", args=[9999]))
        self.assertEqual(response.status_code, 404)
