import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from mainapp.forms import UploadFileForm, UploadFileMetadataForm
from mainapp.models import Comment, Model
from mainapp.tests.mixins import BaseViewTestMixin
from mainapp.utils import LICENSES_DISPLAY


class UploadModelViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the upload view, including both GET and POST requests.
    This includes unauthenticated access, authenticated access, and form validation.
    """

    def test_upload_get_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("upload"))
        self.assertRedirects(response, reverse("index"))

    def test_upload_get_authenticated(self):
        self.login_user()
        response = self.client.get(reverse("upload"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/upload.html")
        self.assertIsInstance(response.context["form"], UploadFileMetadataForm)

    def test_upload_get_with_post_data_in_session(self):
        self.login_user()
        session = self.client.session
        session["post_data"] = {
            "title": "Session Title",
            "description": "Session Desc",
            "license": "0",
        }
        session.save()

        response = self.client.get(reverse("upload"))
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form["title"].value(), "Session Title")
        self.assertIn("You must reupload your file.", form.errors.get("model_file", []))
        self.assertNotIn("post_data", self.client.session)

    def test_upload_post_unauthenticated_stores_data_and_shows_error(self):
        self.client.logout()
        upload_data = {
            "title": "Attempted Upload",
            "description": "Desc",
            "license": "0",
        }
        dummy_file = SimpleUploadedFile(
            "unauth_test.glb", b"content", "model/gltf-binary"
        )
        upload_data["model_file"] = dummy_file

        response = self.client.post(reverse("upload"), data=upload_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "You must be logged in to use this feature."
        )  # Message
        self.assertIn("post_data", self.client.session)
        self.assertEqual(self.client.session["post_data"]["title"], "Attempted Upload")

    @patch("mainapp.views.database.upload")
    def test_upload_post_authenticated_success(self, mock_db_upload):
        mock_model = Model(model_id=1, revision=1)
        mock_db_upload.return_value = mock_model
        self.login_user()

        dummy_file = SimpleUploadedFile(
            name="test_model.glb",
            content=self.model_file,
            content_type="model/gltf-binary",
        )
        upload_data = {
            "title": "My New Model",
            "description": "Awesome model.",
            "latitude": "1.0",
            "longitude": "1.0",
            "categories": "cat1,cat2",
            "tags": "tag1=val1",
            "translation": "0 0 0",
            "rotation": "0",
            "scale": "1",
            "license": "0",
            "model_file": dummy_file,
        }
        response = self.client.post(reverse("upload"), data=upload_data)
        self.assertRedirects(
            response, reverse("model", args=[mock_model.model_id, mock_model.revision])
        )
        mock_db_upload.assert_called_once()
        called_data = mock_db_upload.call_args[0][1]
        self.assertEqual(called_data["title"], "My New Model")
        self.assertEqual(called_data["author"], self.user)

    @patch("mainapp.views.database.upload")
    def test_upload_post_corrupt_model_error(self, mock_db_upload):
        self.login_user()

        dummy_file = SimpleUploadedFile(
            "fail_model.glb", b"corrupt content", "model/gltf-binary"
        )
        upload_data = {
            "title": "Fail Model",
            "description": "It will fail.",
            "license": "0",
            "model_file": dummy_file,
        }

        response = self.client.post(reverse("upload"), data=upload_data)
        self.assertIn("Recheck the form for errors.", response.content.decode())
        # Check for server error message

    def test_upload_post_invalid_form_data(self):
        self.login_user()
        upload_data = {"title": "", "license": "0"}  # Missing description, file etc.
        response = self.client.post(reverse("upload"), data=upload_data)
        self.assertEqual(response.status_code, 200)  # Stays on page
        form = response.context["form"]
        self.assertFormError(form, "title", "This field is required.")
        self.assertFormError(form, "model_file", "This field is required.")


class ModelViewTests(BaseViewTestMixin, TestCase):
    """
    Tests for the model detail view, including visibility of comments and handling of revisions.
    """

    def setUp(self):
        super().setUp()

        self.visible_model = self.model1
        self.hidden_model = self.model2

        self.comment1 = Comment.objects.create(
            model=self.visible_model,
            author=self.user,
            comment="Visible comment",
            rendered_comment="Visible comment",
            is_hidden=False,
        )
        self.comment2 = Comment.objects.create(
            model=self.visible_model,
            author=self.admin_user,
            comment="Hidden comment",
            rendered_comment="Hidden comment",
            is_hidden=True,
        )

    def test_model_view_latest_revision(self):
        response = self.client.get(reverse("model", args=[self.visible_model.model_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/model.html")
        self.assertEqual(response.context["model"].pk, self.visible_model.pk)
        self.assertContains(response, self.visible_model.title)
        self.assertContains(response, self.comment1.comment)
        self.assertNotContains(response, self.comment2.comment)
        self.assertEqual(
            response.context["license"], LICENSES_DISPLAY[self.visible_model.license]
        )
        self.assertEqual(
            self.client.session.get("last_page"),
            reverse("model", args=[self.visible_model.model_id]),
        )

    def test_model_view_specific_revision(self):
        response = self.client.get(
            reverse(
                "model", args=[self.visible_model.model_id, self.visible_model.revision]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["model"].pk, self.visible_model.pk)
        self.assertContains(response, self.visible_model.title)

    def test_model_view_hidden_model_non_admin(self):
        response = self.client.get(reverse("model", args=[self.hidden_model.model_id]))
        self.assertEqual(response.status_code, 404)

    def test_model_view_hidden_model_admin(self):
        self.login_user(user_type="admin")
        response = self.client.get(reverse("model", args=[self.hidden_model.model_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hidden_model.title)

    def test_model_view_comments_admin(self):
        self.login_user(user_type="admin")
        response = self.client.get(reverse("model", args=[self.visible_model.model_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.comment1.comment)
        self.assertContains(response, self.comment2.comment)

    def test_model_view_non_existent_model(self):
        response = self.client.get(reverse("model", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_model_view_non_existent_revision(self):
        response = self.client.get(
            reverse("model", args=[self.visible_model.model_id, 999])
        )
        self.assertEqual(response.status_code, 404)

    def test_model_view_old_comment_in_session(self):
        session = self.client.session
        session["comment"] = "Previous unfinished comment"
        session.save()
        response = self.client.get(reverse("model", args=[self.visible_model.model_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["old_comment"], "Previous unfinished comment")


class EditModelViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the edit views of models in the mainapp.
    This includes both GET and POST requests, form validation, and database interactions.
    """

    def test_edit_view_get(self):
        response = self.client.get(
            reverse("edit", args=[self.model3.model_id, self.model3.revision])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/edit.html")
        form = response.context["form"]
        self.assertEqual(form.initial["title"], self.model3.title)
        self.assertEqual(form.initial["description"], self.model3.description)

    @patch("mainapp.views.database.edit")
    def test_edit_view_post(self, mock_db_edit):
        mock_db_edit.return_value = True

        edit_data = {
            "title": "Updated Title",
            "description": "Updated Description",
            "latitude": "12.34",
            "longitude": "56.78",
            "categories": "NewCat, AnotherCat",
            "tags": "new_tag=val, another_tag=val2",
            "translation": "1.0 2.0 3.0",
            "rotation": "90",
            "scale": "1.5",
            "license": "1",
        }
        response = self.client.post(
            reverse("edit", args=[self.model3.model_id, self.model3.revision]),
            data=edit_data,
        )
        self.assertRedirects(
            response,
            reverse("model", args=[self.model3.model_id, self.model3.revision]),
        )
        mock_db_edit.assert_called_once()
        called_args = mock_db_edit.call_args[0][0]
        self.assertEqual(called_args["title"], "Updated Title")
        self.assertEqual(called_args["license"], "1")

    @patch("mainapp.views.database.edit")
    def test_edit_view_post_db_error(self, mock_db_edit):
        mock_db_edit.return_value = False

        edit_data = {
            "title": "Updated Title",
            "description": "Updated Desc",
            "license": "0",
        }
        response = self.client.post(
            reverse("edit", args=[self.model3.model_id, self.model3.revision]),
            data=edit_data,
        )

        self.assertRedirects(
            response, reverse("edit", args=[self.model3.model_id, self.model3.revision])
        )

    def test_edit_view_post_invalid_form(self):
        edit_data = {"title": "", "description": "Valid Desc", "license": "0"}
        response = self.client.post(
            reverse("edit", args=[self.model3.model_id, self.model3.revision]),
            data=edit_data,
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFormError(form, "title", "This field is required.")


class ReviseModelViewTest(BaseViewTestMixin, TestCase):

    def test_revise_view_get(self):
        response = self.client.get(
            reverse("revise", args=[self.latest_model3.model_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mainapp/revise.html")
        self.assertIsInstance(response.context["form"], UploadFileForm)
        self.assertEqual(response.context["model"].pk, self.latest_model3.pk)

    @patch("mainapp.views.database.upload")
    def test_revise_view_post_success(self, mock_db_upload):
        mock_new_revision_model = Model(
            model_id=self.latest_model3.model_id, revision=2, author=self.user
        )
        mock_db_upload.return_value = mock_new_revision_model

        dummy_file = SimpleUploadedFile(
            "test_revision.glb", self.model_file, content_type="model/gltf-binary"
        )

        response = self.client.post(
            reverse("revise", args=[self.latest_model3.model_id]),
            data={"model_file": dummy_file},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "model",
                args=[
                    mock_new_revision_model.model_id,
                    mock_new_revision_model.revision,
                ],
            ),
        )
        mock_db_upload.assert_called_once()
        call_args = mock_db_upload.call_args[0]
        self.assertEqual(int(call_args[1]["model_id"]), self.latest_model3.model_id)
        self.assertTrue(call_args[1]["revision"])
        self.assertEqual(call_args[1]["author"], self.user)

    @patch("mainapp.views.database.upload")
    def test_revise_view_post_db_error(self, mock_db_upload):
        mock_db_upload.return_value = None
        dummy_file = SimpleUploadedFile(
            "test_rev_fail.glb", self.model_file, content_type="model/gltf-binary"
        )

        response = self.client.post(
            reverse("revise", args=[self.latest_model3.model_id]),
            data={"model_file": dummy_file},
        )
        self.assertRedirects(
            response, reverse("revise", args=[self.latest_model3.model_id])
        )

    def test_revise_view_post_no_file(self):
        response = self.client.post(
            reverse("revise", args=[self.latest_model3.model_id]), data={}
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFormError(form, "model_file", "This field is required.")

    # def test_revise_non_existent_model_id(self):
    #     response = self.client.get(reverse('revise', args=[99999999]))
    #     self.assertEqual(response.status_code, 404)


class HideModelViewTest(BaseViewTestMixin, TestCase):

    def test_hide_model_view_non_admin(self):
        self.login_user()
        response = self.client.post(
            reverse("hide_model"),
            {
                "model_id": self.model3.model_id,
                "revision": self.model3.revision,
                "type": "hide",
            },
        )
        self.assertRedirects(response, reverse("index"))

    def test_hide_model_action(self):
        self.login_user(user_type="admin")
        self.assertFalse(self.model3.is_hidden)
        response = self.client.post(
            reverse("hide_model"),
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
        self.model3.refresh_from_db()
        self.assertTrue(self.model3.is_hidden)

    def test_unhide_model_action(self):
        self.login_user(user_type="admin")
        self.model3.is_hidden = True
        self.model3.save()
        self.assertTrue(self.model3.is_hidden)

        response = self.client.post(
            reverse("hide_model"),
            {
                "model_id": self.model3.model_id,
                "revision": self.model3.revision,
                "type": "unhide",
            },
        )
        self.assertRedirects(
            response,
            reverse("model", args=[self.model3.model_id, self.model3.revision]),
        )
        self.model3.refresh_from_db()
        self.assertFalse(self.model3.is_hidden)

    def test_hide_model_invalid_action(self):
        self.login_user(user_type="admin")
        response = self.client.post(
            reverse("hide_model"),
            {
                "model_id": self.model3.model_id,
                "revision": self.model3.revision,
                "type": "invalidaction",
            },
        )
        self.assertRedirects(
            response,
            reverse("model", args=[self.model3.model_id, self.model3.revision]),
        )
