"""
Summary calculation logic lives here rather than inline in summary_view.py
so it can be unit-tested directly (test_summary_view.py calls
calculate_summary() straight away, no HTTP/auth/JWT roundtrip needed) and
so the view itself stays a thin HTTP adapter.
"""
from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum

from expenses.constants import NO_PREVIOUS_MONTH_DATA
from expenses.models import Expense

INSIGHT_THRESHOLD_PERCENT = 20
TWO_PLACES = Decimal('0.01')


def _as_currency_string(value):
    # SQLite's Sum() doesn't reliably preserve DecimalField's
    # decimal_places, so a clean "150" can come back instead of "150.00" -
    # quantize explicitly before ever turning an amount into a string.
    return str(Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP))


def _month_bounds(year, month):
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return start, end


def _previous_month(year, month):
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _percent_change(current, previous):
    if not previous:
        return None
    return round(float((current - previous) / previous * 100), 2)


def calculate_summary(user, year, month):
    """
    Returns total spend, a per-category breakdown, month-over-month change,
    and a list of categories whose spend rose more than
    INSIGHT_THRESHOLD_PERCENT versus the previous month, all scoped to the
    given user and calendar month.
    """
    start, end = _month_bounds(year, month)
    prev_year, prev_month = _previous_month(year, month)
    prev_start, prev_end = _month_bounds(prev_year, prev_month)

    current_qs = Expense.objects.filter(owner=user, date__gte=start, date__lte=end)
    previous_qs = Expense.objects.filter(owner=user, date__gte=prev_start, date__lte=prev_end)

    total_spend = current_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    previous_total = previous_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    current_by_category = list(
        current_qs.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    )
    previous_by_category = {
        row['category__name']: row['total']
        for row in previous_qs.values('category__name').annotate(total=Sum('amount'))
    }

    mom_change_percent = _percent_change(total_spend, previous_total)

    insights = []
    for row in current_by_category:
        category_name = row['category__name']
        current_amount = row['total']
        previous_amount = previous_by_category.get(category_name)
        change_percent = _percent_change(current_amount, previous_amount)
        if change_percent is not None and change_percent > INSIGHT_THRESHOLD_PERCENT:
            insights.append({
                'category': category_name,
                'message': f"{category_name} spend increased {round(change_percent)}% vs last month.",
            })

    return {
        'month': f"{year:04d}-{month:02d}",
        'total_spend': _as_currency_string(total_spend),
        'by_category': [
            {'category': row['category__name'], 'total': _as_currency_string(row['total'])}
            for row in current_by_category
        ],
        'previous_month_total': _as_currency_string(previous_total),
        'mom_change_percent': mom_change_percent,
        'mom_change_note': None if previous_total else NO_PREVIOUS_MONTH_DATA,
        'insights': insights,
    }
