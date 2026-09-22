from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from expenses.models import Category, Expense

DEMO_USERNAME = 'demo'
DEMO_PASSWORD = 'Demo@1234'

# Deliberately shaped so Travel jumps ~40% month-over-month, to demonstrate
# the >20% insight feature the moment /summary is called.
PREVIOUS_MONTH_SPEND = {
    'Food': Decimal('4000.00'),
    'Travel': Decimal('1500.00'),
    'Rent': Decimal('12000.00'),
    'Utilities': Decimal('2000.00'),
    'Entertainment': Decimal('1000.00'),
}
CURRENT_MONTH_SPEND = {
    'Food': Decimal('4200.00'),
    'Travel': Decimal('2100.00'),
    'Rent': Decimal('12000.00'),
    'Utilities': Decimal('1900.00'),
    'Entertainment': Decimal('1100.00'),
}


class Command(BaseCommand):
    help = "Seeds a demo user with categories and two months of expenses, so /summary shows real data immediately."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username=DEMO_USERNAME, defaults={'email': 'demo@example.com'})
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo user (username: {DEMO_USERNAME}, password: {DEMO_PASSWORD})"))
        else:
            self.stdout.write("Demo user already exists, reusing it.")

        categories = {
            name: Category.objects.get_or_create(owner=user, name=name)[0]
            for name in PREVIOUS_MONTH_SPEND
        }

        # Re-seeding should be idempotent, not additive.
        Expense.objects.filter(owner=user).delete()

        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        self._create_month_expenses(user, categories, PREVIOUS_MONTH_SPEND, previous_month_start)
        self._create_month_expenses(user, categories, CURRENT_MONTH_SPEND, current_month_start)

        self.stdout.write(self.style.SUCCESS("Seeded demo data successfully."))

    @staticmethod
    def _create_month_expenses(user, categories, spend_by_category, month_start):
        day_offset = 2
        for name, amount in spend_by_category.items():
            Expense.objects.create(
                owner=user,
                category=categories[name],
                amount=amount,
                note=f"{name} spend",
                date=month_start + timedelta(days=day_offset % 25),
            )
            day_offset += 3
