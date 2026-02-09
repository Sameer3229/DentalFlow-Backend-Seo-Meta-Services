from django.contrib import admin
from .models import FacebookProfile

@admin.register(FacebookProfile)
class FacebookProfileAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'page_name', 'page_id', 'updated_at')
    search_fields = ('user__username', 'page_name', 'page_id')
    list_filter = ('updated_at',)
    readonly_fields = ('updated_at',)