from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django import forms

import tempfile
import shutil

from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует правильные шаблоны."""
        templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            f'{self.group.slug}'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            f'{self.user.username}'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_detail.html',
            reverse('posts:create'): 'posts/create_post.html',
            reverse('posts:edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html'}

        for adress, template in templates.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))

        self.check_post_info(response.context['page_obj'][0])

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})
        )

        self.assertEqual(response.context['group'], self.group)
        self.check_post_info(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse('posts:profile', kwargs={
                        'username': self.user.username})))

        self.assertEqual(response.context['author'], self.user)
        self.check_post_info(response.context['page_obj'][0])

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

        post_text_0 = {response.context['post'].text: 'Тестовый пост',
                       response.context['post'].group: self.group,
                       response.context['post'].author: self.user.username}

        for field, expected in post_text_0.items():
            self.assertEqual(post_text_0[field], expected)

    def test_forms_show_correct(self):
        """
        Шаблон создания и редактирования поста
        create_post  сформирован с правильным контекстом.
        """
        url_filds = {
            reverse('posts:create'),
            reverse('posts:edit', kwargs={'post_id': self.post.id, }),
        }

        for reverse_page in url_filds:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField)
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField)
                self.assertIsInstance(
                    response.context['form'].fields['image'],
                    forms.fields.ImageField)

    def test_create_post_show_home_group_list_profile_pages(self):
        """Созданный пост отобразился на главной, на странице группы,
        в профиле пользователя."""
        reverse_page_names_post = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
        )

        for name in reverse_page_names_post:
            response = self.authorized_client.get(name)
            self.assertEqual(len(
                response.context['page_obj'].object_list), Post.objects.count()
                )

    def test_post_not_another_group(self):
        """Созданный пост не попал в группу, для которой не был предназначен"""
        new_group = Group.objects.create(
            title='Группа2 для теста',
            slug='test_group2',
            description='Тестовое описание Группы2',
        )
        new_post = Post.objects.create(
            text='Тестовый текст проверка как добавился',
            author=self.user,
            group=self.group)

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': new_group.slug})
        )

        self.assertNotIn(new_post, response.context['page_obj'].object_list)

    def test_cache_index_page(self):
        """Проверка работы кеша"""
        post = Post.objects.create(
            text='Пост под кеш',
            author=self.user)
        content_add = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_delete = self.authorized_client.get(
            reverse('posts:index')).content

        self.assertEqual(content_add, content_delete)
        cache.clear()
        content_cache_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_add, content_cache_clear)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='autor',)
        cls.post_autor = User.objects.create(
            username='post_autor',
        )
        cls.user2 = User.objects.create(
            username='user2',
        )
        cls.post = Post.objects.create(
            text='Подпишись на меня',
            author=cls.post_autor,
        )

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username='user')
        self.client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user2)

    def test_follow(self):
        self.response = (self.client.get(
            reverse('posts:profile_follow', args={self.author})))
        self.assertIs(
            Follow.objects.filter(user=self.user, author=self.author).exists(),
            True
        )

    def test_unfollow(self):
        self.response = (self.client.get(
            reverse('posts:profile_follow', args={self.author})))
        self.response = (self.client.get(
            reverse('posts:profile_unfollow', args={self.author})))
        self.assertIs(
            Follow.objects.filter(user=self.user, author=self.author).exists(),
            False
        )

    def test_follow_on_authors(self):
        """Проверка отписки от пользователя."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        Follow.objects.create(
            user=self.user2,
            author=self.post_autor)

        response = self.author_client.get(
            reverse('posts:follow_index'))

        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто не подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")

        response = self.author_client.get(
            reverse('posts:follow_index'))

        self.assertNotIn(post, response.context['page_obj'].object_list)
