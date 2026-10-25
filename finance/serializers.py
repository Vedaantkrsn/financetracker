from rest_framework import serializers
from .models import Account, Category, Transaction, Budget
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Sum
import calendar


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            'id', 'name', 'account_type', 'institution',
            'current_balance', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    has_transactions=serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type', 'parent', 'icon', 'color', 'is_active', 'has_transactions']
    def  get_has_transactions(self, obj):
        return obj.transactions.exists()

    def validate_parent(self, value):
        if value is not None and value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid parent category")
        return value
    

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    class Meta:
        model=User
        fields = ['username','email','password']
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class TransactionSerializer(serializers.ModelSerializer):
    to_account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'category', 'transaction_type', 'transfer_direction', 'amount',
            'date', 'description', 'notes', 'linked_transaction',
            'to_account', 'created_at', 'updated_at'
        ]
        read_only_fields = ['linked_transaction', 'transfer_direction', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('transaction_type') == 'transfer' and not data.get('to_account'):
            raise serializers.ValidationError("to_account is required for transfers.")
        if data.get('transaction_type') != 'transfer' and data.get('to_account'):
            raise serializers.ValidationError("to_account should only be set for transfers.")
        if data.get('transaction_type') == 'transfer' and data.get('account') == data.get('to_account'):
            raise serializers.ValidationError("Cannot transfer to the same account.")
        return data

    def create(self, validated_data):
        to_account = validated_data.pop('to_account', None)
        user = self.context['request'].user

        if validated_data.get('transaction_type') == 'transfer':
            validated_data['transfer_direction'] = 'out'

        transaction = Transaction.objects.create(user=user, **validated_data)

        if transaction.transaction_type == 'transfer':
            linked = Transaction.objects.create(
                user=user,
                account=to_account,
                category=None,
                transaction_type='transfer', 
                transfer_direction='in',
                amount=transaction.amount,
                date=transaction.date,
                description=f"Transfer from {transaction.account.name}",
            )
            Transaction.objects.filter(pk=transaction.pk).update(linked_transaction=linked)
            transaction.refresh_from_db()

        return transaction

    def validate_account(self,value):
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid account")
        return value

    def validate_category(self,value):
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid category")
        return value

    def validate_to_account(self,value):
            if value.user != self.context['request'].user:
                raise serializers.ValidationError("Invalid to_account")
            return value

class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    percent_used = serializers.SerializerMethodField()
    effective_amount = serializers.SerializerMethodField()
    rollover_amount = serializers.SerializerMethodField()
    rollover_from = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Budget
        fields = [
            'id', 'category', 'category_name', 'period_type', 'amount',
            'start_date', 'end_date', 'rollover_enabled',
            'spent', 'remaining', 'percent_used', 'effective_amount', 
            'rollover_amount', 'rollover_from',
        ]
    def _get_spent(self,obj):
        total=Transaction.objects.filter(
            user=obj.user,
            category=obj.category,
            transaction_type='expense',
            date__gte=obj.start_date,
            date__lte=obj.end_date,
        ).aggregate(total=Sum('amount'))['total']
        return total or 0

    def _get_rollover_info(self,obj):
        if not obj.rollover_enabled:
            return 0, None
        previous = Budget.objects.filter(
            user=obj.user,
            category=obj.category,
            period_type=obj.period_type,
            end_date__lt=obj.start_date,
        ).order_by('-end_date').first()
        if not previous:
            return 0, None
        prev_stats = self._stats(previous)
        leftover = prev_stats['effective'] - prev_stats['spent']
        if leftover <= 0:
            return 0, None
        return leftover, previous

    def get_effective_amount(self,obj):
        return self._stats(obj)['effective']

    def get_spent(self,obj):
        return self._stats(obj)['spent']

    def get_remaining(self,obj):
        stats=self._stats(obj)
        return stats['effective']-stats['spent']

    def get_percent_used(self,obj):
        stats=self._stats(obj)
        if stats['effective'] == 0:
            return 0
        return round((stats['spent']/stats['effective'])*100,1)

    def get_rollover_amount(self,obj):
        return self._stats(obj)['rollover']

    def get_rollover_from(self,obj):
        previous = self._stats(obj)['previous']
        return previous.start_date if previous else None

    def validate_category(self,value):
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid category")
        return value

    def _stats(self, obj):
        if not hasattr(self, '_stats_cache'):
            self._stats_cache = {}

        if obj.pk not in self._stats_cache:
            spent = self._get_spent(obj)
            rollover, previous = self._get_rollover_info(obj)
            effective = obj.amount + rollover

            self._stats_cache[obj.pk] = {
                'spent': spent,
                'rollover': rollover,
                'effective': effective,
                'previous' : previous,
            }

        return self._stats_cache[obj.pk]

    def validate(self,data):
        inst=self.instance
        start= data.get('start_date', inst.start_date if inst else None)
        end= data.get('end_date', inst.end_date if inst else None)
        category= data.get('category', inst.category if inst else None)
        period_type=data.get('period_type', inst.period_type if inst else None)

        if start and end and end < start:
            raise serializers.ValidationError("End date must be on or after start date.")

        if period_type == 'monthly' and start is not None and end is not None:
            print("MONTHLY CHECK RUNNING:", start, end)
            if start.year != end.year or start.month != end.month:
                raise serializers.ValidationError(
                    "A monthly budget must stay within one calendar month."
                )

            if start.day != 1:
                raise serializers.ValidationError(
                    "A monthly budget must start on the first day of the month."
                )

            last_day = calendar.monthrange(start.year, start.month)[1]

            if end.day != last_day:
                raise serializers.ValidationError(
                    "A monthly budget must end on the last day of the month."
                )

        if start and end and category and period_type:
            overlapping=Budget.objects.filter(
                user=self.context['request'].user,
                category=category,
                period_type=period_type,
                start_date__lte=end,
                end_date__gte=start,
            )
            if inst:
                overlapping=overlapping.exclude(pk=inst.pk)
            if overlapping.exists():
                raise serializers.ValidationError("A budget for this category and period type already covers these dates.")
        return data

    