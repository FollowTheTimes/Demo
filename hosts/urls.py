from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CityViewSet, DatacenterViewSet, HostViewSet

router = DefaultRouter()
router.register(r'cities', CityViewSet)
router.register(r'datacenters', DatacenterViewSet)
router.register(r'hosts', HostViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
