import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment


User = get_user_model()


# Создаем временную папку для медиа
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='noname')
        cls.author = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # удаляем временную папку с медиа
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
            'image': self.uploaded,
        }
        post_create = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(post_create.status_code, HTTPStatus.OK)
        posts_count2 = Post.objects.count()
        self.assertEqual(posts_count2, posts_count + 1)
        # проверяем корректность заполненых полей созданого поста
        new_post = Post.objects.first()
        self.assertEqual(new_post.author.username, self.user.username)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.title, self.group.title)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый Тестовый пост',
            'group': self.group.id,
            'image': self.uploaded,
        }
        post_edit = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(post_edit.status_code, HTTPStatus.OK)
        posts_count2 = Post.objects.count()
        self.assertEqual(posts_count2, posts_count)
        post_2 = Post.objects.get(id=self.post.id)
        self.assertEqual(post_2.text, form_data['text'])

    def test_anonymous_cannot_publish_post(self):
        """Гость не может опубликовать пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 3',
            'group': self.group.id,
            'image': self.uploaded,
        }
        post_create = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        posts_count2 = Post.objects.count()
        self.assertEqual(posts_count2, posts_count)
        login_redirect = reverse('users:login')
        create_redirect = reverse('posts:post_create')
        expected_redirect = f'{login_redirect}?next={create_redirect}'
        self.assertRedirects(post_create, expected_redirect)

    def test_anonymous_cannot_publish_comment(self):
        """Гость не может опубликовать комментарий."""
        comment_count = Comment.objects.filter(
            post=self.post.id,
            active=True
        ).all().count()
        form_data = {
            'text': 'Комментарий'
        }
        comment_create = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comment_count2 = Comment.objects.filter(
            post=self.post.id,
            active=True
        ).all().count()
        self.assertEqual(comment_count2, comment_count)
        login_redirect = reverse('users:login')
        create_redirect = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        )
        expected_redirect = f'{login_redirect}?next={create_redirect}'
        self.assertRedirects(comment_create, expected_redirect)

    def test_authorized_user_can_publish_comment(self):
        """Авторизованный пользователь может опубликовать комментарий."""
        comment_count = Comment.objects.filter(
            post=self.post.id,
            active=True
        ).all().count()
        form_data = {
            'text': 'Комментарий'
        }
        comment_create = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(comment_create.status_code, HTTPStatus.OK)
        comment_count2 = Comment.objects.filter(
            post=self.post.id,
            active=True
        ).all().count()
        self.assertEqual(comment_count2, comment_count + 1)
        new_comment = Comment.objects.filter(
            post=self.post.id,
            active=True
        ).first()
        self.assertEqual(new_comment.text, form_data['text'])
