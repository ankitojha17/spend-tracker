from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from expenses.models import Category, Expense
from expenses.services import calculate_summary


class SummaryServiceTests(APITestCase):
    """
    Tests the pure calculation function directly - no HTTP/auth needed,
    which keeps these fast and focused purely on the arithmetic edge cases.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.food = Category.objects.create(owner=self.user, name='Food')
        self.travel = Category.objects.create(owner=self.user, name='Travel')

    def test_total_and_by_category_breakdown(self):
        Expense.objects.create(owner=self.user, category=self.food, amount=Decimal('100'), date=date(2026, 9, 5))
        Expense.objects.create(owner=self.user, category=self.travel, amount=Decimal('50'), date=date(2026, 9, 10))

        result = calculate_summary(self.user, 2026, 9)

        self.assertEqual(result['total_spend'], '150.00')
        self.assertEqual(len(result['by_category']), 2)

    def test_no_data_at_all_returns_zero_not_error(self):
        result = calculate_summary(self.user, 2026, 9)
        self.assertEqual(result['total_spend'], '0.00')
        self.assertEqual(result['by_category'], [])
        self.assertIsNone(result['mom_change_percent'])
        self.assertIsNotNone(result['mom_change_note'])

    def test_mom_change_percent_calculated_correctly(self):
        Expense.objects.create(owner=self.user, category=self.food, amount=Decimal('100'), date=date(2026, 8, 5))
        Expense.objects.create(owner=self.user, category=self.food, amount=Decimal('150'), date=date(2026, 9, 5))

        result = calculate_summary(self.user, 2026, 9)

        self.assertEqual(result['mom_change_percent'], 50.0)

    def test_zero_previous_month_returns_null_change_with_note(self):
        Expense.objects.create(owner=self.user, category=self.food, amount=Decimal('100'), date=date(2026, 9, 5))
        # No expenses at all in August.
        result = calculate_summary(self.user, 2026, 9)

        self.assertIsNone(result['mom_change_percent'])
        self.assertIsNotNone(result['mom_change_note'])

    def test_january_wraps_to_previous_december(self):
        Expense.objects.create(owner=self.user, category=self.food, amount=Decimal('100'), date=date(2025, 12, 5))
        Expense.objects.create(owner=self.user, category=self.food, amount=Decimal('120'), date=date(2026, 1, 5))

        result = calculate_summary(self.user, 2026, 1)

        self.assertEqual(result['previous_month_total'], '100.00')
        self.assertEqual(result['mom_change_percent'], 20.0)

    def test_insight_flagged_when_category_increases_over_20_percent(self):
        Expense.objects.create(owner=self.user, category=self.travel, amount=Decimal('100'), date=date(2026, 8, 5))
        Expense.objects.create(owner=self.user, category=self.travel, amount=Decimal('140'), date=date(2026, 9, 5))

        result = calculate_summary(self.user, 2026, 9)

        self.assertEqual(len(result['insights']), 1)
        self.assertEqual(result['insights'][0]['category'], 'Travel')

    def test_no_insight_when_increase_is_20_percent_or_under(self):
        Expense.objects.create(owner=self.user, category=self.travel, amount=Decimal('100'), date=date(2026, 8, 5))
        Expense.objects.create(owner=self.user, category=self.travel, amount=Decimal('120'), date=date(2026, 9, 5))

        result = calculate_summary(self.user, 2026, 9)

        self.assertEqual(result['insights'], [])

    def test_no_insight_for_category_with_no_previous_month_data(self):
        # Travel is brand new this month - a spike from zero isn't a
        # meaningful "increase" to flag, it's just a new category.
        Expense.objects.create(owner=self.user, category=self.travel, amount=Decimal('500'), date=date(2026, 9, 5))

        result = calculate_summary(self.user, 2026, 9)

        self.assertEqual(result['insights'], [])

    def test_summary_scoped_to_requesting_user_only(self):
        other_user = User.objects.create_user(username='bob', password='pass12345')
        other_category = Category.objects.create(owner=other_user, name='Food')
        Expense.objects.create(owner=other_user, category=other_category, amount=Decimal('999'), date=date(2026, 9, 5))

        result = calculate_summary(self.user, 2026, 9)

        self.assertEqual(result['total_spend'], '0.00')


class SummaryViewTests(APITestCase):
    """A thinner set of tests for the HTTP layer itself: auth, param parsing, defaults."""

    def setUp(self):
        self.url = reverse('summary')
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_defaults_to_current_month_when_no_param_given(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['month'], date.today().strftime('%Y-%m'))

    def test_explicit_month_param_used(self):
        response = self.client.get(self.url, {'month': '2026-03'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['month'], '2026-03')

    def test_invalid_month_format_returns_400(self):
        response = self.client.get(self.url, {'month': '2026/03'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
