import os
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from mainapp.models import Model
from mainapp.tests.mixins import BaseViewTestMixin


class GetModelAPIViewTest(BaseViewTestMixin, TestCase):
    """
    Tests for the get_model API view in the mainapp.
    """

    def test_get_model_success_latest_revision(self):
        response = self.client.get(reverse("get_model", args=[self.model1.model_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "model/gltf-binary")
        self.assertEqual(
            response["Content-Disposition"],
            f"attachment; filename={self.model1.model_id}_{self.model1.revision}.glb",
        )

    def test_get_model_success_specific_revision(self):
        for i in range(2):
            self.model1 = Model.objects.create(
                model_id=self.model1.model_id,
                revision=self.model1.revision+1,
                title=f"Revised model",
                author=self.user,
                is_hidden=False,
                license=1,
                latest=True,
            )
            filepath = f"{settings.MODEL_DIR}/{self.model1.model_id}/{self.model1.revision}.glb"
            self.model_dirs.append(os.path.dirname(filepath))
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb+") as destination:
                destination.write(self.model_file)
        # now we have a total of 3 revisions of model1
        response = self.client.get(reverse("get_model", args=[self.model1.model_id, 2]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"], f"attachment; filename={self.model1.model_id}_{2}.glb")

    def test_get_model_hidden_non_admin(self):
        response = self.client.get(reverse("get_model", args=[self.model2.model_id]))
        self.assertEqual(response.status_code, 404)
