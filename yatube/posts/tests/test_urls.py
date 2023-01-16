from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache
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
        adresses = ('/',
                    f'/group/{self.group.slug}/',
                    f'/profile/{self.user.username}/',
                    f'/posts/{self.post.id}/')

        for adress in adresses:
            with self.subTest(adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_client(self):
        """Доступ create и posts для авторизованного пользователя"""
        pages = ('/create/',
                 f'/posts/{self.post.id}/edit/')

        for page in pages:
            response = self.authorized_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """Проверка доступности страниц и шаблонов """
        templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html'}

        for adress, template in templates.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        """Проверяем, запрос к несуществующей странице 404."""
        response = self.guest_client.get('/page_404/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
