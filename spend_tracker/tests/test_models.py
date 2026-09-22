from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from expenses.models import Category, Expense


class CategoryModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def test_creates_category(self):
        category = Category.objects.create(owner=self.user, name='Food')
        self.assertEqual(category.name, 'Food')
        self.assertEqual(category.owner, self.user)

    def test_same_name_allowed_for_different_users(self):
        other_user = User.objects.create_user(username='bob', password='pass12345')
        Category.objects.create(owner=self.user, name='Food')
        # Should not raise - the unique constraint is scoped per-owner.
        Category.objects.create(owner=other_user, name='Food')
        self.assertEqual(Category.objects.filter(name='Food').count(), 2)

    def test_duplicate_name_for_same_user_rejected_at_db_level(self):
        Category.objects.create(owner=self.user, name='Food')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(owner=self.user, name='Food')


class ExpenseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.category = Category.objects.create(owner=self.user, name='Food')

    def test_creates_expense_with_decimal_amount(self):
        expense = Expense.objects.create(
            owner=self.user, category=self.category, amount=Decimal('99.99'), date=date.today(),
        )
        self.assertEqual(expense.amount, Decimal('99.99'))

    def test_note_defaults_to_empty_string(self):
        expense = Expense.objects.create(
            owner=self.user, category=self.category, amount=Decimal('10.00'), date=date.today(),
        )
        self.assertEqual(expense.note, '')

    def test_category_cannot_be_deleted_while_referenced(self):
        Expense.objects.create(
            owner=self.user, category=self.category, amount=Decimal('10.00'), date=date.today(),
        )
        with self.assertRaises(ProtectedError):
            self.category.delete()
