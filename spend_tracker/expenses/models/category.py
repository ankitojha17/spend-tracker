from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    """
    Categories are user-owned rather than a global fixed list, so each user
    manages their own set (two users can both have a "Food" category without
    clashing) and categories can grow richer fields later (budget_limit,
    color, is_active, ...) without touching the Expense model at all.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'category'
        # DB-level guarantee backing the serializer's case-insensitive
        # check: a user can't end up with two exact-duplicate categories
        # even under a race condition.
        unique_together = ('owner', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.owner.username})"
