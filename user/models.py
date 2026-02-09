import uuid
from django.db import models
from django.utils import timezone
from core.choices import UserType
from user.manager import UserManager
from core.base_model import BaseModel
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import FileExtensionValidator

class User(AbstractBaseUser):
    """
    Custom user model using email instead of username.
    Includes personal info, user role, phone number, and status.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Optional phone number")
    role = models.SmallIntegerField(choices=UserType.choices, default=UserType.USER)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30,blank=True,null=True)
    username = None
    is_active = models.BooleanField(default=False)
    profile_image = models.ImageField(
        upload_to="user/profile/",
        default="user/profile/default.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", ".jpg", "jpeg", "png", "webp"]
            )
        ],
        verbose_name="Profile Image",
        blank=True,
        null=True,
    )

    objects = UserManager()

    password_reset_otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=200, blank=True, null=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.id}----{self.phone}--{self.first_name}--{self.profile_image}--{self.email} ({self.role})"

    def is_otp_expired(self):
        if not self.otp_created_at:
            return True
        return (timezone.now() - self.otp_created_at).total_seconds() > 600  # 10 min expiry


class UserWhitelistToken(BaseModel):
    """
    Stores whitelist of user tokens for active sessions.
    Includes token, refresh token, and login metadata.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tokens')
    access_token_fingerprint = models.TextField()
    refresh_token_fingerprint = models.TextField()
    login_info = models.JSONField()

    def __str__(self):
        return f"User--{self.user.email}--login--info"
