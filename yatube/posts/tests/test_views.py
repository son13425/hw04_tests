from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms
import time

from ..models import Post, Group


User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        number_posts = 13
        for posts_num in range(number_posts):
            time.sleep(0.1)
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост %s' % posts_num,
                group=cls.group,
            )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        time.sleep(0.1)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 2 группы',
            group=cls.group2,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': 'testname'}),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_author(self):
        """URL-адрес использует соответствующий шаблон,
        если пользователь - автор.
        """
        if self.authorized_client.force_login(self.user) == self.post.author:
            templates_pages_names = {
                'posts/create_post.html': reverse(
                    'posts:post_edit',
                    kwargs={'post_id': '1'}),
            }
            for template, reverse_name in templates_pages_names.items():
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def test_list_page_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        """Пост с группой появляется на страницах: главная,профиль,группа."""
        views_objects = {
            reverse
            ('posts:index'): 'page_obj',
            reverse
            ('posts:group_posts', kwargs={'slug': 'test-slug2'}): 'page_obj',
            reverse
            ('posts:profile', kwargs={'username': 'testname'}): 'page_obj',
        }
        for views, objects in views_objects.items():
            with self.subTest(objects=objects):
                response = self.authorized_client.get(views)
                first_object = response.context[objects][0]
                post_author_0 = first_object.author.username
                post_group_0 = first_object.group.title
                post_text_0 = first_object.text
                self.assertEqual(post_author_0, 'testname')
                self.assertEqual(post_group_0, 'Тестовая группа 2')
                self.assertEqual(post_text_0, 'Тестовый пост 2 группы')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})))
        self.assertEqual(
            response.context.get('post').author.username, 'testname')
        self.assertEqual(
            response.context.get('post').text, 'Тестовый пост 0')
        self.assertEqual(
            response.context.get('post').group.title, 'Тестовая группа')

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        if self.authorized_client.force_login(self.user) == self.post.author:
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            url_ff = {
                reverse('posts:post_create'): form_fields,
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': '1'}): form_fields,
            }
            for url, ff in url_ff.items():
                with self.subTest(ff=ff):
                    response = self.authorized_client.get(url)
                    for value, expected in form_fields.items():
                        with self.subTest(value=value):
                            form_field = (
                                response.context.get('form').fields.get(value)
                            )
                            self.assertIsInstance(form_field, expected)

    def test_first_page_contains_ten_records(self):
        """Первая страница содержит 10 записей."""
        address_list = {
            '/': 'page_obj',
            '/group/test-slug/': 'page_obj',
            '/profile/testname/': 'page_obj',
        }
        for address, list in address_list.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(len(response.context[list]), 10)

    def test_second_page_contains_three_records(self):
        """Вторая страница содержит 3 записи."""
        address_list = {
            '/': 'page_obj',
            '/group/test-slug/': 'page_obj',
            '/profile/testname/': 'page_obj',
        }
        for address, list in address_list.items():
            with self.subTest(list=list):
                response = self.client.get(address + '?page=2')
                self.assertEqual(len(response.context[list]), 4)

    def test_post_group2_not_in_posts_group(self):
        """Пост из группы 1 не попал в группу 2."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test-slug2'})
        )
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.group.title
        post_text_0 = first_object.text
        self.assertNotEqual(post_group_0, 'Тестовая группа')
        self.assertNotEqual(post_text_0, 'Тестовый пост')
