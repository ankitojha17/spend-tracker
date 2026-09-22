from django.contrib.auth.models import User
from django.db import models

from expenses.models.category import Category


class Expense(models.Model):
    """
    An expense is a record of money already spent, tied to exactly one
    category (a real FK, not a free-text field, so totals/filters stay
    accurate even if a category is later renamed).

    amount uses DecimalField rather than Float - money must never be stored
    as a binary float, since floats can't represent values like 0.10
    exactly and that error compounds across a running total.

    category uses on_delete=PROTECT rather than CASCADE: in a finance
    context, a category that already has real spend recorded against it
    should not be silently deletable (and take that spend history with it).
    There's no category-delete endpoint in this project yet, but the
    constraint documents the intent for when one is added.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True, default='')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expense'
        ordering = ['-date', '-id']
        indexes = [
            # These match exactly how /expenses and /summary filter and
            # group data, so the common queries stay index-backed as the
            # table grows.
            models.Index(fields=['owner', 'date']),
            models.Index(fields=['owner', 'category']),
        ]

    def __str__(self):
        return f"{self.amount} - {self.category.name} ({self.date})"
