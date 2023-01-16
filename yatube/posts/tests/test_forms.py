from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from posts.models import Post, Group

User = get_user_model()


class PostFormTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test-group',
                                          description='Описание')

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        self.post = Post.objects.create(
            author=self.user,
            text="Тестовый текст",
        )
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст',
                     'group': self.group.id}

        response = self.authorized_client.post(
            reverse("posts:edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response, reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(Post.objects.count(),
                         posts_count)
        self.assertTrue(Post.objects.filter(
                        text=form_data['text'],
                        group=self.group.id,
                        author=self.user
                        ).exists()
                        )

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        self.post = Post.objects.create(
            author=self.user,
            text="Тестовый текст",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        posts_count = Post.objects.count()
        form_data = {"text": "Изменяем текст", "group": self.group.id}

        response = self.authorized_client.post(
            reverse("posts:edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response, reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text=form_data['text'],).exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)
