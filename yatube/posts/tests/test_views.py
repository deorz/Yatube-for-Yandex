import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, Follow

User = get_user_model()

NUMBER_OF_POSTS = 12

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def create_image():
    image = (
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    )
    uploaded = SimpleUploadedFile(
        name='image.gif',
        content=image,
        content_type='image/gif'
    )
    return uploaded


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.different_user = User.objects.create_user(
            username='different_user'
        )
        cls.one_more_user = User.objects.create_user(
            username='one_more_user'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        cls.different_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='different-group-slug',
            description='Описание тестовой группы'
        )
        cls.follow_one_more_user = Follow.objects.create(
            user=cls.one_more_user,
            author=cls.user
        )
        cls.post_list = []
        for i in range(NUMBER_OF_POSTS):
            cls.post_list.append(Post.objects.create(
                text=f'Тестовый пост{i}',
                author=cls.user,
                group=cls.group,
                image=create_image()
            ))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.another_client = Client()
        self.one_more_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_client.force_login(self.different_user)
        self.one_more_client.force_login(self.one_more_user)

    def correct_context(self,
                        response,
                        post_list,
                        context_key,
                        check_group, ):
        if context_key == 'post':
            context_object = response.context[context_key]
        else:
            context_object = response.context[context_key][0]
        post_text_0 = context_object.text
        post_author_0 = context_object.author
        post_pk_0 = context_object.pk
        if check_group:
            post_group_0 = context_object.group
            self.assertEqual(str(post_group_0),
                             f'{post_list[-1].group}')
        if context_object.image:
            post_image_0 = context_object.image
            self.assertEqual(post_image_0, post_list[-1].image)
        self.assertEqual(post_text_0, post_list[-1].text)
        self.assertEqual(str(post_author_0),
                         f'{post_list[-1].author}')
        self.assertEqual(post_pk_0, post_list[-1].pk)

    def test_views_uses_correct_template(self):
        """View-функция использует правильный шаблон."""
        template_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            }): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': self.user
            }): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post_list[0].pk
            }): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post_list[0].pk
            }): 'posts/create_post.html',
        }

        for reverse_name, template in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """
        Шаблон posts:index сформирован с правильным контекстом,
        а также работает паджинатор.
         """
        response = self.authorized_client.get(reverse('posts:index'))
        self.correct_context(response=response,
                             post_list=self.post_list,
                             context_key='page_obj',
                             check_group=False)

        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_PER_PAGE)

        if Post.objects.count() % settings.POSTS_PER_PAGE == 0:
            response = self.authorized_client.get(
                reverse('posts:index') + '?page='
                + str(int(Post.objects.count()
                          / settings.POSTS_PER_PAGE)))
            self.assertEqual(len(response.context['page_obj']),
                             int(Post.objects.count()
                                 / (Post.objects.count()
                                    / settings.POSTS_PER_PAGE)))

        else:
            response = self.authorized_client.get(
                reverse('posts:index') + '?page='
                + str(int(Post.objects.count()
                          / settings.POSTS_PER_PAGE) + 1))
            self.assertEqual(len(response.context['page_obj']),
                             Post.objects.count()
                             % settings.POSTS_PER_PAGE)

    def test_posts_group_page_show_correct_context(self):
        """
        Шаблон posts:group_list сформирован с правильным контекстом,
        а также работает паджинатор.
        """
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        self.correct_context(response=response,
                             post_list=self.post_list,
                             context_key='page_obj',
                             check_group=True)

        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_PER_PAGE)

        if Post.objects.count() % settings.POSTS_PER_PAGE == 0:
            response = self.authorized_client.get(reverse(
                'posts:group_list', kwargs={
                    'slug': self.group.slug}) + '?page=' + str(
                int(Post.objects.count() / settings.POSTS_PER_PAGE)))
            self.assertEqual(len(response.context['page_obj']),
                             int(Post.objects.count()
                                 / (Post.objects.count()
                                    / settings.POSTS_PER_PAGE)))

        else:
            response = self.authorized_client.get(reverse(
                'posts:group_list', kwargs={
                    'slug': self.group.slug}) + '?page=' + str(
                int(Post.objects.count()
                    / settings.POSTS_PER_PAGE) + 1))
            self.assertEqual(len(response.context['page_obj']),
                             Post.objects.count()
                             % settings.POSTS_PER_PAGE)

    def test_profile_page_show_correct_context(self):
        """
        Шаблон posts:profile сформирован с правильным контекстом,
        а также работает паджинатор.
        """
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={
                'username': self.user}))
        self.correct_context(response=response,
                             post_list=self.post_list,
                             context_key='page_obj',
                             check_group=True)

        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={
                'username': self.user}))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_PER_PAGE)

        if Post.objects.count() % settings.POSTS_PER_PAGE == 0:
            response = self.authorized_client.get(reverse(
                'posts:profile', kwargs={
                    'username': self.user}) + '?page=' + str(
                int(Post.objects.count() / settings.POSTS_PER_PAGE)))
            self.assertEqual(len(response.context['page_obj']),
                             int(Post.objects.count()
                                 / (Post.objects.count()
                                    / settings.POSTS_PER_PAGE)))

        else:
            response = self.authorized_client.get(reverse(
                'posts:profile', kwargs={
                    'username': self.user}) + '?page=' + str(
                int(Post.objects.count()
                    / settings.POSTS_PER_PAGE) + 1))
            self.assertEqual(len(response.context['page_obj']),
                             Post.objects.count()
                             % settings.POSTS_PER_PAGE)

    def test_post_detail_page_show_correct_context(self):
        """
        Шаблон posts:post_detail сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={
                'post_id': self.post_list[-1].pk}))
        self.correct_context(response=response,
                             post_list=self.post_list,
                             context_key='post',
                             check_group=True)

    def test_create_post_page_show_correct_context(self):
        """
        Шаблон posts:create_post сформирован с правильным контекстом,
        а поля формы соответствуют форме модели.
        """
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(
                    value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """
        Шаблон posts:post_edit сформирован с правильным контекстом,
        а поля формы соответствуют форме модели.
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post_list[-1].pk
            }))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(
                    value)
                self.assertIsInstance(form_field, expected)

    def test_post_dont_appear_in_different_group(self):
        """
        При создании поста он не появляется в другой группе.
        """
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={
                'slug': self.different_group.slug}))
        with self.assertRaises(IndexError):
            response.context['page_obj'][0]

    def test_auth_user_can_follow(self):
        """
        Авторизованный пользователь может подписываться на другого.
        """
        follow_count = Follow.objects.count()
        self.another_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.user
        }))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.different_user,
                author=self.user
            ).exists()
        )

    def test_auth_user_can_unfollow(self):
        """
        Авторизованный пользователь может отписываться.
        """
        follow_count = Follow.objects.count()
        self.another_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={
                        'username': self.user
                    }))
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.different_user,
                author=self.user
            ).exists())

    def test_new_post_appear_on_follow_user(self):
        """
        Новый пост появляется у подписавшегося пользователя
        """
        response = self.one_more_client.get(
            reverse('posts:follow_index')
        )
        self.correct_context(
            response=response,
            post_list=self.post_list,
            context_key='page_obj',
            check_group=False
        )

    def test_new_post_dont_appear_on_other_users(self):
        """
        Новый пост не появляется у пользователей,
        которые не подписаны на автора.
        """
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        with self.assertRaises(IndexError):
            self.correct_context(
                response=response,
                post_list=self.post_list,
                context_key='page_obj',
                check_group=False
            )
