from django.db import models
from core.base_model import BaseModel
from user.models import User

class Package(BaseModel):
    PACKAGE_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('premium', 'Premium'),
    ]
    admin = models.ForeignKey(
        User,   
        on_delete=models.CASCADE,
        related_name="created_packages"
    )
    name = models.CharField(max_length=100, choices=PACKAGE_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=3)
    is_popular = models.BooleanField(default=False)  
    stripe_product_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_price_id_dkk = models.CharField(max_length=200, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.admin.email})" if hasattr(self.admin, 'email') else self.name
    
    def has_bought_by_user(self, user):
        return UserPackage.objects.filter(user=user, package=self, is_active=True).exists()




class PackageFeature(BaseModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="features")
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.package.name} - {self.name}"



class UserPackage(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="subscriptions")
    stripe_customer_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, default="incomplete")

    def __str__(self):
        return f"{self.user} - {self.package.name}"


class CartFeature(BaseModel):
    name = models.CharField(max_length=100)

class Feature(BaseModel):
    admin = models.ForeignKey(User,on_delete=models.CASCADE,related_name='features')
    cart = models.ManyToManyField(CartFeature, related_name='features')
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.admin.first_name} - {self.name}"

