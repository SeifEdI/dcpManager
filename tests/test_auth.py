from django.test import TestCase
from django.urls import reverse

class AuthTestCase(TestCase):
    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/auth/login/')

    
