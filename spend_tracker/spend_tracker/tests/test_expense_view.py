from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from expenses.models import Category, Expense


class ExpenseViewTests(APITestCase):
    def setUp(self):
        self.url = reverse('expenses')
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.other_user = User.objects.create_user(username='bob', password='pass12345')
        self.category = Category.objects.create(owner=self.user, name='Food')
        self.other_users_category = Category.objects.create(owner=self.other_user, name='Travel')
        self.client.force_authenticate(user=self.user)

    # --- auth ---
    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- create: happy path ---
    def test_create_expense_success(self):
        payload = {'amount': '150.50', 'category': self.category.id, 'date': str(date.today()), 'note': 'Lunch'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['category_name'], 'Food')
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(Expense.objects.first().owner, self.user)

    def test_note_is_optional(self):
        payload = {'amount': '20.00', 'category': self.category.id, 'date': str(date.today())}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- create: validation ---
    def test_zero_amount_rejected(self):
        payload = {'amount': '0', 'category': self.category.id, 'date': str(date.today())}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data['errors'])

    def test_negative_amount_rejected(self):
        payload = {'amount': '-10.00', 'category': self.category.id, 'date': str(date.today())}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data['errors'])

    def test_future_date_rejected(self):
        tomorrow = date.today() + timedelta(days=1)
        payload = {'amount': '10.00', 'category': self.category.id, 'date': str(tomorrow)}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data['errors'])

    def test_missing_category_rejected(self):
        payload = {'amount': '10.00', 'date': str(date.today())}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data['errors'])

    # --- create: ownership / IDOR protection ---
    def test_cannot_use_another_users_category(self):
        payload = {'amount': '10.00', 'category': self.other_users_category.id, 'date': str(date.today())}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data['errors'])
        self.assertEqual(Expense.objects.count(), 0)

    # --- list: scoping ---
    def test_list_only_returns_own_expenses(self):
        Expense.objects.create(owner=self.user, category=self.category, amount=Decimal('10'), date=date.today())
        Expense.objects.create(owner=self.other_user, category=self.other_users_category, amount=Decimal('20'), date=date.today())

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    # --- list: filters ---
    def test_filter_by_category(self):
        other_category = Category.objects.create(owner=self.user, name='Travel')
        Expense.objects.create(owner=self.user, category=self.category, amount=Decimal('10'), date=date.today())
        Expense.objects.create(owner=self.user, category=other_category, amount=Decimal('20'), date=date.today())

        response = self.client.get(self.url, {'category': self.category.id})
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['category_name'], 'Food')

    def test_filter_by_date_range(self):
        Expense.objects.create(owner=self.user, category=self.category, amount=Decimal('10'), date=date(2026, 1, 5))
        Expense.objects.create(owner=self.user, category=self.category, amount=Decimal('20'), date=date(2026, 3, 5))

        response = self.client.get(self.url, {'start_date': '2026-01-01', 'end_date': '2026-01-31'})
        self.assertEqual(response.data['data']['count'], 1)

    def test_no_results_returns_empty_list_not_error(self):
        response = self.client.get(self.url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(response.data['data']['results'], [])

    # --- list: pagination ---
    def test_pagination_limits_page_size(self):
        for i in range(15):
            Expense.objects.create(owner=self.user, category=self.category, amount=Decimal('5'), date=date.today())

        response = self.client.get(self.url)
        self.assertEqual(response.data['data']['count'], 15)
        self.assertEqual(len(response.data['data']['results']), 10)  # default page_size
        self.assertIsNotNone(response.data['data']['next'])
