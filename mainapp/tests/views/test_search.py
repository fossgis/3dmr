from django.test import TestCase
from django.urls import reverse

from mainapp.models import Location, Model
from mainapp.tests.mixins import BaseViewTestMixin


class SearchViewTest(BaseViewTestMixin, TestCase):
    """Tests for the search view in the mainapp."""

    def test_search_view_no_params_redirects_to_index(self):
        response = self.client.get(reverse("search"))
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)

    def test_search_by_title(self):
        response = self.client.get(reverse("search"), {"query": "Model 1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Model 1")
        self.assertNotContains(response, "Model 2")
        self.assertNotContains(response, "Model 3")
        self.assertEqual(len(response.context["models"]), 1)

    def test_search_by_tag_filter(self):
        response = self.client.get(reverse("search"), {"tag": "color=red"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Model 1")
        self.assertNotContains(response, "Model 2")
        self.assertNotContains(response, "Model 3")

    def test_invalid_tag_redirect(self):
        response = self.client.get(reverse("search"), {"tag": "invalidtag"})
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)

    def test_search_by_category(self):
        response = self.client.get(reverse("search"), {"category": "category1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Model 1")
        self.assertNotContains(response, "Model 2")

    def test_hidden_model_shown_to_admin(self):
        self.client.logout()
        self.client.login(username="testadmin", password="adminpassword")
        response = self.client.get(reverse("search"), {"query": "Model 2"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Model 2")

    def test_search_pagination(self):
        for i in range(10):
            m = Model.objects.create(
                model_id=100 + i,
                revision=1,
                title=f"Paginated {i}",
                author=self.user,
                is_hidden=False,
                location=Location.objects.create(latitude=0, longitude=0),
                tags={},
                license=0,
                latest=True,
            )

        page1 = self.client.get(reverse("search"), {"query": "Paginated", "page": 1})
        page2 = self.client.get(reverse("search"), {"query": "Paginated", "page": 2})

        self.assertEqual(page1.status_code, 200)
        self.assertEqual(page2.status_code, 200)
        self.assertEqual(len(page1.context["models"]), 6)
        self.assertEqual(len(page2.context["models"]), 4)

    def test_search_no_results(self):
        response = self.client.get(reverse("search"), {"query": "nohits"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No models were found with those parameters.")
        self.assertIsNone(response.context["models"])

    def test_url_params_context(self):
        response = self.client.get(
            reverse("search"), {"query": "Model", "category": "category1"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("query=Model", response.context["url_params"])
        self.assertIn("category=category1", response.context["url_params"])

    def test_last_page_updated(self):
        self.client.get(reverse("search"), {"query": "Model"})
        self.assertTrue(
            self.client.session.get("last_page").startswith(reverse("search"))
        )
