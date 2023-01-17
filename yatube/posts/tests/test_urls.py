from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache
from django.urls import reverse
from http import HTTPStatus


from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст')
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание')
        cache.clear()

    def test_urls_anybody(self):
        """Доступ кучи страниц для неавторизованного пользователя"""
        adresses = (reverse('posts:index'),
                    reverse('posts:group_list',
                            kwargs={'slug': self.group.slug}),
                    reverse('posts:profile',
                            kwargs={'username': self.user.username}),
                    reverse('posts:post_detail',
                            kwargs={'post_id': self.post.id}))

        for adress in adresses:
            with self.subTest(adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_client(self):
        """Доступ create и posts для авторизованного пользователя"""
        pages = (reverse('posts:edit',
                         kwargs={'post_id': self.post.id}),
                 reverse('posts:create'))

        for page in pages:
            response = self.authorized_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        """Проверяем, запрос к несуществующей странице 404."""
        response = self.guest_client.get('/page_404/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
