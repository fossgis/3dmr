from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from social_django.models import UserSocialAuth

from mainapp.models import Ban
from mainapp.tests.mixins import BaseViewTestMixin


class BanTest(BaseViewTestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.user_to_be_banned = User.objects.create_user("bannableuser", "password")
        UserSocialAuth.objects.create(
            user=self.user_to_be_banned,
            provider="test-provider",
            uid="3234567890",
            extra_data={"avatar": "http://example.com/avatar.jpg"},
        )
        self.user_to_be_banned.save()

    def test_ban_view_non_admin(self):
        self.login_user()
        response = self.client.post(
            reverse("ban"),
            {
                "uid": self.user_to_be_banned.profile.uid,
                "type": "ban",
                "reason": "test",
            },
        )
        self.assertRedirects(response, reverse("index"))

    def test_ban_view_no_uid(self):
        self.login_user(user_type="admin")
        response = self.client.post(reverse("ban"), {"type": "ban", "reason": "test"})
        self.assertRedirects(response, reverse("index"))

    def test_ban_user_success(self):
        self.login_user(user_type="admin")
        self.assertFalse(self.user_to_be_banned.profile.is_banned)

        response = self.client.post(
            reverse("ban"),
            {
                "uid": self.user_to_be_banned.profile.uid,
                "type": "ban",
                "reason": "Test ban reason",
            },
        )
        self.assertRedirects(
            response, reverse("user", args=[self.user_to_be_banned.profile.uid])
        )
        self.user_to_be_banned.refresh_from_db()
        self.assertTrue(Ban.objects.filter(banned_user=self.user_to_be_banned).exists())

    def test_ban_user_no_reason(self):
        self.login_user(user_type="admin")
        response = self.client.post(
            reverse("ban"),
            {"uid": self.user_to_be_banned.profile.uid, "type": "ban", "reason": ""},
        )
        self.assertRedirects(
            response, reverse("user", args=[self.user_to_be_banned.profile.uid])
        )
        self.assertFalse(
            Ban.objects.filter(banned_user=self.user_to_be_banned).exists()
        )

    def test_ban_user_already_banned(self):
        self.login_user(user_type="admin")
        Ban.objects.create(
            admin=self.admin_user,
            banned_user=self.user_to_be_banned,
            reason="Pre-existing ban",
        )

        response = self.client.post(
            reverse("ban"),
            {
                "uid": self.user_to_be_banned.profile.uid,
                "type": "ban",
                "reason": "Another reason",
            },
        )
        self.assertRedirects(
            response, reverse("user", args=[self.user_to_be_banned.profile.uid])
        )
        self.assertEqual(
            Ban.objects.filter(banned_user=self.user_to_be_banned).count(), 1
        )

    def test_unban_user_success(self):
        self.login_user(user_type="admin")
        Ban.objects.create(
            admin=self.admin_user,
            banned_user=self.user_to_be_banned,
            reason="To be unbanned",
        )
        self.assertTrue(Ban.objects.filter(banned_user=self.user_to_be_banned).exists())

        response = self.client.post(
            reverse("ban"),
            {"uid": self.user_to_be_banned.profile.uid, "type": "unban"},
        )
        self.assertRedirects(
            response, reverse("user", args=[self.user_to_be_banned.profile.uid])
        )
        self.user_to_be_banned.profile.refresh_from_db()
        self.assertFalse(self.user_to_be_banned.profile.is_banned)

    def test_unban_user_not_banned(self):
        self.login_user(user_type="admin")
        Ban.objects.filter(banned_user=self.user_to_be_banned).delete()

        response = self.client.post(
            reverse("ban"),
            {"uid": self.user_to_be_banned.profile.uid, "type": "unban"},
        )
        self.assertRedirects(
            response, reverse("user", args=[self.user_to_be_banned.profile.uid])
        )
