from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post


User = get_user_model()


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

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

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
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 3',
            'group': self.group.id,
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
