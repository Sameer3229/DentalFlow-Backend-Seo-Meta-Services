from django.contrib import admin
from admin_side.models import Package,PackageFeature,UserPackage,Feature,CartFeature

admin.site.register(Package)
admin.site.register(PackageFeature)
admin.site.register(UserPackage)
admin.site.register(CartFeature)
admin.site.register(Feature)