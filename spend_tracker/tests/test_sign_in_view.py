from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SignInViewTests(APITestCase):
    def setUp(self):
        # The login endpoint has a dedicated 5/min throttle (see
        # utils/throttles.py) - without clearing the cache here, earlier
        # tests' login attempts in this same run count against that limit
        # and later ones get wrongly rate-limited.
        cache.clear()
        self.url = reverse('login')
        self.user = User.objects.create_user(username='alice', password='CorrectPass123')

    def test_login_success_returns_tokens(self):
        response = self.client.post(self.url, {'username': 'alice', 'password': 'CorrectPass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

    def test_wrong_password_returns_401(self):
        response = self.client.post(self.url, {'username': 'alice', 'password': 'WrongPass'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_nonexistent_username_returns_401(self):
        response = self.client.post(self.url, {'username': 'ghost', 'password': 'whatever'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_error_message_does_not_reveal_which_field_was_wrong(self):
        wrong_password = self.client.post(self.url, {'username': 'alice', 'password': 'WrongPass'})
        wrong_username = self.client.post(self.url, {'username': 'ghost', 'password': 'whatever'})
        self.assertEqual(wrong_password.data['message'], wrong_username.data['message'])


class TokenRefreshViewTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='alice', password='CorrectPass123')
        login_response = self.client.post(reverse('login'), {'username': 'alice', 'password': 'CorrectPass123'})
        self.refresh_token = login_response.data['data']['refresh']

    def test_refresh_returns_new_access_token(self):
        response = self.client.post(reverse('token_refresh'), {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['data'])

    def test_invalid_refresh_token_returns_401(self):
        response = self.client.post(reverse('token_refresh'), {'refresh': 'not-a-real-token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
