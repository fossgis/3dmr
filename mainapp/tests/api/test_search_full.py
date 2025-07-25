import json

from django.test import TestCase
from django.urls import reverse

from mainapp.api import RESULTS_PER_API_CALL
from mainapp.models import Model
from mainapp.tests.mixins import BaseViewTestMixin


class SearchFullAPIViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the full search api view in the mainapp.
    """

    def test_search_full_no_filters(self):
        payload = {}
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertIn(self.model1.model_id, results)
        self.assertNotIn(self.model2.model_id, results)

    def test_search_full_author_filter(self):
        payload = {"author": "testuser", "format": ["id", "title"]}
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertEqual(len(results), 2)
        self.assertSetEqual({result[1] for result in results}, {"Model 1", "Model 3"})

    def test_search_full_title_filter(self):
        payload = {"title": "Model", "format": ["id", "title"]}
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertEqual(len(results), 2)
        self.assertSetEqual({result[1] for result in results}, {"Model 1", "Model 3"})

    def test_search_full_tags_filter(self):
        payload = {"tags": {"color": "red"}, "format": ["id", "title"]}
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "Model 1")

    def test_search_full_categories_filter(self):
        payload = {"categories": ["category1"], "format": ["id", "title"]}
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "Model 1")

    def test_search_full_location_filter(self):
        payload = {
            "lat": 48.8566,
            "lon": 2.3522,
            "range": 1000,
            "format": ["id", "title"],
        }
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "Model 1")

    def test_search_full_pagination(self):
        for i in range(RESULTS_PER_API_CALL + 5):
            model = Model.objects.create(
                model_id=100 + i,
                revision=1,
                title=f"Paged API Model {i}",
                author=self.user,
                is_hidden=False,
                license=1,
                latest=True,
            )

        payload_page1 = {"author": self.user.profile.uid, "page": 1}
        response_page1 = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload_page1),
            content_type="application/json",
        )
        self.assertEqual(response_page1.status_code, 200)
        data_page1 = response_page1.json()
        self.assertEqual(len(data_page1), RESULTS_PER_API_CALL)

        payload_page2 = {"author": self.user.profile.display_name, "page": 2}
        response_page2 = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload_page2),
            content_type="application/json",
        )
        self.assertEqual(response_page2.status_code, 200)
        data_page2 = response_page2.json()
        self.assertTrue(0 < len(data_page2) <= RESULTS_PER_API_CALL)

    def test_search_full_empty_page_result(self):
        payload = {"author": self.user.profile.display_name, "page": 999}
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 0)

    def test_search_full_invalid_format(self):
        payload = {"format": ["invalid"]}
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Invalid format specifier")

    def test_search_full_admin_access(self):
        self.login_user("admin")
        payload = {"format": ["id", "title"]}
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertIn(self.model1.model_id, [r[0] for r in results])
        self.assertIn(self.model2.model_id, [r[0] for r in results])

    def test_search_full_with_format_no_location(self):
        self.model_no_loc = Model.objects.create(
            model_id=99,
            revision=1,
            title="Model No Loc",
            author=self.user,
            is_hidden=False,
            location=None,
            license=1,
            latest=True,
        )

        payload = {
            "title": self.model_no_loc.title,
            "format": ["id", "title", "latitude", "longitude"],
        }
        response = self.client.post(
            reverse("search_full"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) > 0)
        first_result = data[0]
        self.assertEqual(first_result[0], self.model_no_loc.model_id)
        self.assertEqual(first_result[1], self.model_no_loc.title)
        self.assertIsNone(first_result[2])
        self.assertIsNone(first_result[3])
