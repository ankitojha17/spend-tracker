from rest_framework import serializers

from expenses.constants import CATEGORY_ALREADY_EXISTS
from expenses.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category name cannot be blank.")

        # DB unique_together on (owner, name) is exact-match only; this
        # catches "Food" vs "food" as the same category before it ever
        # reaches the database, with a clear message instead of a raw
        # IntegrityError.
        request = self.context['request']
        if Category.objects.filter(owner=request.user, name__iexact=value).exists():
            raise serializers.ValidationError(CATEGORY_ALREADY_EXISTS)
        return value
