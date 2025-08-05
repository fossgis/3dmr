import json

from django.test import TestCase
from django.urls import reverse

from mainapp.models import Comment
from mainapp.tests.mixins import BaseViewTestMixin


class CommentViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the comment functionality in models.
    This includes both AJAX and non-AJAX comment submissions.
    """

    def test_addcomment_non_ajax(self):
        comment_text = "This is a valid comment."
        comment_data = {
            "comment": comment_text,
            "model_id": self.model1.model_id,
            "revision": self.model1.revision,
            "ajax": "false",
        }
        comment_count_before = Comment.objects.count()
        response = self.client.post(reverse("addcomment"), comment_data)
        self.assertEqual(Comment.objects.count(), comment_count_before + 1)
        new_comment = Comment.objects.latest("datetime")
        self.assertEqual(new_comment.comment, comment_text)
        self.assertEqual(new_comment.author, self.user)
        self.assertEqual(new_comment.model, self.model1)

    def test_addcomment_ajax(self):
        comment_text = "A valid AJAX comment."
        comment_data = {
            "comment": comment_text,
            "model_id": self.model1.model_id,
            "revision": self.model1.revision,
            "ajax": "true",
        }
        comment_count_before = Comment.objects.count()
        response = self.client.post(reverse("addcomment"), comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), comment_count_before + 1)

        response_data = json.loads(response.content)
        self.assertEqual(response_data["success"], "yes")
        self.assertEqual(response_data["author"], self.user.profile.display_name)
        self.assertIn(comment_text, response_data["comment"])
        self.assertIsNotNone(response_data["datetime"])

    def test_addcomment_non_existent_model(self):
        comment_data = {
            "comment": "A comment",
            "model_id": 99999,  # Non-existent
            "revision": 1,
            "ajax": "false",
        }
        response = self.client.post(reverse("addcomment"), comment_data)
        self.assertEqual(response.status_code, 404)

    def test_addcomment_empty_comment(self):
        comment_data = {
            "comment": " ",
            "model_id": self.model1.model_id,
            "revision": self.model1.revision,
            "ajax": "false",
        }
        response = self.client.post(reverse("addcomment"), comment_data)
        self.assertRedirects(response, reverse("index"))


class HideCommentViewTest(BaseViewTestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.comment = Comment.objects.create(
            model=self.model3,
            author=self.user,
            comment="Hidable comment",
            is_hidden=False,
        )

    def test_hide_comment_view_non_admin(self):
        self.login_user()
        response = self.client.post(
            reverse("hide_comment"),
            {
                "model_id": self.model3.model_id,
                "revision": self.model3.revision,
                "comment_id": self.comment.pk,
                "type": "hide",
            },
        )
        self.assertRedirects(response, reverse("index"))

    def test_hide_comment_action(self):
        self.login_user(user_type="admin")
        self.assertFalse(self.comment.is_hidden)
        response = self.client.post(
            reverse("hide_comment"),
            {
                "model_id": self.model3.model_id,
                "revision": self.model3.revision,
                "comment_id": self.comment.pk,
                "type": "hide",
            },
        )
        self.assertRedirects(
            response,
            reverse("model", args=[self.model3.model_id, self.model3.revision]),
        )
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_hidden)

    def test_unhide_comment_action(self):
        self.login_user(user_type="admin")
        self.comment.is_hidden = True
        self.comment.save()
        self.assertTrue(self.comment.is_hidden)

        response = self.client.post(
            reverse("hide_comment"),
            {
                "model_id": self.model3.model_id,
                "revision": self.model3.revision,
                "comment_id": self.comment.pk,
                "type": "unhide",
            },
        )
        self.assertRedirects(
            response,
            reverse("model", args=[self.model3.model_id, self.model3.revision]),
        )
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_hidden)

    def test_hide_comment_no_comment_id(self):
        self.login_user(user_type="admin")
        response = self.client.post(
            reverse("hide_comment"),
            {
                "model_id": self.model3.model_id,
                "revision": self.model3.revision,
                "type": "hide",
            },
        )
        self.assertRedirects(
            response,
            reverse("model", args=[self.model3.model_id, self.model3.revision]),
        )
