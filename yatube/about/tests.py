from django.test import TestCase, Client
from django.urls import reverse


class AboutPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_exists_at_desired_location(self):
        """Проверка доступности адресов."""
        urls_status_code = {
            '/about/author/': 200,
            '/about/tech/': 200,
        }
        for address, code in urls_status_code.items():
            with self.subTest(code=code):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)
    
    
    def test_url_uses_correct_template(self):
        """Проверка шаблонов для адресов."""
        urls_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address, template in urls_template.items():
            with self.subTest(template=template):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_accessible_by_name(self):
        """URL, генерируемый при помощи имени, доступен."""
        urls_status_code = {
            'about:author': 200,
            'about:tech': 200,
        }
        for address, code in urls_status_code.items():
            with self.subTest(code=code):
                response = self.guest_client.get(reverse(address))
                self.assertEqual(response.status_code, code)

    def test_pages_uses_correct_template(self):
        """При запросе к странице применяется правильный шаблон."""
        urls_template = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for address, template in urls_template.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse(address))
                self.assertTemplateUsed(response, template)
