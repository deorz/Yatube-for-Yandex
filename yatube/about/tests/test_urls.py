from django.test import TestCase, Client


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_page(self):
        """
        Страница /about/author/ возвращает код 200.
        """
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_tech_page(self):
        """
        Страница /about/tech/ возвращает код 200.
        """
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)
