from datetime import date

from rest_framework import serializers

from expenses.constants import AMOUNT_MUST_BE_POSITIVE, CATEGORY_NOT_OWNED, FUTURE_DATE_NOT_ALLOWED
from expenses.models import Category, Expense


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Expense
        fields = ['id', 'amount', 'category', 'category_name', 'note', 'date', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'category': {'error_messages': {'does_not_exist': CATEGORY_NOT_OWNED}},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Scope the category dropdown/validation to the requesting user's
        # own categories only. A category ID that exists but belongs to
        # someone else simply isn't in this queryset, so it's rejected with
        # the same clear message as a category that doesn't exist at all -
        # deliberately, so the error can't be used to probe which IDs exist.
        request = self.context.get('request')
        if request is not None:
            self.fields['category'].queryset = Category.objects.filter(owner=request.user)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(AMOUNT_MUST_BE_POSITIVE)
        return value

    def validate_date(self, value):
        # An expense records money already spent, so a future date isn't a
        # valid state for this model - a planned/recurring expense would be
        # a different feature (e.g. a Budget entity), not a relaxed version
        # of this field.
        if value > date.today():
            raise serializers.ValidationError(FUTURE_DATE_NOT_ALLOWED)
        return value
