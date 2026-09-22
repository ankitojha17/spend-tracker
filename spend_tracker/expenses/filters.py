import django_filters

from expenses.models import Expense


class ExpenseFilter(django_filters.FilterSet):
    """
    Powers GET /api/expenses?category=<id>&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

    Declarative rather than hand-written if/else chains in the view, and
    trivially extendable later (e.g. a min_amount filter is one more line
    here, not a new branch in the view).
    """
    start_date = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Expense
        fields = ['category', 'start_date', 'end_date']
