from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import AccountViewSet, CategoryViewSet, TransactionViewSet, BudgetViewSet, RecurringTransactionViewSet, ReportView

router = DefaultRouter()
router.register('accounts', AccountViewSet, basename='account')
router.register('categories', CategoryViewSet, basename='category')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('budgets', BudgetViewSet, basename='budget')
router.register('recurring', RecurringTransactionViewSet, basename='recurring')

urlpatterns = router.urls + [
    path('reports/', ReportView.as_view(), name='reports'),
]