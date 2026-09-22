from django.urls import path

from expenses.views.category_view import CategoryListCreateView
from expenses.views.expense_view import ExpenseListCreateView
from expenses.views.sign_in_view import SignInView
from expenses.views.sign_up_view import SignUpView
from expenses.views.summary_view import SummaryView
from expenses.views.token_refresh_view import CustomTokenRefreshView

urlpatterns = [
    path('auth/signup', SignUpView.as_view(), name='signup'),
    path('auth/login', SignInView.as_view(), name='login'),
    path('auth/refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),

    path('categories', CategoryListCreateView.as_view(), name='categories'),
    path('expenses', ExpenseListCreateView.as_view(), name='expenses'),
    path('summary', SummaryView.as_view(), name='summary'),
]
