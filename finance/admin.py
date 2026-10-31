from django.contrib import admin
from .models import Account, Category, Transaction, Budget, RecurringTransaction

# Register your models here.
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'account_type', 'current_balance', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category_type', 'parent')
    list_filter = ('category_type',)
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'account', 'transaction_type', 'category', 'amount')
    list_filter = ('transaction_type', 'account')
    search_fields = ('description', 'notes')

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'user', 'period_type', 'amount', 'start_date', 'end_date', 'rollover_enabled')
    list_filter = ('period_type', 'rollover_enabled')

@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'account', 'transaction_type', 'amount', 'frequency', 'next_due_date', 'is_active')
    list_filter = ('transaction_type', 'frequency', 'is_active')
    search_fields = ('name',)