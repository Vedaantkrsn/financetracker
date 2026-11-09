from rest_framework import viewsets, permissions, generics, status
from .models import Account, Category, Transaction, Budget, RecurringTransaction
from django.contrib.auth.models import User
from .serializers import AccountSerializer, CategorySerializer, RegisterSerializer, TransactionSerializer, BudgetSerializer, RecurringSerializer
from rest_framework.permissions import AllowAny
from .filters import TransactionFilter
from rest_framework.response import Response
from decimal import Decimal, InvalidOperation
from rest_framework.decorators import action
from decimal import Decimal
from django.db.models import Sum,Count,Min,Max
from django.db.models.functions import TruncDay,TruncMonth
from rest_framework.views import APIView



class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        category=self.get_object()
        if category.transactions.exists():
            return Response(
                {'detail': 'This category is used by existing transactions and cannot be deleted. Deactivate it instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

class RegisterView(generics.CreateAPIView):
    queryset=User.objects.all()
    serializer_class=RegisterSerializer
    permission_classes=[AllowAny]

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class=BudgetSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RecurringTransactionViewSet(viewsets.ModelViewSet):
    serializer_class=RecurringSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user, 
            next_due_date=serializer.validated_data['start_date'],
        )

    @action(detail=True, methods=['post'], url_path='post')
    def post_now(self, request, pk=None):
        item = self.get_object()
        if not item.is_active:
            return Response({'detail': 'This item is paused or finished.'}, status=400)
        amount = request.data.get('amount')
        if amount in (None, ''):
            amount = None
        else:
            try:
                amount = Decimal(str(amount))
            except InvalidOperation:
                return Response({'detail': 'Invalid amount.'}, status=400)
            if amount <= 0:
                return Response({'detail': 'Amount must be positive.'}, status=400)
        item.post_transaction(amount=amount)
        return Response(self.get_serializer(item).data)

    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        item = self.get_object()
        if not item.is_active:
            return Response({'detail': 'This item is paused or finished.'}, status=400)
        item.skip_period()
        return Response(self.get_serializer(item).data)


class ReportView(APIView):
    permission_classes=[permissions.IsAuthenticated]

    def get(self,request):
        base=Transaction.objects.filter(user=request.user, transaction_type__in=['income','expense'])
        filterset=TransactionFilter(request.query_params,queryset=base)
        if not filterset.is_valid():
          return Response(filterset.errors,status=400)
        qs=filterset.qs

        zero=Decimal('0')

        sums={
          row['transaction_type']:row['total']
          for row in qs.values('transaction_type').annotate(total=Sum('amount')).order_by()
        }
        income=sums.get('income',0)
        expenses=sums.get('expense',0)
        net=income-expenses
        savings_rate=round(net/income*100,1) if income > 0 else None

        by_category={'expense':[],'income':[]}
        category_rows=( 
            qs.values('transaction_type','category__id','category__name')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )
        for row in category_rows:
            kind=row['transaction_type']
            kind_total=expenses if kind=='expense' else income
            by_category[kind].append({
                'category_id':row['category__id'],
                'category':row['category__name'] or 'Uncategorized',
                'total':row['total'],
                'count':row['count'],
                'percent':round(row['total']/kind_total*100,1) if kind_total else 0,
            })

        accounts={}
        account_rows=(
            qs.values('account__id','account__name','transaction_type')
            .annotate(total=Sum('amount'))
            .order_by()
        )
        for row in account_rows:
            entry=accounts.setdefault(row['account__id'],{
                'account_id':row['account__id'],
                'account':row['account__name'],
                'income':zero,
                'expense':zero,
            })
            entry[row['transaction_type']]=row['total']

        cleaned=filterset.form.cleaned_data
        date_from,date_to=cleaned.get('date_from'), cleaned.get('date_to')
        if not (date_from and date_to):
            bounds=qs.aggregate(first=Min('date'),last=Max('date'))
            date_from=date_from or bounds['first']
            date_to=date_to or bounds['last']
        by_day=bool(date_from and date_to and (date_to-date_from).days <= 62)
        bucket=TruncDay('date') if by_day else  TruncMonth('date')

        periods = {}
        trend_rows = (
            qs.annotate(period=bucket)
            .values('period', 'transaction_type')
            .annotate(total=Sum('amount'))
            .order_by('period')
        )
        for row in trend_rows:
            entry = periods.setdefault(row['period'], {
                'period': row['period'], 'income': zero, 'expense': zero,
            })
            entry[row['transaction_type']] = row['total']
        trend = [{**p, 'net': p['income'] - p['expense']} for p in periods.values()]

        return Response({
            'range': {
                'date_from': date_from,
                'date_to': date_to,
                'granularity': 'day' if by_day else 'month',
            },
            'summary': {
                'income': income,
                'expenses': expenses,
                'net': net,
                'savings_rate': savings_rate,
                'transaction_count': qs.count(),
            },
            'by_category': by_category,
            'by_account': list(accounts.values()),
            'trend': trend,
        })
