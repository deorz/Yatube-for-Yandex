from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group_str = self.group.__str__()
        group_title = self.group.title
        self.assertEqual(group_str, group_title)

        post_str = self.post.__str__()
        post_text = self.post.text[:15]
        self.assertEqual(post_str, post_text)

    def test_models_have_correct_verbose_names(self):
        """Проверка verbose_name для полей модели."""
        verbose_names = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_model_have_correct_help_texts(self):
        """Проверка help_text для полей модели."""
        help_texts = {
            'text': 'Здесь будет текст вашего поста',
            'group':
                'Можно выбрать группу, которой будет принадлежать пост'
        }
        for field, expected_value in help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value)
