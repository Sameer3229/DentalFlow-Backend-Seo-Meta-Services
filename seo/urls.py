from django.urls import path,include 
from rest_framework.routers import DefaultRouter
from seo.views import SERankingKeywordViewSet


seo_router = DefaultRouter()
seo_router.register(r'keywords', SERankingKeywordViewSet, basename='keywords')


urlpatterns = [
    path('', include(seo_router.urls)),
]

