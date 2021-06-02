from core.viewsets.LedgerViewSet import LedgerViewSet
from core.viewsets.GroupViewSet import GroupViewSet
from core.viewsets.UserViewSet import UserViewSet
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'ledger', LedgerViewSet)


urlpatterns = [
    path('', include(router.urls))
]
