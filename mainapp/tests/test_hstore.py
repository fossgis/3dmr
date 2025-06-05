from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase

from mainapp.models import Model

User = get_user_model()


class HStoreExtensionTest(TestCase):
    """
    Tests for the HStore extension in the database.
    """

    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser", password="userpassword"
        )
        self.model = Model.objects.create(
            model_id=1,
            revision=1,
            title="Test Model",
            author=self.user,
            tags={"color": "red", "size": "large"},
            license=1,
        )

    def test_hstore_extension_is_installed(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'hstore';")
            result = cursor.fetchone()

        self.assertIsNotNone(
            result, "HStore extension is not installed in the database."
        )

    def test_hstore_field_behaves_like_dict(self):
        self.assertEqual(type(self.model.tags), dict)
