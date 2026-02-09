from django.urls import path,include 
from rest_framework.routers import DefaultRouter
from user.views import(
    Auth,
    UserProfile,
    PackageView,
    PasswordResetViewSet
)

founder = DefaultRouter()
founder.register('user-auth',Auth,basename='user-auth')
founder.register('user-profile',UserProfile,basename='user-profile')
founder.register('user-packages',PackageView,basename='user-packages')
founder.register('user-reset',PasswordResetViewSet,basename='user-reset')

urlpatterns = [
    path('', include(founder.urls)),
]

