import datetime
import jwt
from django.conf import settings
from rest_framework.response import Response
from user.models import UserWhitelistToken
from core.choices import UserType
from rest_framework.exceptions import AuthenticationFailed

def get_client_info(request):
    """
    Extract client IP and User-Agent from the request for tracking.
    """
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR')
        or request.META.get('REMOTE_ADDR')
    )
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')

    return {
        "ip": ip.split(',')[0].strip() if ip else 'unknown',
        "user_agent": user_agent,
    }

def get_jwt_secret_by_role(role):
    """
    Return the appropriate secret key based on the user role.
    """
    if role == UserType.USER:
        return settings.FOUNDER_JWT_SECRET
    elif role == UserType.ADMIN:
        return settings.ADMIN_JWT_SECRET
    else:
        raise Exception("Invalid role for JWT token")

def UserGenerateToken(user,request):
    """
    Generate access and refresh JWT tokens with role-based payload and secret key.
    """
    try:
        access_token_exp = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        refresh_token_exp = datetime.datetime.utcnow() + datetime.timedelta(days=30)

        # Common payload data   
        payload_common = {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "iat": datetime.datetime.utcnow(),
        }

        access_payload = {
            **payload_common,
            "exp": access_token_exp,
            "type": "access"
        }

        refresh_payload = {
            **payload_common,
            "exp": refresh_token_exp,
            "type": "refresh"
        }

        secret_key = get_jwt_secret_by_role(user.role)

        access_token = jwt.encode(access_payload, str(secret_key), algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, str(secret_key), algorithm="HS256")

        client_info = get_client_info(request)

        UserWhitelistToken.objects.create(
            user=user,
            access_token_fingerprint=access_token,
            refresh_token_fingerprint=refresh_token,
            login_info={
                "access_exp": str(access_token_exp),
                "refresh_exp": str(refresh_token_exp),
                "ip": client_info['ip'],
                "user_agent": client_info['user_agent'],
            }
        )
        return access_token, refresh_token,user

    except Exception as e:
        return {"status": False, "message": f"Error during generating tokens: {str(e)}"}




def user_delete_token(user, request):
    try:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Invalid token header")

        token = auth_header[7:]

        whitelist_token = UserWhitelistToken.objects.filter(
            user=user,
            access_token_fingerprint=token
        ).first()

        if whitelist_token:
            whitelist_token.delete()
        else:
            print("Token not found in whitelist.")
            return False

        return True

    except Exception as e:
        print("Logout error:", str(e))
        return False





    