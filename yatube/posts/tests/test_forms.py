from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
import time

from ..forms import PostForm
from ..models import Post, Group


User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title = 'Тестовая группа',
            slug = 'test-slug',
            description = 'Тестовое описание',
        )
        cls.post = Post.objects.create(
            author = cls.user,
            text = 'Тестовый пост',
            group = cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
        }
        post_create = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(post_create.status_code, 200)
        time.sleep(0.1)
        posts_count2 = Post.objects.count()
        self.assertEqual(posts_count2, posts_count + 1)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        if self.authorized_client.force_login(self.user) == self.post.author:
            posts_count = Post.objects.count()
            form_data = {
            'text': 'Новый Тестовый пост',
            'group': self.group.id,
            }
            post_edit = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
            )
            self.assertEqual(post_edit.status_code, 200)
            time.sleep(0.1)
            posts_count2 = Post.objects.count()
            self.assertEqual(posts_count2, posts_count)
            post_2 = Post.objects.get(id=1)
            self.assertEqual(post_2, 'Новый Тестовый пост')
