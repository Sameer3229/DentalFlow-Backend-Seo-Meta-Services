from django.urls import path,include 
from rest_framework.routers import DefaultRouter
from .views import TopicViewSet, GenerateContentViewSet


srouter = DefaultRouter()


router = DefaultRouter()
router.register("topics", TopicViewSet, basename="topics")
router.register("generate", GenerateContentViewSet, basename="generate")


urlpatterns = [
    path('', include(router.urls)),
]

