from django.test import TestCase
from django.urls import reverse

from mainapp.tests.mixins import BaseViewTestMixin


class IndexViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the index view of the mainapp.
    This includes visibility of models based on user type (anonymous, authenticated, admin).
    """

    def test_index_view_get_anonymous(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/index.html")

        self.assertContains(response, "Model 1")
        self.assertContains(response, "Model 3")
        self.assertNotContains(response, "Model 2")  # hidden model

        models = response.context["models"]
        self.assertTrue(all(not m.is_hidden for m in models))
        self.assertIn(self.latest_model1, models)
        self.assertIn(self.latest_model3, models)
        self.assertNotIn(self.latest_model2, models)

    def test_index_view_get_authenticated_user(self):
        self.login_user(user_type="user")  # Assuming this uses self.user
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/index.html")

        self.assertContains(response, "Model 1")
        self.assertContains(response, "Model 3")
        self.assertNotContains(response, "Model 2")

        models = response.context["models"]
        self.assertTrue(all(not m.is_hidden for m in models))
        self.assertIn(self.latest_model1, models)
        self.assertIn(self.latest_model3, models)
        self.assertNotIn(self.latest_model2, models)

    def test_index_view_get_admin_user(self):
        self.login_user(user_type="admin")  # Assuming this uses self.admin_user
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/index.html")

        self.assertContains(response, "Model 1")
        self.assertContains(response, "Model 2")  # now visible to admin
        self.assertContains(response, "Model 3")

        models = response.context["models"]
        self.assertIn(self.latest_model1, models)
        self.assertIn(self.latest_model2, models)
        self.assertIn(self.latest_model3, models)

    def test_update_last_page_called_on_index(self):
        self.client.get(reverse("index"))
        self.assertEqual(self.client.session.get("last_page"), reverse("index"))
