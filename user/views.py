import uuid
import stripe
from django.core.mail import send_mail
from random import randint
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from user.models import User
from core.token import (
    UserGenerateToken,
    user_delete_token
)
from core.helpers import(
    handle_serializer_exception
)
from core.permission import(
    UserAuthenticated
)
from admin_side.models import Package,UserPackage,Feature
from django.conf import settings
from core.choices import UserType
from user.serializer import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    GetUserProfileSerializer,
    UpdateProfileSerializer,
    GetAllPackageSerializer,
    GetAllSubScription,
    SendOTPSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
    FeatureSerializer,
    PackageSerializer,
    UserSubscriptionListSerializer

)

stripe.api_key = settings.STRIPE_SECRET_KEY

class Auth(ModelViewSet):

    @action(detail=False, methods=['POST'])
    def signup(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save() 
                access_token, refresh_token, user = UserGenerateToken(user=user, request=request)

                user_data = {
                    "id": str(user.id),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "role": user.role,
                    "phone":user.phone,
                }

                return Response({
                    "status": True,
                    "message": "Account Created and Logged in Successfully!",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "data": user_data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": False,
                "message": handle_serializer_exception(serializer)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def login(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                if user.role == UserType.USER:
                    access_token, refresh_token, user = UserGenerateToken(user=user, request=request)
                    user_data = {
                        "id": str(user.id),
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "role": user.role,
                        "phone":user.phone,
                    }

                    return Response({
                        "status": True,
                        "message": "Login successful",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "data": user_data
                    }, status=status.HTTP_200_OK)

                return Response({
                    "status": False,
                    "message": "Only users are allowed to login here."
                }, status=status.HTTP_403_FORBIDDEN)

            return Response({
                "status": False,
                "message": handle_serializer_exception(serializer)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetViewSet(ModelViewSet):

    @action(detail=False, methods=['POST'])
    def send_otp(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"status": False, "message": "Email not registered."}, status=status.HTTP_400_BAD_REQUEST)

            otp = str(randint(100000, 999999))
            user.password_reset_otp = otp
            user.otp_created_at = timezone.now()
            user.save()

            send_mail(
                "Your OTP for Password Reset",
                f"Your OTP is: {otp}",
                "khan.245lala@gmail.com",
                [email],
            )

            return Response({"status": True, "message": "OTP sent to your email."}, status=status.HTTP_200_OK)

        return Response({"status": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"status": False, "message": "Invalid email or OTP."}, status=status.HTTP_400_BAD_REQUEST)

            if user.password_reset_otp != otp or user.is_otp_expired():
                return Response({"status": False, "message": "OTP expired or invalid."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"status": True, "message": "OTP verified successfully."}, status=status.HTTP_200_OK)

        return Response({"status": False, "message": handle_serializer_exception(serializer)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"status": False, "message": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST)


            user.set_password(new_password)
            user.password_reset_otp = None
            user.otp_created_at = None
            user.save()

            return Response({"status": True, "message": "Password reset successfully."}, status=status.HTTP_200_OK)

        return Response({"status": False, "message": handle_serializer_exception(serializer)}, status=status.HTTP_400_BAD_REQUEST)



class UserProfile(ModelViewSet):

    @action(detail=False,methods=['GET'],permission_classes=[UserAuthenticated])
    def profile(self,request):

        try:
            user = request.user

            serializer = GetUserProfileSerializer(user)

            return Response ({
                "status":True,
                "data":serializer.data,
            },status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,methods=['PATCH'],permission_classes=[UserAuthenticated])
    def update_profile(self,request):
        try:
            user = request.user
            serializer = UpdateProfileSerializer(user,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response ({
                    "status":True,
                    "data":serializer.data,
                },status=status.HTTP_200_OK)
            return Response({"status":False,"message":handle_serializer_exception(serializer)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PackageView(ModelViewSet):
    """User-side Package View"""

    @action(detail=False, methods=['GET'])
    def all_features(self, request):
        try:
            features = Feature.objects.all().order_by('-created_at')
            serializer = FeatureSerializer(features, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=200)
        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=400)

    @action(detail=False, methods=['GET'])
    def get_all_packages(self, request):
        """Fetch all available packages with features"""
        try:
            packages = Package.objects.prefetch_related('features').order_by('price_per_month')
            serializer = GetAllPackageSerializer(packages, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching packages: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
    def create_subscription(self, request):
        user = request.user
        package_id = request.data.get("package_id")
        if not package_id:
            return Response({"status": False, "message": "package_id is required"}, status=400)

        package = get_object_or_404(Package, id=package_id)

        if not getattr(user, "stripe_customer_id", None):
            customer = stripe.Customer.create(email=user.email, name=f"{user.first_name} {user.last_name}")
            user.stripe_customer_id = customer.id
            user.save()
        else:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)

        user_package = UserPackage.objects.create(
            user=user,
            package=package,
            stripe_customer_id=customer.id,
            status="pending",
            is_active=False
        )

        metadata = {
            "user_id": str(user.id),
            "user_package_id": str(user_package.id),
            "package_id": str(package.id),
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}"
        }

        origin = request.META.get("HTTP_ORIGIN", "http://localhost:8000")
        success_url = f"{origin}/success/?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin}/cancel/"

        if not package.stripe_price_id_dkk:
            return Response({"status": False, "message": "DKK price ID is missing for this package"}, status=400)

        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{"price": package.stripe_price_id_dkk, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            subscription_data={"metadata": metadata},
            allow_promotion_codes=True,
            currency="dkk" 
        )

        return Response({"status": True, "checkout_url": checkout_session.url}, status=200)

    

    @method_decorator(csrf_exempt, name='dispatch')
    @action(detail=False, methods=['POST'])
    def stripe_webhook(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({"error": "Invalid payload or signature"}, status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            subscription_id = session.get("subscription")
            customer_id = session.get("customer")
            metadata = session.get("metadata", {})

            user_package = get_object_or_404(UserPackage, id=metadata.get("user_package_id"))

            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                cps = subscription.get("current_period_start")
                cpe = subscription.get("current_period_end")

                user_package.current_period_start = datetime.fromtimestamp(cps, tz=timezone.utc) if cps else timezone.now()
                user_package.current_period_end = datetime.fromtimestamp(cpe, tz=timezone.utc) if cpe else timezone.now() + relativedelta(months=1)

                user_package.is_active = True
                user_package.status = "active"
                user_package.stripe_subscription_id = subscription_id
                user_package.stripe_customer_id = customer_id
                user_package.save()

        elif event["type"] == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            currency = invoice.get("currency") 
            subscription_id = invoice.get("subscription")
            customer_id = invoice.get("customer")
            metadata = invoice.get("metadata", {})

            user_package = get_object_or_404(UserPackage, id=metadata.get("user_package_id"))

            subscription = stripe.Subscription.retrieve(subscription_id)

            cps = subscription.get("current_period_start")
            cpe = subscription.get("current_period_end")

            user_package.current_period_start = datetime.fromtimestamp(cps, tz=timezone.utc)
            user_package.current_period_end = datetime.fromtimestamp(cpe, tz=timezone.utc)

            user_package.is_active = True
            user_package.status = "active"
            user_package.save()

        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            user_package = get_object_or_404(UserPackage, stripe_subscription_id=subscription.id)

            if subscription["status"] == "active":
                user_package.is_active = True
                user_package.status = "active"
            elif subscription["status"] == "canceled":
                user_package.is_active = False
                user_package.status = "canceled"

            user_package.save()

        return Response({"status": "success"}, status=200)


    @action(detail=False,methods=["GET"],permission_classes=[UserAuthenticated])
    def subscriptions(self,request):
        user = request.user

        purchased_package_ids = UserPackage.objects.filter(
            user=user, is_active=True).values_list('package_id', flat=True)

        available_packages = Package.objects.filter(id__in=purchased_package_ids)

        packages_with_bought_info = []
        for package in available_packages:
            package_data = PackageSerializer(package).data
            package_data['has_bought'] = package.has_bought_by_user(user)
            packages_with_bought_info.append(package_data)

        return Response({
            "status": True,
            "message": "Available packages fetched successfully",
            "packages": packages_with_bought_info
        })

    @action(detail=False, methods=["GET"], permission_classes=[UserAuthenticated])
    def my_subscriptions(self, request):
        subscriptions = (
            UserPackage.objects
            .filter(user=request.user)
            .select_related("package")
            .prefetch_related("package__features")
        )

        serializer = UserSubscriptionListSerializer(
            subscriptions,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "status": True,
                "message": "User subscriptions fetched successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK
        )

#stripe checkout old code 

# @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
#     def stripe_checkout(self, request):
#         package_id = request.data.get('package_id')
#         user = request.user

#         try:
#             package = Package.objects.get(id=package_id)
#         except Package.DoesNotExist:
#             return Response(
#                 {"status": False, "message": "Package not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         try:
#             origin = request.META.get('HTTP_ORIGIN')

#             success_url = f"{origin}/success?session_id={{CHECKOUT_SESSION_ID}}"
#             cancel_url = f"{origin}/failed"

#             checkout_session = stripe.checkout.Session.create(
#                 payment_method_types=['card'],
#                 line_items=[{
#                     'price_data': {
#                         'currency': 'usd',
#                         'product_data': {
#                             'name': package.name,
#                             'description': package.description,
#                         },
#                         'unit_amount': int(package.price_per_month * 100),
#                     },
#                     'quantity': 1,
#                 }],
#                 mode='payment',
#                 success_url=success_url,
#                 cancel_url=cancel_url,
#                 metadata={
#                     "user_id": str(user.id),
#                     "package_id": str(package.id)
#                 }
#             )

#             return Response({
#                 "status": True,
#                 "checkout_url": checkout_session.url
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response(
#                 {"status": False, "message": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


#     @method_decorator(csrf_exempt)
#     @action(detail=False, methods=["POST"])
#     def stripe_webhook(self, request):
#         payload = request.body
#         sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
#         event = None

#         try:
#             event = stripe.Webhook.construct_event(
#                 payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
#             )
#         except ValueError:
#             return Response({'status': False, 'message': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
#         except stripe.error.SignatureVerificationError:
#             return Response({'status': False, 'message': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

#         if event['type'] == 'checkout.session.completed':
#             session = event['data']['object']
#             user_id = session['metadata'].get('user_id')
#             package_id = session['metadata'].get('package_id')
#             try:
#                 user_uuid = uuid.UUID(user_id)
#                 package_uuid = uuid.UUID(package_id)
#             except (ValueError, TypeError):
#                 return Response({'status': False, 'message': 'Invalid user_id or package_id in metadata'}, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 user = User.objects.get(id=user_uuid)
#                 package = Package.objects.get(id=package_uuid)
#             except (User.DoesNotExist, Package.DoesNotExist):
#                 return Response({'status': False, 'message': 'User or Package not found'}, status=status.HTTP_404_NOT_FOUND)

#             end_date = timezone.now() + timedelta(days=30)

#             UserPackage.objects.update_or_create(
#                 user=user,
#                 package=package,
#                 defaults={
#                     'start_date': timezone.now(),
#                     'end_date': end_date,
#                     'is_active': True,
#                     'payment_status': 'paid'
#                 }
#             )

#         return Response({'status': True, 'message': 'Webhook received'}, status=status.HTTP_200_OK)






#docker









    
    