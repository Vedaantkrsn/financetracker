from rest_framework import viewsets, permissions, generics, status
from .models import Account, Category, Transaction, Budget
from django.contrib.auth.models import User
from .serializers import AccountSerializer, CategorySerializer, RegisterSerializer, TransactionSerializer, BudgetSerializer
from rest_framework.permissions import AllowAny
from .filters import TransactionFilter
from rest_framework.response import Response



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
