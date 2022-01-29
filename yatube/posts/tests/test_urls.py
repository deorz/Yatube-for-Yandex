from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class PostsUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='auth')
        cls.asdf_user = User.objects.create_user(username='asdf')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_asdf = Client()
        self.authorized_client.force_login(self.auth_user)
        self.authorized_client_asdf.force_login(self.asdf_user)

    def test_url_uses_correct_template(self):
        """URL-адрес использует правильный шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.auth_user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template_name in url_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template_name)

    def test_redirect_if_different_user(self):
        """
        Перенаправление на страницу поста, если пользователь
        не автор.
        """
        response = self.authorized_client_asdf.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_url_requires_login(self):
        """Для перехода на страницу необходимо авторизоваться."""
        response = self.client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_404_error_for_unexisting_page(self):
        """Несуществующая страница возвращает код 404."""
        response = self.client.get(
            '/unexisting_page/').status_code
        self.assertEqual(response, HTTPStatus.NOT_FOUND)
