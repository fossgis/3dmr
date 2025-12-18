import json
from django.test import TestCase
from django.urls import reverse

from mainapp.tests.mixins import BaseViewTestMixin


class LookupTagAPIViewTests(BaseViewTestMixin, TestCase):
    """
    Tests for the lookup_tag API view in the mainapp.
    """

    def test_lookup_tag_success(self):
        response = self.client.get(reverse("lookup_tag", args=["color=red"]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(self.model1.model_id, data)

    def test_lookup_tag_invalid_format_400(self):
        response = self.client.get(reverse("lookup_tag", args=["invalidtag"]))
        self.assertEqual(response.status_code, 400)

    def test_lookup_tag_hidden_admin(self):
        self.login_user(user_type="admin")
        response = self.client.get(reverse("lookup_tag", args=["hidden=true"]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(self.model2.model_id, data)

    def test_lookup_tag_hidden_non_admin(self):
        response = self.client.get(reverse("lookup_tag", args=["hidden=true", 1]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 0)


class LookupCategoryAPIViewTests(BaseViewTestMixin, TestCase):

    def test_lookup_category_success(self):
        response = self.client.get(reverse("lookup_category", args=[self.cat1.name, 1]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(self.model1.model_id, data)


class LookupAuthorAPIViewTests(BaseViewTestMixin, TestCase):

    def test_lookup_author_success(self):
        response = self.client.get(
            reverse("lookup_author", args=[self.user.profile.uid, 1])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(self.model1.model_id, data)
        self.assertIn(self.model3.model_id, data)


class LookupRangeAPIViewTests(BaseViewTestMixin, TestCase):

    def test_search_range_success(self):
        response = self.client.get(
            reverse(
                "lookup_range",
                args=[
                    self.model1.location.latitude,
                    self.model1.location.longitude,
                    1000,
                    1,
                ],
            )
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(self.model1.model_id, data)

    def test_search_range_invalid_params_400(self):
        # Invalid latitude
        response = self.client.get(
            f"/api/search/invalid/10.0/1000/1"
        )
        self.assertEqual(response.status_code, 400)

        # Invalid longitude
        response = self.client.get(
            f"/api/search/10.0/invalid/1000/1"
        )
        self.assertEqual(response.status_code, 400)

        # Invalid distance
        response = self.client.get(
            f"/api/search/10.0/10.0/invalid/1"
        )
        self.assertEqual(response.status_code, 400)


class LookupTitleAPIViewTests(BaseViewTestMixin, TestCase):

    def test_search_title_success(self):
        response = self.client.get(reverse("search_title", args=[self.model1.title, 1]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(self.model1.model_id, data)


class SearchFullAPIViewTests(BaseViewTestMixin, TestCase):
    
    def test_search_full_invalid_json_400(self):
        response = self.client.post(
            reverse("search_full"),
            data="invalid json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_search_full_valid_json_success(self):
        data = {
            "title": self.model1.title
        }
        response = self.client.post(
            reverse("search_full"),
            data=data,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.model1.model_id, response.json())
