from django.test import TestCase
from django.urls import reverse

from mainapp.tests.mixins import BaseViewTestMixin


class DocsViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the docs view.
    """

    def test_docs_view(self):
        response = self.client.get(reverse("docs"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/docs.html")
        self.assertEqual(self.client.session.get("last_page"), reverse("docs"))
