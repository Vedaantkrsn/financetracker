from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, CategoryViewSet

router = DefaultRouter()
router.register('accounts', AccountViewSet, basename='account')
router.register('categories', CategoryViewSet, basename='category')

urlpatterns = router.urls