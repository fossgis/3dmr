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

    def test_lookup_tag_invalid_format_500(self):
        with self.assertRaises(ValueError):
            self.client.get(reverse("lookup_tag", args=["invalidtag", 1]))

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
            reverse("lookup_author", args=[self.user.username, 1])
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


class LookupTitleAPIViewTests(BaseViewTestMixin, TestCase):

    def test_search_title_success(self):
        response = self.client.get(reverse("search_title", args=[self.model1.title, 1]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(self.model1.model_id, data)
