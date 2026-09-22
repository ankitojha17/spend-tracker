from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SignUpViewTests(APITestCase):
    def setUp(self):
        self.url = reverse('signup')
        self.valid_payload = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
        }

    def test_signup_success(self):
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'newuser')
        self.assertNotIn('password', response.data['data'])
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_password_is_hashed_not_stored_plain(self):
        self.client.post(self.url, self.valid_payload)
        user = User.objects.get(username='newuser')
        self.assertNotEqual(user.password, 'StrongPass123')

    def test_password_mismatch_rejected(self):
        payload = {**self.valid_payload, 'confirm_password': 'DifferentPass123'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('confirm_password', response.data['errors'])

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='newuser', password='pass12345')
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['errors'])

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='someoneelse', email='new@example.com', password='pass12345')
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['errors'])

    def test_weak_password_rejected(self):
        payload = {**self.valid_payload, 'password': '123', 'confirm_password': '123'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['errors'])

    def test_missing_required_field_rejected(self):
        payload = {**self.valid_payload}
        del payload['email']
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['errors'])
