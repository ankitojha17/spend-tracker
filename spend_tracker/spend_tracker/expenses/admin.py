from django.contrib import admin

from expenses.models import Category, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name', 'owner__username')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'category', 'amount', 'date', 'created_at')
    list_filter = ('category', 'owner')
    search_fields = ('note', 'owner__username')
    date_hierarchy = 'date'
