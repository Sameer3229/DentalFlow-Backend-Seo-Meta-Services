from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.token import (
    UserGenerateToken,
    user_delete_token
)
from core.helpers import(
    handle_serializer_exception
)
from admin_side.models import Package,PackageFeature,Feature
from core.permission import(
    AdminAuthenticated
)
from core.choices import UserType
from admin_side.serializer import (
    AdminRegistrationSerializer,
    AdminLoginSerializer,
    GetAdminProfileSerializer,
    UpdateAdminProfileSerializer,
    PackageFeatureSerializer,
    CreatePackageSerializer,
    GetAllPackageSerializer,
    FeatureSerializer
)


class Auth(ModelViewSet):

    @action(detail=False, methods=['POST'])
    def signup(self, request):
        try:
            serializer = AdminRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save() 
                access_token, refresh_token, user = UserGenerateToken(user=user, request=request)

                user_data = {
                    "id": str(user.id),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "role": user.role,
                    "phone":user.phone,
                }

                return Response({
                    "status": True,
                    "message": "Account Created and Logged in Successfully!",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "data": user_data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": False,
                "message": handle_serializer_exception(serializer)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def login(self, request):
        try:
            serializer = AdminLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                if user.role == UserType.ADMIN:
                    access_token, refresh_token, user = UserGenerateToken(user=user, request=request)
                    user_data = {
                        "id": str(user.id),
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "role": user.role,
                        "phone":user.phone,
                    }

                    return Response({
                        "status": True,
                        "message": "Login successful",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "data": user_data
                    }, status=status.HTTP_200_OK)

                return Response({
                    "status": False,
                    "message": "Only users are allowed to login here."
                }, status=status.HTTP_403_FORBIDDEN)

            return Response({
                "status": False,
                "message": handle_serializer_exception(serializer)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)



class AdminProfile(ModelViewSet):

    @action(detail=False,methods=['GET'],permission_classes=[AdminAuthenticated])
    def profile(self,request):

        try:
            user = request.user

            serializer = GetAdminProfileSerializer(user)

            return Response ({
                "status":True,
                "data":serializer.data,
            },status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,methods=['PATCH'],permission_classes=[AdminAuthenticated])
    def update_profile(self,request):
        try:
            user = request.user
            serializer = UpdateAdminProfileSerializer(user,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response ({
                    "status":True,
                    "data":serializer.data,
                },status=status.HTTP_200_OK)
            return Response({"status":False,"message":handle_serializer_exception(serializer)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PackageAPI(ModelViewSet):
    """API for managing Packages and their Features"""

    @action(detail=False, methods=['GET'], permission_classes=[AdminAuthenticated])
    def all_packages(self, request):
        """Fetch all packages with their features"""
        try:
            packages = Package.objects.prefetch_related('features').order_by('-created_at')
            serializer = GetAllPackageSerializer(packages, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching packages: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], permission_classes=[AdminAuthenticated])
    def get_package(self, request):
        """Fetch single package by package_id (from query params)"""
        try:
            package_id = request.query_params.get('package_id')
            if not package_id:
                return Response({
                    "status": False,
                    "message": "package_id is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            package = Package.objects.prefetch_related('features').get(id=package_id)
            serializer = GetAllPackageSerializer(package)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Package.DoesNotExist:
            return Response({
                "status": False,
                "message": "Package not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching package: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'], permission_classes=[AdminAuthenticated])
    def create_package(self, request):
        """Create a new package"""
        try:
            serializer = CreatePackageSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                serializer.save()  # admin auto-adds from serializer
                return Response({
                    "status": True,
                    "data": serializer.data,
                    "message": "Package created successfully."
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": False,
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error creating package: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['PATCH'], permission_classes=[AdminAuthenticated])
    def update_package(self, request):
        """Update package using package_id from query params"""
        try:
            package_id = request.query_params.get('package_id')
            if not package_id:
                return Response({
                    "status": False,
                    "message": "package_id is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            package = Package.objects.get(id=package_id)
            serializer = CreatePackageSerializer(package, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": True,
                    "data": serializer.data,
                    "message": "Package updated successfully."
                }, status=status.HTTP_200_OK)

            return Response({
                "status": False,
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Package.DoesNotExist:
            return Response({
                "status": False,
                "message": "Package not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error updating package: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['DELETE'], permission_classes=[AdminAuthenticated])
    def delete_package(self, request):
        """Delete package using package_id from query params"""
        try:
            package_id = request.query_params.get('package_id')
            if not package_id:
                return Response({
                    "status": False,
                    "message": "package_id is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            package = Package.objects.get(id=package_id)
            package.delete()

            return Response({
                "status": True,
                "message": "Package deleted successfully."
            }, status=status.HTTP_200_OK)

        except Package.DoesNotExist:
            return Response({
                "status": False,
                "message": "Package not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error deleting package: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


class FeatureAPI(ModelViewSet):
    """API for managing admin Features"""

    @action(detail=False, methods=['GET'], permission_classes=[AdminAuthenticated])
    def all_features(self, request):
        """Fetch all features of the logged-in admin"""
        try:
            admin = request.user
            features = Feature.objects.filter(admin=admin).order_by('-created_at')
            serializer = FeatureSerializer(features, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching features: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], permission_classes=[AdminAuthenticated])
    def get_feature(self, request):
        """Fetch a single feature by feature_id (from query params)"""
        try:
            feature_id = request.query_params.get('feature_id')
            if not feature_id:
                return Response({
                    "status": False,
                    "message": "feature_id is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            admin = request.user
            feature = Feature.objects.get(id=feature_id, admin=admin)
            serializer = FeatureSerializer(feature)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Feature.DoesNotExist:
            return Response({
                "status": False,
                "message": "Feature not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching feature: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'], permission_classes=[AdminAuthenticated])
    def create_feature(self, request):
        try:
            serializer = FeatureSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                feature = serializer.save()
                return Response({
                    "status": True,
                    "message": "Feature created successfully.",
                    "data": FeatureSerializer(feature).data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": False,
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error creating feature: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['PATCH'], permission_classes=[AdminAuthenticated])
    def update_feature(self, request):
        """Update a feature using feature_id from query params"""
        try:
            feature_id = request.query_params.get('feature_id')
            if not feature_id:
                return Response({
                    "status": False,
                    "message": "feature_id is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            admin = request.user
            feature = Feature.objects.get(id=feature_id, admin=admin)
            serializer = FeatureSerializer(feature, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": True,
                    "data": serializer.data,
                    "message": "Feature updated successfully."
                }, status=status.HTTP_200_OK)
            return Response({
                "status": False,
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Feature.DoesNotExist:
            return Response({
                "status": False,
                "message": "Feature not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error updating feature: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['DELETE'], permission_classes=[AdminAuthenticated])
    def delete_feature(self, request):
        """Delete a feature using feature_id from query params"""
        try:
            feature_id = request.query_params.get('feature_id')
            if not feature_id:
                return Response({
                    "status": False,
                    "message": "feature_id is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            admin = request.user
            feature = Feature.objects.get(id=feature_id, admin=admin)
            feature.delete()
            return Response({
                "status": True,
                "message": "Feature deleted successfully."
            }, status=status.HTTP_200_OK)
        except Feature.DoesNotExist:
            return Response({
                "status": False,
                "message": "Feature not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error deleting feature: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

#done