from passlib.hash import django_pbkdf2_sha256 as handler
from user.models import User
from core.utils import check_password_requirements
from core.choices import UserType
from admin_side.models import Package,PackageFeature,UserPackage
from admin_side.models import Feature, CartFeature
from rest_framework.serializers import(
    Serializer,
    ModelSerializer,
    EmailField,
    CharField,
    ValidationError,
    SerializerMethodField,
    BooleanField
)



class UserRegistrationSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','phone','password','role','is_active']

    def validate_role(self, role):
        if role != UserType.USER:
            raise ValidationError("Only founder role is allowed for registration.")
        return role

    def validate_password(self,password):
        return handler.hash(password)


class UserLoginSerializer(ModelSerializer):
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

class GetUserProfileSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','phone','role','profile_image']


class UpdateProfileSerializer(ModelSerializer):

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

class GetAllPackageSerializer(ModelSerializer):
    features = SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "description",
            "price_per_month",
            "is_popular",
            "features"
        ]

    def get_features(self, obj):
        current_features = list(obj.features.values_list("name", flat=True))
        name = obj.name.lower()

        if name == "professional":
            basic_pkg = Package.objects.filter(name__iexact="basic", admin=obj.admin).first()
            if basic_pkg:
                basic_features = set(basic_pkg.features.values_list("name", flat=True))
                current_features = [f for f in current_features if f not in basic_features]
            current_features = ["Everything in Basic", *current_features]

        elif name == "premium":
            prof_pkg = Package.objects.filter(name__iexact="professional", admin=obj.admin).first()
            if prof_pkg:
                prof_features = set(prof_pkg.features.values_list("name", flat=True))
                current_features = [f for f in current_features if f not in prof_features and f != "Everything in Professional"]
            current_features = ["Everything in Professional", *current_features]

        current_features = list(dict.fromkeys(current_features))

        return current_features

    # def get_features(self, obj):
    #     current_features = list(obj.features.values_list("name", flat=True))
    #     name = obj.name.lower()

    #     if name == "professional":
    #         basic_pkg = Package.objects.filter(name="basic", admin=obj.admin).first()
    #         if basic_pkg:
    #             basic_features = set(basic_pkg.features.values_list("name", flat=True))
    #             current_features = [f for f in current_features if f not in basic_features]
    #         return ["Everything in Basic", *current_features]

    #     elif name == "premium":
    #         prof_pkg = Package.objects.filter(name="professional", admin=obj.admin).first()
    #         if prof_pkg:
    #             prof_features = set(prof_pkg.features.values_list("name", flat=True))
    #             current_features = [f for f in current_features if f not in prof_features]
    #         return ["Everything in Professional", *current_features]
    #     return current_features


class GetAllSubScription(ModelSerializer):
    package_name = SerializerMethodField()
    package_price = SerializerMethodField()

    class Meta:
        model = UserPackage
        fields = ['id','user','package','package_name','package_price','start_date','end_date','is_active','payment_status']
        read_only_field = ['user']

    def get_package_name(self,obj):
        return obj.package.name
    
    def get_package_price(self,obj):
        return obj.package.price_per_month
    

class SendOTPSerializer(Serializer):
    email = EmailField()

class VerifyOTPSerializer(Serializer):
    email = EmailField()
    otp = CharField(max_length=6)

class ResetPasswordSerializer(Serializer):
    email = EmailField()
    new_password = CharField(min_length=6, write_only=True)

class FeatureCartItemSerializer(ModelSerializer):
    class Meta:
        model = CartFeature
        fields = ['id', 'name']

class FeatureSerializer(ModelSerializer):
    cart = FeatureCartItemSerializer(many=True)  

    class Meta:
        model = Feature
        fields = ["id", "name", "description", "cart"]


class PackageSerializer(ModelSerializer):
    has_bought = BooleanField(read_only=True) 
    class Meta:
        model = Package
        fields = ['id', 'name', 'description', 'price_per_month', 'is_popular', 'stripe_product_id', 'stripe_price_id_dkk', 'stripe_price_id', 'has_bought']


class PackageDetailSerializer(ModelSerializer):
    class Meta:
        model = Package
        fields = (
            "id",
            "name",
            "description",
            "price_per_month",
            "is_popular",
        )


class UserSubscriptionListSerializer(ModelSerializer):
    package = PackageDetailSerializer(read_only=True)

    class Meta:
        model = UserPackage
        fields = (
            "id",
            "is_active",
            "status",
            "current_period_start",
            "current_period_end",
            "stripe_subscription_id",
            "package",
        )
