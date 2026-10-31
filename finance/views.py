from rest_framework import viewsets, permissions, generics, status
from .models import Account, Category, Transaction, Budget, RecurringTransaction
from django.contrib.auth.models import User
from .serializers import AccountSerializer, CategorySerializer, RegisterSerializer, TransactionSerializer, BudgetSerializer, RecurringSerializer
from rest_framework.permissions import AllowAny
from .filters import TransactionFilter
from rest_framework.response import Response
from decimal import Decimal, InvalidOperation
from rest_framework.decorators import action



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

    