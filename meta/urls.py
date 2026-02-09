from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacebookManagerViewSet

# Router banana
router = DefaultRouter()
router.register(r'fb-manager', FacebookManagerViewSet, basename='fb-manager')

urlpatterns = [
    path('', include(router.urls)),
]