from passlib.hash import django_pbkdf2_sha256 as handler
from user.models import User
from core.utils import check_password_requirements
from core.choices import UserType
from admin_side.models import Package,PackageFeature,CartFeature,Feature
from rest_framework.serializers import(
    ModelSerializer,
    CharField,
    ValidationError,
    SerializerMethodField
)



class AdminRegistrationSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','phone','password','role','is_active']

    def validate_role(self, role):
        if role != UserType.ADMIN:
            raise ValidationError("Only Admin role is allowed for registration.")
        return role

    def validate_password(self,password):
        return handler.hash(password)


class AdminLoginSerializer(ModelSerializer):
    email = CharField()
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email','password']

    def validate(self, attrs):

        email = attrs.get('email')
        password = attrs.get('password')

        user = User.objects.filter(email=email).first()

        if not user:
            raise ValidationError("Email not found . . .")

        verify_pass = handler.verify(password,user.password)

        if not verify_pass:
            raise ValidationError("wrong password")

        attrs["user"] = user

        return attrs

class GetAdminProfileSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','phone','role','profile_image']


class UpdateAdminProfileSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','phone','role','profile_image']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)

        instance.save()
        return instance
    
class PackageFeatureSerializer(ModelSerializer):
    class Meta:
        model = PackageFeature
        fields = ["id", "name"]


class CreatePackageSerializer(ModelSerializer):
    features = PackageFeatureSerializer(many=True)

    class Meta:
        model = Package
        fields = ["id", "name", "description", "price_per_month", "is_popular", "features"]

    def create(self, validated_data):
        features_data = validated_data.pop("features", [])
        admin = self.context["request"].user  # logged-in admin

        # Create base package
        package = Package.objects.create(admin=admin, **validated_data)

        # Add its own features
        for feature in features_data:
            PackageFeature.objects.create(package=package, **feature)

        # Add features from lower-tier packages
        if package.name == "professional":
            basic_pkg = Package.objects.filter(name="basic", admin=admin).first()
            if basic_pkg:
                for f in basic_pkg.features.all():
                    PackageFeature.objects.create(package=package, name=f.name)

        elif package.name == "premium":
            basic_pkg = Package.objects.filter(name="basic", admin=admin).first()
            professional_pkg = Package.objects.filter(name="professional", admin=admin).first()

            for pkg in [basic_pkg, professional_pkg]:
                if pkg:
                    for f in pkg.features.all():
                        PackageFeature.objects.create(package=package, name=f.name)

        return package


class GetAllPackageSerializer(ModelSerializer):
    features = PackageFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Package
        fields = ["id", "name", "description", "price_per_month", "is_popular", "features"]

class FeatureCartItemSerializer(ModelSerializer):
    class Meta:
        model = CartFeature
        fields = ['id', 'name']


class FeatureSerializer(ModelSerializer):
    cart = FeatureCartItemSerializer(many=True)

    class Meta:
        model = Feature
        fields = ["id", "name", "description", "cart"]

    def create(self, validated_data):
        cart_data = validated_data.pop('cart', [])
        admin = self.context['request'].user

        feature = Feature.objects.create(admin=admin, **validated_data)

        for cart_item in cart_data:
            cart_obj, _ = CartFeature.objects.get_or_create(**cart_item)
            feature.cart.add(cart_obj)

        return feature

