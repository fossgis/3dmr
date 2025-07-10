from django.test import SimpleTestCase
from mainapp.utils import get_kv

class TestUtils(SimpleTestCase):
    def test_tag_with_single_equality(self):
        tag = "key=value"
        self.assertEqual(get_kv(tag), ["key", "value"])

    def test_tag_with_multiple_equality(self):
        tag_a = "key=value=value"
        tag_b = "key=value=val=v"

        self.assertEqual(get_kv(tag_a), ["key", "value=value"])
        self.assertEqual(get_kv(tag_b), ["key", "value=val=v"])
