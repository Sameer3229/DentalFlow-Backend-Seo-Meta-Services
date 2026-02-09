from django.db import models

class UserType(models.IntegerChoices):
    USER = 1, "User"
    ADMIN = 2, "Admin"