from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user
        )

    def test_index_cache(self):
        """Проверяем работу кеширования главной страницы"""
        response_before_post = self.client.get(reverse('posts:index'))
        Post.objects.create(
            text='deleted',
            author=self.user,
        )
        response_after_post = self.client.get(reverse('posts:index'))
        self.assertEqual(response_before_post.content,
                         response_after_post.content)

        cache.clear()
        response_after_clear_cache = self.client.get(
            reverse('posts:index'))
        self.assertNotEqual(response_after_clear_cache.content,
                            response_after_post.content)
