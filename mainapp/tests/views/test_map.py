from django.test import TestCase
from django.urls import reverse

from mainapp.tests.mixins import BaseViewTestMixin


class MapViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the map view.
    """

    def test_map_view(self):
        response = self.client.get(reverse("map"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/map.html")
        self.assertEqual(self.client.session.get("last_page"), reverse("map"))
