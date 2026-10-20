from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Post


User = get_user_model()


class BlogWorkflowTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author",
            password="StrongPass!234",
        )
        self.other_user = User.objects.create_user(
            username="another",
            password="StrongPass!234",
        )

    def test_signup_creates_account(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new_user",
                "password1": "A-strong-password!92",
                "password2": "A-strong-password!92",
            },
        )

        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="new_user").exists())

    def test_login_and_logout(self):
        self.assertTrue(
            self.client.login(username="author", password="StrongPass!234")
        )
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_signed_in_user_can_create_post_as_self(self):
        self.client.force_login(self.author)

        response = self.client.post(
            reverse("post_new"),
            {
                "title": "A first post",
                "body": "Post content",
            },
        )

        post = Post.objects.get(title="A first post")
        self.assertEqual(post.author, self.author)
        self.assertRedirects(response, reverse("post_detail", args=[post.pk]))

    def test_anonymous_user_is_redirected_from_post_creation(self):
        response = self.client.get(reverse("post_new"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('post_new')}",
        )

    def test_only_author_can_edit_or_delete_post(self):
        post = Post.objects.create(
            title="Owned post",
            body="Original body",
            author=self.author,
        )
        self.client.force_login(self.other_user)

        edit_response = self.client.get(reverse("post_edit", args=[post.pk]))
        delete_response = self.client.get(reverse("post_delete", args=[post.pk]))

        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_author_can_edit_and_delete_post(self):
        post = Post.objects.create(
            title="Owned post",
            body="Original body",
            author=self.author,
        )
        self.client.force_login(self.author)

        edit_response = self.client.post(
            reverse("post_edit", args=[post.pk]),
            {"title": "Updated post", "body": "Updated body"},
        )

        post.refresh_from_db()
        self.assertEqual(post.title, "Updated post")
        self.assertEqual(post.body, "Updated body")
        self.assertRedirects(
            edit_response,
            reverse("post_detail", args=[post.pk]),
        )

        delete_response = self.client.post(
            reverse("post_delete", args=[post.pk]),
        )

        self.assertRedirects(delete_response, reverse("home"))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_post_detail_and_absolute_url(self):
        post = Post.objects.create(
            title="Visible post",
            body="Post body",
            author=self.author,
        )

        response = self.client.get(post.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible post")
        self.assertEqual(
            post.get_absolute_url(),
            reverse("post_detail", args=[post.pk]),
        )
