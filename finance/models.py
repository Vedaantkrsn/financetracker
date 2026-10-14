from django.db import models, transaction as db_transaction
from django.contrib.auth.models import User


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('bank', 'Bank Account'),
        ('cash', 'Cash'),
        ('wallet', 'Digital Wallet'),
        ('credit_card', 'Credit Card'),
        ('investment', 'Investment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    institution = models.CharField(max_length=100, blank=True)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"


class Category(models.Model):
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, blank=True)  # hex code like #FF5733

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transfer_direction = models.CharField(
        max_length=3, choices=[('out', 'Out'), ('in', 'In')], null=True, blank=True
    )
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    linked_transaction = models.OneToOneField(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_from'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.account.name}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old_amount = None
        old_type = None
        old_account_id = None
        old_transfer_direction = None

        if not is_new:
            old = Transaction.objects.get(pk=self.pk)
            old_amount = old.amount
            old_type = old.transaction_type
            old_account_id = old.account_id
            old_transfer_direction = old.transfer_direction

        super().save(*args, **kwargs)

        with db_transaction.atomic():
            if is_new:
                self._apply_balance_change(self.account, self.amount, self.transaction_type, self.transfer_direction)
            else:
                # reverse old effect, apply new effect
                old_account = Account.objects.get(pk=old_account_id)
                self._apply_balance_change(old_account, old_amount, old_type, old_transfer_direction, reverse=True)
                self._apply_balance_change(self.account, self.amount, self.transaction_type, self.transfer_direction)

    def delete(self, *args, **kwargs):
        with db_transaction.atomic():
            paired = None
            if self.transaction_type == 'transfer' and self.linked_transaction_id:
                paired = self.linked_transaction
            else:
                try:
                    paired = self.linked_from
                except Transaction.DoesNotExist:
                    paired = None

            if paired:
                # prevents paired.delete() from trying to re-find/re-delete us,
                # since we're about to delete ourselves right below
                paired.linked_transaction_id = None

            self._apply_balance_change(self.account, self.amount, self.transaction_type, self.transfer_direction, reverse=True)
            super().delete(*args, **kwargs)

            if paired:
                paired.delete()

    @staticmethod
    def _apply_balance_change(account, amount, transaction_type, transfer_direction=None, reverse=False):
        sign = -1 if reverse else 1
        if transaction_type == 'income':
            account.current_balance += sign * amount
        elif transaction_type == 'expense':
            account.current_balance -= sign * amount
        elif transaction_type == 'transfer':
            if transfer_direction == 'in':
                account.current_balance += sign * amount
            else:
                account.current_balance -= sign * amount
        account.save(update_fields=['current_balance'])

class Budget(models.Model):
    PERIOD_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    rollover_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.category.name} — {self.period_type} — {self.start_date}"
