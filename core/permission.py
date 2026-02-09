from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed, APIException
from core.choices import UserType
from user.models import User, UserWhitelistToken
import jwt
from django.conf import settings


class UserAuthenticated(BasePermission):
    """
    Allows access only to authenticated users with role 'User'.
    """

    def has_permission(self, request, view):
        try:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if not auth_header.startswith("Bearer "):
                raise AuthenticationFailed("Invalid token header")

            token = auth_header[7:]
            decoded_token = jwt.decode(token, str(settings.FOUNDER_JWT_SECRET), algorithms=["HS256"])

            user = User.objects.filter(id=decoded_token["id"], role=UserType.USER).first()
            if not user:
                raise AuthenticationFailed("User not found")

            if not UserWhitelistToken.objects.filter(user=user, access_token_fingerprint=token).exists():
                raise AuthenticationFailed("Token Expired")

            request.user = user
            return True

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed({"status": False, "error": "Session expired!"})
        except jwt.DecodeError:
            raise AuthenticationFailed({"status": False, "error": "Invalid token!"})
        except Exception as e:
            raise AuthenticationFailed({"status": False, "error": str(e)})



class AdminAuthenticated(BasePermission):
    """
    Allows access only to authenticated users with role 'Admin'.
    """

    def has_permission(self, request, view):
        try:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if not auth_header.startswith("Bearer "):
                raise AuthenticationFailed("Invalid token header")

            token = auth_header[7:]
            decoded_token = jwt.decode(token, str(settings.ADMIN_JWT_SECRET), algorithms=["HS256"])

            user = User.objects.filter(id=decoded_token["id"], role=UserType.ADMIN).first()
            if not user:
                raise AuthenticationFailed("Admin not found")

            if not UserWhitelistToken.objects.filter(user=user, access_token_fingerprint=token).exists():
                raise AuthenticationFailed("Token Expired")

            request.user = user
            return True

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed({"status": False, "error": "Session expired!"})
        except jwt.DecodeError:
            raise AuthenticationFailed({"status": False, "error": "Invalid token!"})
        except Exception as e:
            raise AuthenticationFailed({"status": False, "error": str(e)})


class NeedLogin(APIException):
    status_code = 401
    default_detail = {"status": False, "message": "Unauthorized"}
    default_code = "not_authenticated"