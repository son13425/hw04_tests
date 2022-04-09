from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
import time

from yatube.settings import NUMBER_OF_POSTS_PER_PAGE
from ..models import Post, Group


User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='noname')
        cls.author = User.objects.create_user(username='testname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        cls.post1 = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        time.sleep(0.1)
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост 2 группы',
            group=cls.group2,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': self.author.username}),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}),
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
        templates_pages_names = {
                'posts/create_post.html': reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_list_page_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        """Пост с группой появляется на страницах: главная,профиль,группа."""
        views_objects = {
            reverse
            ('posts:index'): 'page_obj',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group2.slug},
            ): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            ): 'page_obj',
        }
        for views, objects in views_objects.items():
            with self.subTest(objects=objects):
                response = self.authorized_client.get(views)
                first_object = response.context[objects][0]
                post_author_0 = first_object.author.username
                post_group_0 = first_object.group.title
                post_text_0 = first_object.text
                self.assertEqual(post_author_0, self.author.username)
                self.assertEqual(post_group_0, self.group2.title)
                self.assertEqual(post_text_0, self.post.text)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']
        self.assertEqual(
            post.author.username,
            self.author.username
        )
        self.assertEqual(
            post.text,
            self.post.text
        )
        self.assertEqual(
            post.group.title,
            self.group2.title
        )

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        url_ff = {
            reverse('posts:post_create'): form_fields,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): form_fields,
        }
        for url, ff in url_ff.items():
            with self.subTest(ff=ff):
                response = self.authorized_author.get(url)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = (
                            response.context.get('form').fields.get(value)
                        )
                        self.assertIsInstance(form_field, expected)

    def test_post_group2_not_in_posts_group(self):
        """Пост из группы 1 не попал в группу 2."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group2.slug})
        )
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.group.title
        post_text_0 = first_object.text
        self.assertNotEqual(post_group_0, self.group.title)
        self.assertNotEqual(post_text_0, self.post1.text)
    
    def test_first_page_contains_ten_records(self):
        """паджинатор обеспечивает требуемое количество записей
        на странице."""
        number_posts = 15
        Post.objects.bulk_create(
            Post(
                    author=self.user,
                    group=self.group,
                    text='Тестовый пост %s' % posts_num
                )
                for posts_num in range(number_posts)
            )
        N = NUMBER_OF_POSTS_PER_PAGE
        # cоздан пагинатор для всех постов на странице
        paginator1 = Paginator(Post.objects.all(), N)
        # число страниц (int)
        number_pages1 = paginator1.num_pages
        # получена последняя страница
        page_end1 = paginator1.page(number_pages1)
        # посчитано количество постов на последней странице
        n1 = page_end1.object_list.count()

        group = get_object_or_404(Group, slug=self.group.slug)
        posts_group = group.posts.all()
        paginator2 = Paginator(posts_group, N)
        number_pages2 = paginator2.num_pages
        page_end2 = paginator2.page(number_pages2)
        n2 = page_end2.object_list.count()

        author = get_object_or_404(User, username=self.user.username)
        posts_author = author.author_posts.all()
        paginator3 = Paginator(posts_author, N)
        number_pages3 = paginator3.num_pages
        page_end3 = paginator3.page(number_pages3)
        n3 = page_end3.object_list.count()
        address_list = {
            reverse('posts:index'):  N,
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ):  N,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ):  N,
            reverse('posts:index') + f'?page={number_pages1}':  n1,
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ) + f'?page={number_pages2}':  n2,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ) + f'?page={number_pages3}':  n3,
        }
        for address, list in address_list.items():
            with self.subTest(list=list):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    list
                )
