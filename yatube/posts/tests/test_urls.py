from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title = 'Тестовая группа',
            slug = 'test-slug',
            description = 'Тестовое описание',
        )
        cls.post = Post.objects.create(
            author = cls.user,
            text = 'Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testnoname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)


    def test_pages_is_available_to_everyone(self):
        """Страницы доступны любому пользователю."""
        urls_status_code = {
            '/': 200,
            '/group/test-slug/': 200,
            '/profile/auth/': 200,
            '/posts/1/': 200,
        }
        for address, code in urls_status_code.items():
            with self.subTest(code=code):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)
    
    def test_pages_is_only_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)
    
    def test_pages_is_only_author(self):
        """Страница /posts/<post_id>/edit/ доступна автору."""
        if self.authorized_client.force_login(self.user) == self.post.author:
            response = self.authorized_client.get('/posts/1/edit/')
            self.assertEqual(response.status_code, 200)

    def test_create_url_redirect_anonymous(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_not_author(self):
        """Страница /posts/<post_id>/edit/ перенаправляет пользователя
           на страницу поста если он не автор.
        """
        if self.authorized_client.force_login(self.user) != self.post.author:
            response = self.authorized_client.get('/posts/1/edit/', follow=True)
            self.assertRedirects(response, '/profile/testnoname/')

    def test_url_everyone_uses_correct_template(self):
        """Проверка шаблонов для общедоступных адресов."""
        urls_template = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': '404.html',            
        }
        for address, template in urls_template.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_authorized_uses_correct_template(self):
        """Проверка шаблонов для адресов, доступных только 
           автору.
        """
        if self.authorized_client.force_login(self.user) == self.post.author:
            urls_template = {
                '/posts/1/edit/': 'posts/create_post.html',
            }
            for address, template in urls_template.items():
                with self.subTest(template=template):
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)
