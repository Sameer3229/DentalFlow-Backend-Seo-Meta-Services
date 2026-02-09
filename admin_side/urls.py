from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin_side.views import (
    Auth,
    AdminProfile,
    PackageAPI,
    FeatureAPI
)

admin_router = DefaultRouter()

admin_router.register(r'admin-auth', Auth, basename='admin-auth')
admin_router.register(r'admin-profile', AdminProfile, basename='admin-profile')
admin_router.register(r'admin-packages', PackageAPI, basename='admin-packages')
admin_router.register(r'admin-feature', FeatureAPI, basename='admin-feature')

urlpatterns = [
    path('', include(admin_router.urls)),
]
