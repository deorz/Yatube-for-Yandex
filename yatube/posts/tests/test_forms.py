import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateEditFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.another_user = User.objects.create_user(
            username='another_user')
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='group_slug',
            description='Тестовое описание',
        )
        cls.another_test_group = Group.objects.create(
            title='Ещё одна тестовая группа',
            slug='another_group_slug',
            description='Ещё одно тестовое описание',
        )
        cls.editable_post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.test_group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.another_authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client.force_login(self.another_user)

    def test_create_post_form(self):
        """
        Валидная форма создает запись в Post.
        """
        posts_count = Post.objects.count()
        group_posts_count = self.test_group.posts.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст нового поста',
            'group': self.test_group.id,
            'image': uploaded_image
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': self.user
            }))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(self.test_group.posts.count(),
                         group_posts_count + 1)
        posts = Post.objects.order_by('-pk')
        self.assertTrue(
            Post.objects.filter(
                pk=posts[0].pk,
                text=form_data['text'],
                author=self.user,
                group_id=form_data['group'],
                image=f'posts/{form_data["image"].name}'
            ).exists()
        )

    def test_post_edit_form(self):
        """
        Валидная форма изменяет запись в Post.
        """
        posts_count = Post.objects.count()
        another_group_posts_count = self.another_test_group.posts.count()
        form_data = {
            'text': 'Измененный текст тестового поста',
            'group': self.another_test_group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.editable_post.pk
            }),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': self.editable_post.pk
            }))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.another_test_group.posts.count(),
                         another_group_posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                pk=self.editable_post.pk,
                text=form_data['text'],
                author=self.user,
                group_id=form_data['group']
            ).exists()
        )

    def test_create_post_form_without_login(self):
        """
        Валидная форма не создает запись в Post,
        если пользователь не авторизован.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст ещё одного нового поста'
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_form_without_login(self):
        """
        Валидная форма не изменяет запись в Post,
        если пользователь не авторизован.
        """
        posts_count = Post.objects.count()
        another_group_posts_count = self.another_test_group.posts.count()
        form_data = {
            'text': 'Измененный текст тестового поста',
            'group': self.another_test_group.id
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.editable_post.pk
            }),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            reverse('users:login')
            + f'?next=/posts/{self.editable_post.pk}/edit/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.another_test_group.posts.count(),
                         another_group_posts_count)
        self.assertFalse(
            Post.objects.filter(
                pk=self.editable_post.pk,
                text=form_data['text'],
                author=self.user,
                group_id=form_data['group']
            ).exists()
        )

    def test_another_author_cant_edit_post(self):
        """
        Валидная форма не изменяет запись в Post,
        если пользователь авторизован, но автор не он.
        """
        posts_count = Post.objects.count()
        another_group_posts_count = self.another_test_group.posts.count()
        form_data = {
            'text': 'Измененный текст тестового поста',
            'group': self.another_test_group.id
        }
        response = self.another_authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.editable_post.pk
            }),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': self.editable_post.pk
            }))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.another_test_group.posts.count(),
                         another_group_posts_count)
        self.assertNotEqual(self.editable_post.text, form_data['text'])
        self.assertNotEqual(self.editable_post.group, form_data['group'])

    def test_only_auth_user_can_add_comments(self):
        """
        Только авторизованные пользователи могут оставлять комментарии.
        """
        comments_count = Comment.objects.filter(
            post_id=self.editable_post.pk).count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.editable_post.pk
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login')
            + f'?next=/posts/{self.editable_post.pk}/comment/')
        self.assertEqual(Comment.objects.filter(
            post_id=self.editable_post.pk).count(), comments_count)

    def test_successful_comment_appear_on_page(self):
        """
        После добавления комментария он появляется на странице поста.
        """
        comments_count = Comment.objects.filter(
            post_id=self.editable_post.pk).count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.editable_post.pk
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.filter(
            post_id=self.editable_post.pk).count(), comments_count + 1)
        response_get = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': self.editable_post.pk
            }))
        comment_objects = response_get.context['comments'][0]
        text_comment = comment_objects.text
        author_comment = comment_objects.author
        post_id_comment = comment_objects.post_id
        self.assertEqual(text_comment, form_data['text'])
        self.assertEqual(author_comment, self.user)
        self.assertEqual(post_id_comment, self.editable_post.pk)
