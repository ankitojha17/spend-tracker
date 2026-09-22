from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from expenses.models import Category


class CategoryViewTests(APITestCase):
    def setUp(self):
        self.url = reverse('categories')
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_category_success(self):
        response = self.client.post(self.url, {'name': 'Food'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['name'], 'Food')

    def test_blank_name_rejected(self):
        response = self.client.post(self.url, {'name': '   '})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_name_case_insensitive_rejected(self):
        Category.objects.create(owner=self.user, name='Food')
        response = self.client.post(self.url, {'name': 'food'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data['errors'])

    def test_same_name_allowed_for_a_different_user(self):
        Category.objects.create(owner=self.other_user, name='Food')
        response = self.client.post(self.url, {'name': 'Food'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_only_returns_own_categories(self):
        Category.objects.create(owner=self.user, name='Food')
        Category.objects.create(owner=self.other_user, name='Travel')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [c['name'] for c in response.data['data']]
        self.assertEqual(names, ['Food'])
