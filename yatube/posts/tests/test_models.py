from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth'),
            text='Тестовый текст',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(str(self.post),
                         self.post.text[:settings.LEN_OF_POSTS])
