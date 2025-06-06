from django.test import TestCase
from django.urls import reverse

from mainapp.tests.mixins import BaseViewTestMixin


class DownloadsViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the downloads view.
    """

    def test_downloads_view(self):
        response = self.client.get(reverse("downloads"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/downloads.html")
        self.assertEqual(self.client.session.get("last_page"), reverse("downloads"))
