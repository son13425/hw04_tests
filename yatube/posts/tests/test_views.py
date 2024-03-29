import math
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import NUMBER_OF_POSTS_PER_PAGE

from ..models import Group, Post


User = get_user_model()


# Создаем временную папку для медиа
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post1 = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост 2 группы',
            group=cls.group2,
            image=cls.uploaded,
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
                kwargs={'post_id': self.post.id}
            ),
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
                post_image_0 = first_object.image.name
                self.assertEqual(post_author_0, self.author.username)
                self.assertEqual(post_group_0, self.group2.title)
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_image_0, self.post.image)

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
        self.assertEqual(
            post.image.name,
            self.post.image
        )

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
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


class PaginatorViewsTests(TestCase):
    def setUp(self):
        self.number_posts = 15
        self.user = User.objects.create_user(username='noname')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.posts = Post.objects.bulk_create(
            Post(
                author=self.user,
                group=self.group,
                text='Тестовый пост %s' % posts_num,
            )
            for posts_num in range(self.number_posts)
        )

    def test_paginator_provides_required_number_articles(self):
        """паджинатор обеспечивает требуемое количество записей
        на странице."""
        N = NUMBER_OF_POSTS_PER_PAGE
        # число страниц (int)
        number_pages = math.ceil(self.number_posts / N)
        # требуемое количество постов на последней странице
        n = self.number_posts - math.floor(self.number_posts / N) * N
        address_list = {
            reverse('posts:index'): N,
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ): N,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): N,
            reverse('posts:index') + f'?page={number_pages}': n,
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ) + f'?page={number_pages}': n,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ) + f'?page={number_pages}': n,
        }
        for address, list in address_list.items():
            with self.subTest(list=list):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    list
                )


class CacheViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def test_cache_index_page(self):
        """На странице index работает кеширование данных."""
        # кеш очищен
        cache.clear()
        # пост создан
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
        )
        # запрос
        response = self.authorized_client.get(reverse('posts:index'))
        # получен контент
        objects = response.content
        # удален пост
        post.delete()
        # второй запрос
        response1 = self.authorized_client.get(reverse('posts:index'))
        # получен контент
        objects1 = response1.content
        # проверка наличия поста
        self.assertEqual(objects, objects1)
        # кеш очищен
        cache.clear()
        # третий запрос
        response2 = self.authorized_client.get(reverse('posts:index'))
        # получен контент
        objects2 = response2.content
        # проверка отсутствия поста
        self.assertNotEqual(objects, objects2)
