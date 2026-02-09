from django.contrib import admin
from user.models import User,UserWhitelistToken

admin.site.register(User)
admin.site.register(UserWhitelistToken)
