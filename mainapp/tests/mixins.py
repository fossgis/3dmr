import os
import shutil
import tempfile

from django.conf import settings
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth

from mainapp.models import Category, LatestModel, Location, Model


@override_settings(
    MODEL_DIR=tempfile.mkdtemp(prefix="3dmr_")
)
class BaseViewTestMixin(TestCase):
    """
    A mixin to set up a base test environment with a user,
    admin user, and models. This mixin creates a user and an admin user, along with some models and categories.
    It also logs in the user for testing purposes.
    """

    def setUp(self) -> None:
        with open("mainapp/tests/test_files/test_model.glb", "rb") as f:
            self.model_file = f.read()

        self.user = User.objects.create_user(
            username="testuser", email="test@user.com", password="userpassword"
        )
        UserSocialAuth.objects.create(
            user=self.user,
            provider="test-provider",
            uid="1234567890",
            extra_data={"avatar": "http://example.com/avatar.jpg"},
        )
        self.user.save()
        self.login_user("user")

        self.admin_user = User.objects.create_user(
            username="testadmin", email="admin@user.com", password="adminpassword"
        )
        self.admin_user.profile.is_admin = True
        UserSocialAuth.objects.create(
            user=self.admin_user,
            provider="test-provider",
            uid="2234567890",
            extra_data={"avatar": "http://example.com/avatar.jpg"},
        )
        self.admin_user.save()

        self.model1 = Model.objects.create(
            model_id=1,
            revision=1,
            title="Model 1",
            author=self.user,
            is_hidden=False,
            location=Location.objects.create(latitude=48.8566, longitude=2.3522),
            tags={"color": "red", "size": "large"},
            license=0,
        )
        self.cat1 = Category.objects.create(name="category1")
        self.model1.categories.set([self.cat1])
        self.model1.save() # trigger post_save signal to sync LatestModel
        self.latest_model1 = LatestModel.objects.get(
            model_id=self.model1.model_id, revision=self.model1.revision
        )

        self.model2 = Model.objects.create(
            model_id=2,
            revision=1,
            title="Model 2",
            author=self.admin_user,
            is_hidden=True,
            location=Location.objects.create(latitude=2.3522, longitude=48.8566),
            tags={"color": "blue", "size": "small", "hidden": "true"},
            license=1,
        )
        self.cat2 = Category.objects.create(name="category2")
        self.model2.categories.set([self.cat2])
        self.model2.save()
        self.latest_model2 = LatestModel.objects.get(
            model_id=self.model2.model_id, revision=self.model2.revision
        )

        self.model3 = Model.objects.create(
            model_id=3,
            revision=1,
            title="Model 3",
            author=self.user,
            is_hidden=False,
            location=Location.objects.create(latitude=2.3522, longitude=48.8566),
            tags={"color": "blue", "size": "small"},
            license=1,
        )
        self.cat3 = Category.objects.create(name="category3")
        self.model3.categories.set([self.cat3])
        self.model3.save()
        self.latest_model3 = LatestModel.objects.get(
            model_id=self.model3.model_id, revision=self.model3.revision
        )

        self.model_dirs = []

        for model in [self.model1, self.model2, self.model3]:
            filepath = f"{settings.MODEL_DIR}/{model.model_id}/{model.revision}.glb"
            self.model_dirs.append(os.path.dirname(filepath))
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb+") as destination:
                destination.write(self.model_file)

    def tearDown(self) -> None:
        shutil.rmtree(settings.MODEL_DIR)

    def login_user(self, user_type="user"):
        """
        Helper method to log in a user based on the user_type.
        :param user_type: 'user' for regular user, 'admin' for admin user.
        """
        if user_type == "admin":
            self.client.force_login(self.admin_user)
        else:
            self.client.force_login(self.user)
