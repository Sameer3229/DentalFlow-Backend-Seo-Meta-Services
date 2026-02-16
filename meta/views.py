from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.user import User as FBUser
from facebook_business.adobjects.adset import AdSet
import requests
import base64
import os
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adpreview import AdPreview
from datetime import datetime, timedelta
from django.contrib.auth.models import User  # Just to satisfy ModelViewSet queryset
import requests
from .models import FacebookProfile
from .serializers import *
from facebook_business.exceptions import FacebookRequestError
import pytz
from datetime import datetime, timedelta


class FacebookManagerViewSet(viewsets.ModelViewSet):
    """
    Ek hi ViewSet mein saari Facebook functionality handle hogi using @action.
    """
    queryset = User.objects.none()  # Abhi hum DB use nahi kr rhy, isliye empty queryset
    serializer_class = None         # Abhi serializer ki zaroorat nahi
    APP_ID = '852721637524289'
    APP_SECRET = '153b212ec134da245cfcc7e82510614e'
    # Ye URL same honi chahiye jo Meta Console mein "Valid OAuth Redirect URIs" mein hai
    # REDIRECT_URI = 'https://dentalflow.devssh.xyz/api/fb-manager/callback/'
    # REDIRECT_URI = 'https://dentalflownew.netlify.app/fb/callback/'
    REDIRECT_URI = 'http://localhost:8000/api/fb-manager/callback/'


    def get_fb_credentials(self, request):
        """Helper function to get App ID/Secret & Token"""
        return {
            'app_id': '852721637524289',
            'app_secret': '153b212ec134da245cfcc7e82510614e',
            'access_token': request.data.get('access_token')
        }
    
    @action(detail=False, methods=['get'])
    def get_login_url(self, request):
        """
        Frontend is API ko call karega taa k pata chale user ko kahan redirect karna hai.
        """
        # scope = 'email,pages_show_list,ads_management,ads_read,pages_read_engagement,business_management'
        # 'email' hata diya hai, ab ye error nahi dega
        scope = 'pages_show_list,ads_management,ads_read,pages_read_engagement,business_management'
        
        url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.APP_ID}&"
            f"redirect_uri={self.REDIRECT_URI}&"
            f"scope={scope}&"
            f"response_type=code"
        )
        return Response({"auth_url": url})
    
    # --- API 2: CODE SE TOKEN BANANA AUR SAVE KARNA ---
    @action(detail=False, methods=['post'])
    def handle_callback(self, request):
        """
        User login k baad 'code' le kar wapis ayega. Hum us code se token banayen gy
        aur Database mein save kar len gy.
        """
        code = request.data.get('code')
        if not code:
            return Response({"error": "Code is missing"}, status=400)

        # 1. Exchange Code for Access Token
        token_url = (
            f"https://graph.facebook.com/v18.0/oauth/access_token?"
            f"client_id={self.APP_ID}&"
            f"redirect_uri={self.REDIRECT_URI}&"
            f"client_secret={self.APP_SECRET}&"
            f"code={code}"
        )
        
        try:
            resp = requests.get(token_url).json()
            if 'access_token' not in resp:
                return Response({"error": "Failed to get token", "details": resp}, status=400)
            
            access_token = resp['access_token']

            # 2. Database mein Save karein
            user = request.user
            if user.is_anonymous: user = User.objects.first() # Testing hack

            # Save token to DB
            FacebookProfile.objects.update_or_create(
                user=user,
                defaults={'access_token': access_token}
            )

            return Response({"message": "Login Successful! Token Saved.", "status": "connected"})

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    # --- ACTION 1: Full Connection Test ---
    @action(detail=False, methods=['post'])
  
    def test_connection(self, request):
        # 1. Credentials
        app_id = '852721637524289'
        app_secret = '153b212ec134da245cfcc7e82510614e'
        token = request.data.get('access_token') or request.data.get('token')

        if not token:
            return Response({"error": "Access Token is required"}, status=400)

        FacebookAdsApi.init(app_id, app_secret, token)
        
        data = {
            "status": "checked",
            "pages": [],
            "ad_accounts": [],
            "debug_info": []
        }

        # --- STEP 1: General List Fetch (Jo pehle kar rahy thay) ---
        try:
            url = "https://graph.facebook.com/v18.0/me/accounts"
            params = {'access_token': token, 'fields': 'name,id,category,access_token,tasks'}
            resp = requests.get(url, params=params).json()
            
            if 'data' in resp:
                data['pages'].extend(resp['data'])
            else:
                data['debug_info'].append(f"List Fetch Empty: {resp}")

        except Exception as e:
            data['debug_info'].append(f"List Error: {str(e)}")

        # --- STEP 2: DIRECT TARGET FETCH (The Fix 🛠️) ---
        # Agar list khali hai, to hum seedha 'mo_elias_d' ki ID ko hit karein gy
        target_page_id = '112591256879208'
        
        # Check karein k kya ye page already list mein aa gaya? Agar nahi to fetch karein
        already_found = any(p['id'] == target_page_id for p in data['pages'])
        
        if not already_found:
            try:
                # Direct Page Call
                direct_url = f"https://graph.facebook.com/v18.0/{target_page_id}"
                direct_params = {'access_token': token, 'fields': 'name,id,access_token,category'}
                direct_resp = requests.get(direct_url, params=direct_params).json()
                
                if 'id' in direct_resp:
                    data['pages'].append({
                        "name": direct_resp.get('name'),
                        "id": direct_resp.get('id'),
                        "category": direct_resp.get('category'),
                        "source": "Direct Fetch (Granular Access)"
                    })
                    data['debug_info'].append("Success! Found page via Direct ID fetch.")
                else:
                    data['debug_info'].append(f"Direct Fetch Failed: {direct_resp}")
            except Exception as e:
                data['debug_info'].append(f"Direct Fetch Error: {str(e)}")

        # --- STEP 3: Ad Accounts ---
        try:
            me = FBUser(fbid='me')
            my_accounts = me.get_ad_accounts(fields=['name', 'account_id', 'currency'])
            for acc in my_accounts:
                data['ad_accounts'].append(acc.export_all_data())
        except Exception as e:
            data['debug_info'].append(f"Ad Account Error: {str(e)}")

        return Response(data)
    # --- ACTION 2: Get Only Pages ---
    @action(detail=False, methods=['get'])
    def get_my_pages(self, request):
        """
        Ye API Database se token uthayegi aur Facebook se Pages la kar degi.
        Frontend isy 'Dashboard' par dikhaye ga.
        """
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            # Database se Token nikalo
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected. Please login first."}, status=401)

        # Facebook se Pages mangwana
        try:
            # Pehle '/me/accounts' try karein
            url = "https://graph.facebook.com/v18.0/me/accounts"
            params = {'access_token': token, 'fields': 'name,id,category,tasks'}
            response = requests.get(url, params=params).json()
            
            pages_list = response.get('data', [])

            # Agar list khali hai (Granular access issue), to 'mo_elias_d' ko direct fetch karein
            if not pages_list:
                target_id = '112591256879208' # Client Page ID
                direct_url = f"https://graph.facebook.com/v18.0/{target_id}"
                direct_resp = requests.get(direct_url, params={'access_token': token, 'fields': 'name,id,category'}).json()
                if 'id' in direct_resp:
                    pages_list.append(direct_resp)

            return Response({"pages": pages_list})

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    # --- ACTION 3: Get Only Ad Accounts ---
    @action(detail=False, methods=['post'])
    def get_ad_accounts(self, request):
      
        app_id = '852721637524289'
        app_secret = '153b212ec134da245cfcc7e82510614e'

        # --- CHANGE 1: Token Database se lena ---
        user = request.user
        if user.is_anonymous: user = User.objects.first() # Testing hack

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected. Please login with Facebook first."}, status=400)
        
        # ----------------------------------------

        try:
            FacebookAdsApi.init(app_id, app_secret, token)
            me = FBUser(fbid='me')
            
            # Ad Accounts fetch karna
            accounts = me.get_ad_accounts(fields=['name', 'account_id', 'account_status', 'amount_spent', 'currency'])
            
            clean_data = [acc.export_all_data() for acc in accounts]
            return Response({"ad_accounts": clean_data})

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

    # @action(detail=False, methods=['post'])
    # def create_campaign(self, request):
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        ad_account_id = request.data.get('ad_account_id')
        campaign_name = request.data.get('name', 'New Campaign via API')
        objective = request.data.get('objective', 'OUTCOME_TRAFFIC')
        status = request.data.get('status', 'PAUSED')
        special_ad_categories = request.data.get('special_ad_categories', [])

        if not ad_account_id:
            return Response({"error": "Ad Account ID is required"}, status=400)

        try:
            account = AdAccount(ad_account_id)

            params = {
                'name': campaign_name,
                'objective': objective,
                'status': status,
                'special_ad_categories': special_ad_categories or ['NONE'],
                'buying_type': 'AUCTION',
                'is_adset_budget_sharing_enabled': False 
            }

            campaign = account.create_campaign(params=params)

            # --- ERROR FIX HUA YAHAN ---
            # Hum 'campaign['name']' ki bajaye variable 'campaign_name' use kar rahy hain
            return Response({
                "message": "Campaign Created Successfully!",
                "campaign_id": campaign['id'], 
                "campaign_name": campaign_name, # Fixed Line
                "objective": objective
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
#===============================================================================================
    @action(detail=False, methods=['post'])
    def create_campaign(self, request):
        
        # --- 1. Authentication ---
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "Facebook account not connected."}, status=400)
        
        # --- 2. Input Validation ---
        serializer = CampaignCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data

        special_cats = data.get('special_ad_categories', [])
        if not special_cats:
            special_cats = ['NONE'] 
        elif isinstance(special_cats, str):
            special_cats = [special_cats]

        # --- 3. Basic Parameters ---
        params = {
            'name': data['name'],
            'objective': data['objective'],
            'status': data['status'],
            'special_ad_categories': special_cats, # ✅ Corrected
            'buying_type': 'AUCTION', 
        }

        # --- FEATURE A: Campaign Spending Limit ---
        if data.get('spend_cap'):
            # Convert Dollars to Cents (10.00 -> 1000)
            params['spend_cap'] = int(data['spend_cap'] * 100)

        # --- FEATURE B: iOS 14+ Campaign ---
        if data.get('is_ios14_campaign'):
            # 1. Flag Enable
            params['is_skadnetwork_attribution'] = True
            
            # 2. Set App ID (Using the ID user provided)
            # Meta requires this structure for SKAdNetwork
            params['promoted_object'] = {
                'application_id': data['ios14_app_id'], 
                'object_store_url': f"https://itunes.apple.com/app/id{data['ios14_app_id']}"
            }

        # --- FEATURE C: CBO Logic (Existing) ---
        if data['is_cbo_enabled']:
            
            if data.get('daily_budget'):
                params['daily_budget'] = int(data['daily_budget'] * 100)
            
            if data.get('lifetime_budget'):
                params['lifetime_budget'] = int(data['lifetime_budget'] * 100)
            
            
            params['bid_strategy'] = data.get('bid_strategy', 'LOWEST_COST_WITHOUT_CAP')
        else:
            params['is_adset_budget_sharing_enabled'] = False
            
            
        try:
            
            print("🚀 Sending to Meta:", params)

            FacebookAdsApi.init(access_token=access_token)
            account = AdAccount(data['ad_account_id'])

            campaign = account.create_campaign(params=params)

            return Response({
                "message": "Campaign Created Successfully!",
                "campaign_id": campaign['id'],
                "name": data['name'],
                "objective": data['objective'],
                "status": "CREATED",
                "spend_cap_cents": params.get('spend_cap'),
                "is_ios14": params.get('is_skadnetwork_attribution', False)
            }, status=status.HTTP_201_CREATED)
        
        except FacebookRequestError as e:
            return Response({
                "error": "Meta API Error",
                "details": e.body() 
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({"error": "Internal Server Error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            


#===============================================================================================


    # @action(detail=False, methods=['post'])
    # def update_campaign(self, request):
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        # 1. Inputs (Jo jo user update karna chahta hai)
        campaign_id = request.data.get('campaign_id')
        new_name = request.data.get('name')
        new_status = request.data.get('status') # PAUSED, ACTIVE, ARCHIVED
        special_ad_categories = request.data.get('special_ad_categories') # List e.g. ['HOUSING']
        
        # Note: 'Objective' cannot be updated after creation via API.
        
        if not campaign_id:
            return Response({"error": "Campaign ID is required"}, status=400)

        try:
            campaign = Campaign(campaign_id)
            
            params = {}
            
            # 2. Sirf wo fields add karein jo user ne bheji hain
            if new_name:
                params['name'] = new_name
            
            if new_status:
                # Validation: Status sirf yehi 3 ho sakte hain
                if new_status not in ['ACTIVE', 'PAUSED', 'ARCHIVED']:
                     return Response({"error": "Invalid Status. Use ACTIVE, PAUSED or ARCHIVED"}, status=400)
                params['status'] = new_status
            
            if special_ad_categories:
                params['special_ad_categories'] = special_ad_categories

            # 3. Request Bhejen
            if params:
                campaign.remote_update(params=params)
                
                return Response({
                    "message": "Campaign Updated Successfully!", 
                    "campaign_id": campaign_id, 
                    "updated_fields": params
                })
            else:
                return Response({"message": "No changes provided to update."}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

#===============================================================================================
    @action(detail=False, methods=['get'])
    def get_campaigns(self, request):
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        ad_account_id = request.query_params.get('ad_account_id')

        if not ad_account_id:
            return Response({"error": "Ad Account ID is required"}, status=400)

        try:
            account = AdAccount(ad_account_id)
            
            # ✅ Change 1: Added 'spend_cap' field
            fields = [
                Campaign.Field.id,
                Campaign.Field.name,
                Campaign.Field.status,
                Campaign.Field.objective,
                Campaign.Field.daily_budget,
                Campaign.Field.lifetime_budget,
                Campaign.Field.spend_cap, # Added this
                Campaign.Field.start_time,
                Campaign.Field.special_ad_categories,
            ]
            
            # Fetch latest 50 campaigns
            campaigns = account.get_campaigns(fields=fields, params={'limit': 50})
            
            data = []
            for cmp in campaigns:
                # ✅ Change 2: Formatting Budget (Cents -> Main Currency)
                # daily = float(cmp['daily_budget']) / 100 if 'daily_budget' in cmp else None
                # lifetime = float(cmp['lifetime_budget']) / 100 if 'lifetime_budget' in cmp else None
                # cap = float(cmp['spend_cap']) / 100 if 'spend_cap' in cmp else None

                has_daily = 'daily_budget' in cmp and int(cmp['daily_budget']) > 0
                has_lifetime = 'lifetime_budget' in cmp and int(cmp['lifetime_budget']) > 0
                
                is_cbo = has_daily or has_lifetime

                data.append({
                    'id': cmp.get('id'),
                    'name': cmp.get('name'),
                    'status': cmp.get('status'),
                    'is_cbo_enabled': is_cbo,  # ✅ Frontend ko ye flag milega
                    'budget_source': 'Campaign Level' if is_cbo else 'Ad Set Level', # ✅ Readable text
                    'daily_budget': float(cmp['daily_budget'])/100 if has_daily else None,
                    'lifetime_budget': float(cmp['lifetime_budget'])/100 if has_lifetime else None,
                    'spend_cap': float(cmp['spend_cap'])/100 if 'spend_cap' in cmp else None,
                })

            return Response({"count": len(data), "campaigns": data})

        except FacebookRequestError as e:
            return Response({"error": "Meta API Error", "details": e.body()}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
#===============================================================================================

    @action(detail=False, methods=['get'])
    def get_campaign_detail(self, request):
        
        # 1. Auth Check
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        # 2. Input Check
        campaign_id = request.query_params.get('campaign_id')
        if not campaign_id:
            return Response({"error": "Campaign ID is required"}, status=400)

        try:
            FacebookAdsApi.init(access_token=access_token)
            
            fields = [
                'id',
                'name',
                'status',
                'effective_status',  
                'objective',
                'buying_type',
                'daily_budget',      # Check 1
                'lifetime_budget',   # Check 2
                'budget_remaining',
                'spend_cap',
                'start_time',
                'stop_time',
                'created_time',
                'updated_time',
                'account_id',
                'special_ad_categories',
                'bid_strategy',
                'issues_info'
            ]
            
            # 3. Fetch Data
            campaign = Campaign(campaign_id).api_get(fields=fields)
            
            # Data ko Dictionary mein convert karein
            data = campaign.export_all_data()

            # --- 🕵️‍♂️ STEP 4: DETECT CBO STATUS (New Logic) ---
            # Logic: Agar Campaign level par budget hai, to CBO On hai.
            
            is_cbo = False
            if 'daily_budget' in data or 'lifetime_budget' in data:
                is_cbo = True
            
            # Response mein apni Custom Key add karein
            data['is_cbo_enabled'] = is_cbo 

            return Response(data)

        except FacebookRequestError as e:
            return Response({
                "error": "Meta API Error",
                "message": e.api_error_message(),
                "details": e.body()
            }, status=400)
        except Exception as e:
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)
        

#=================================================================================================

    @action(detail=False, methods=['post'])
    def update_campaign(self, request):
        user = request.user
        if user.is_anonymous: 
            user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except Exception:
            return Response({"error": "Facebook account not connected."}, status=400)

        serializer = CampaignUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        campaign_id = data['campaign_id']
        params = {}

        # 1. Fetch Current State (Bohat zaroori hai validation ke liye)
        try:
            FacebookAdsApi.init(access_token=access_token)
            campaign = Campaign(campaign_id)
            current_meta_data = campaign.api_get(fields=['daily_budget', 'lifetime_budget', 'bid_strategy'])
            
            has_daily = 'daily_budget' in current_meta_data
            has_lifetime = 'lifetime_budget' in current_meta_data
            is_cbo = has_daily or has_lifetime
        except FacebookRequestError as e:
            return Response({"error": "Meta API Error", "message": e.api_error_message()}, status=400)

        # 2. Basic Fields Mapping
        if 'name' in data: params['name'] = data['name']
        if 'status' in data: params['status'] = data['status']
        if 'special_ad_categories' in data:
            params['special_ad_categories'] = data['special_ad_categories']

        # 3. Budget & CBO Validation Logic
        new_daily = data.get('daily_budget')
        new_lifetime = data.get('lifetime_budget')

        # Scenario A: Daily se Lifetime (Ya vice versa) switch karne ki koshish
        if (new_daily and has_lifetime) or (new_lifetime and has_daily):
            return Response({
                "error": "Invalid Action",
                "message": "Meta does not allow switching between Daily and Lifetime budget. Please create a new campaign."
            }, status=400)

        # Scenario B: CBO Disable karne ki koshish (Budget 0 bhej kar)
        if (new_daily == 0 or new_lifetime == 0) and is_cbo:
            return Response({
                "error": "Action Not Allowed",
                "message": "CBO cannot be disabled after creation. You can only update the budget amount."
            }, status=400)

        # Scenario C: Budget Update
        if new_daily and new_daily > 0:
            params['daily_budget'] = int(new_daily * 100)
        if new_lifetime and new_lifetime > 0:
            params['lifetime_budget'] = int(new_lifetime * 100)

        # 4. Bid Strategy Logic
        if 'bid_strategy' in data:
            if is_cbo or (new_daily or new_lifetime): # Only if CBO is active or being enabled
                params['bid_strategy'] = data['bid_strategy']

        # 5. Final Update Call
        if not params:
            return Response({"message": "No valid changes detected."}, status=200)

        try:
            campaign.api_update(params=params)
            return Response({
                "message": "Campaign updated successfully!",
                "campaign_id": campaign_id,
                "updated_fields": list(params.keys())
            }, status=status.HTTP_200_OK)

        except FacebookRequestError as e:
            return Response({"error": "Meta API Error", "message": e.api_error_message()}, status=400)
        except Exception as e:
            return Response({"error": "Internal Error", "details": str(e)}, status=500)
        
#=================================================================================================


    @action(detail=False, methods=['post'])
    def delete_campaign(self, request):
       
        # 1. Auth Check
        user = request.user
        if user.is_anonymous: user = User.objects.first()
        
        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        # 2. Validation via Serializer
        serializer = CampaignDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        campaign_id = serializer.validated_data['campaign_id']

        try:
            FacebookAdsApi.init(access_token=access_token)
            campaign = Campaign(campaign_id)
            
            # 3. Remote Delete (Sets status='ARCHIVED')
            campaign.remote_delete()
            
            return Response({
                "message": "Campaign deleted successfully (Archived).", 
                "campaign_id": campaign_id,
                "status": "ARCHIVED",  # Meta 'DELETED' nahi, 'ARCHIVED' kehta hai
                "meta_success": True
            }, status=status.HTTP_200_OK)
            
        except FacebookRequestError as e:
            # Meta Specific Error Handling
            return Response({
                "error": "Meta API Error",
                "message": e.api_error_message(),
                "code": e.api_error_code(),
                "details": e.body()
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)
        

#=================================================================================================

    @action(detail=False, methods=['post'])
    def toggle_campaign_status(self, request):
        
        # 1. Auth Check
        user = request.user
        if user.is_anonymous: user = User.objects.first()
        
        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        # 2. Validation via Serializer
        serializer = CampaignToggleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        campaign_id = data['campaign_id']
        target_status = data['status']

        try:
            FacebookAdsApi.init(access_token=access_token)
            campaign = Campaign(campaign_id)
            
            # 3. Status Update Call
            print(f"🔌 Toggling Campaign {campaign_id} to {target_status}")
            
            campaign.remote_update(params={
                'status': target_status
            })
            
            return Response({
                "message": f"Campaign is now {target_status}", 
                "campaign_id": campaign_id,
                "status": target_status,
                "success": True
            }, status=status.HTTP_200_OK)
            
        except FacebookRequestError as e:
            # Safe Error Handling
            return Response({
                "error": "Meta API Error",
                "message": e.api_error_message(),
                "code": e.api_error_code(),
                "details": e.body()
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)
   
#=================================================================================================

    @action(detail=False, methods=['post'])
    def create_ad_set(self, request):
        
        # 1. Auth Check
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        # 2. Validation
        serializer = AdSetCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            FacebookAdsApi.init(access_token=access_token)
            account = AdAccount(data['ad_account_id'])
            
            # Timezone Setup
            account_details = account.api_get(fields=['timezone_name'])
            tz_name = account_details.get('timezone_name', 'UTC')
            local_tz = pytz.timezone(tz_name)
            
            start_time = data.get('start_time')
            if start_time:
                start_time = start_time.astimezone(local_tz)
            else:
                start_time = datetime.now(local_tz) + timedelta(minutes=15)

            # --- 🕵️‍♂️ CAMPAIGN INSPECTION ---
            campaign = Campaign(data['campaign_id'])
            # 'bid_strategy' add kia taake bidding conflict check kar sakein
            camp_data = campaign.api_get(fields=['daily_budget', 'lifetime_budget', 'special_ad_categories', 'bid_strategy'])
            
            is_campaign_cbo = 'daily_budget' in camp_data or 'lifetime_budget' in camp_data
            campaign_strategy = camp_data.get('bid_strategy')

            # Special Ad Check
            special_cats = camp_data.get('special_ad_categories', [])
            is_special_ad = bool(special_cats and 'NONE' not in special_cats)
            
            if is_special_ad:
                print(f"⚠️ Special Ad Category Detected: {special_cats}")

            # --- 📝 BASE PARAMETERS ---
            params = {
                'name': data['name'],
                'campaign_id': data['campaign_id'],
                'status': data['status'],
                'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'billing_event': data['billing_event'],
                'optimization_goal': data['optimization_goal'],
            }
            
            if data.get('end_time'):
                params['end_time'] = data['end_time'].astimezone(local_tz).strftime('%Y-%m-%dT%H:%M:%S%z')

            # --- 💰 BUDGET & BIDDING LOGIC ---
            
            # 1. Budget Handling
            if is_campaign_cbo:
                pass # CBO hai to budget ignore
            else:
                if data.get('daily_budget'): params['daily_budget'] = int(data['daily_budget'] * 100)
                elif data.get('lifetime_budget'): params['lifetime_budget'] = int(data['lifetime_budget'] * 100)

            # 2. Bidding Handling (New Logic)
            if data.get('bid_amount'):
                # Cents conversion
                params['bid_amount'] = int(data['bid_amount']) * 100
                
                # Agar Campaign par strategy nahi hai to Ad Set par Cost Cap lagao
                if not campaign_strategy: 
                     params['bid_strategy'] = 'COST_CAP'
            
            # Error Check: Campaign Cost Cap hai par User ne Bid Amount nahi di
            elif campaign_strategy in ['COST_CAP', 'BID_CAP'] and not data.get('bid_amount'):
                return Response({
                    "error": "Bid Amount Missing",
                    "message": f"Your Campaign is using {campaign_strategy}. You MUST provide a 'bid_amount' for this Ad Set.",
                    "campaign_strategy": campaign_strategy
                }, status=status.HTTP_400_BAD_REQUEST)


            # --- 🎯 TARGETING ---
            targeting = {
                'geo_locations': data['geo_locations'],
                'publisher_platforms': data['publisher_platforms'],
                'device_platforms': data['device_platforms'],
                'targeting_automation': {'advantage_audience': 0}
            }

            if is_special_ad:
                # Force Rules
                targeting['age_min'] = 18
                targeting['age_max'] = 65
                if 'genders' in targeting: del targeting['genders']
                print("ℹ️ Applied Special Ad Category Restrictions.")
            else:
                # Normal Rules
                targeting['age_min'] = data.get('age_min', 18)
                targeting['age_max'] = data.get('age_max', 65)
                if data.get('genders'): targeting['genders'] = data['genders']
                
                # --- 🔗 FLEXIBLE SPEC (Complete) ---
                flexible_spec = []
                
                # 1. Interests
                if data.get('interest_ids'):
                    flexible_spec.append({'interests': [{'id': i, 'name': 'Unknown'} for i in data['interest_ids']]})
                
                # 2. Behaviors
                if data.get('behavior_ids'):
                    flexible_spec.append({'behaviors': [{'id': i, 'name': 'Unknown'} for i in data['behavior_ids']]})
                
                # 3. Life Events / Demographics (Ye Wapis Add Kar Dia) ✅
                if data.get('life_event_ids'):
                    flexible_spec.append({'life_events': [{'id': i, 'name': 'Unknown'} for i in data['life_event_ids']]})
                
                if flexible_spec: targeting['flexible_spec'] = flexible_spec

            params['targeting'] = targeting

            # --- 🚀 EXECUTE ---
            print(f"🚀 Params being sent: {params}")
            adset = account.create_ad_set(params=params)

            return Response({
                "message": "Ad Set Created Successfully!",
                "adset_id": adset['id'],
                "status": "CREATED"
            }, status=status.HTTP_201_CREATED)

        except FacebookRequestError as e:
            return Response({
                "error": "Meta API Error",
                "message": e.api_error_message(),
                "details": e.body()
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Server Error", "details": str(e)}, status=500)
        
#=================================================================================================

    @action(detail=False, methods=['get'])
    def search_interests(self, request):
        
        # 1. Inputs
        query = request.query_params.get('q')
        ad_account_id = request.query_params.get('ad_account_id')
        
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        if not query:
            return Response([]) 

        try:
            # ... Auth setup ...
            profile = FacebookProfile.objects.get(user=user)
            FacebookAdsApi.init(access_token=profile.access_token)
            
            # Agar ad_account_id nahi hai to error do
            if not ad_account_id:
                 return Response({"error": "Ad Account ID required for search"}, status=400)

            # 🛑 CHANGE 1: Search Parameters Updated
            # 'adTargetingCategory' use karenge taake Sab kuch (Behavior/Demographics) mile
            params = {
                'type': 'adTargetingCategory', 
                'class': ['interests', 'behaviors', 'demographics'], 
                'q': query,
                'limit': 15,
                'locale': 'en_US'
            }

            results = AdAccount(ad_account_id).get_targeting_search(params=params)
            
            # 3. Clean Format for Dropdown
            data = []
            for item in results:
                # 🛑 CHANGE 2: Extract Type
                # Meta 'type' return karta hai (e.g., 'interests', 'behaviors')
                category_type = item.get('type') 
                
                # Frontend ki asani k liye hum specific keys bata dete hain
                submission_key = 'interest_ids' # Default
                
                if category_type == 'behaviors':
                    submission_key = 'behavior_ids'
                elif category_type == 'demographics':
                    submission_key = 'life_event_ids' # Demographics usually life_events mein jate hain ya demographics mein

                data.append({
                    'value': item['id'],   
                    'label': item['name'], 
                    'size': item.get('audience_size_lower_bound'),
                    'type': category_type,      # 'interests', 'behaviors', etc.
                    'target_key': submission_key # Frontend ko batayega k kahan bhejna hai
                })
                
            return Response(data) 

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
#=================================================================================================

    @action(detail=False, methods=['post'])
    def update_ad_set(self, request):
        
        # --- 1. Authentication Check ---
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        # --- 2. Validation ---
        serializer = AdSetUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        data = serializer.validated_data
        adset_id = data['adset_id']

        try:
            FacebookAdsApi.init(access_token=access_token)
            adset = AdSet(adset_id)

            # --- 📥 STEP 1: FETCH CONTEXT (Current Data + Parent Campaign) ---
            # Hum 'campaign_id' aur 'targeting' mangwa rahe hain
            current_adset = adset.api_get(fields=['targeting', 'name', 'start_time', 'account_id', 'campaign_id'])
            
            # Account ID & Timezone Setup
            raw_account_id = current_adset['account_id']
            account_id = f"act_{raw_account_id}" if not raw_account_id.startswith('act_') else raw_account_id
            
            account = AdAccount(account_id)
            account_details = account.api_get(fields=['timezone_name'])
            local_tz = pytz.timezone(account_details.get('timezone_name', 'UTC'))

            # --- 🕵️‍♂️ STEP 2: CHECK PARENT CAMPAIGN ---
            campaign_id = current_adset['campaign_id']
            campaign = Campaign(campaign_id)
            camp_data = campaign.api_get(fields=['daily_budget', 'lifetime_budget', 'special_ad_categories'])
            
            # A. CBO Check
            is_cbo = 'daily_budget' in camp_data or 'lifetime_budget' in camp_data
            
            # B. Special Category Check
            special_cats = camp_data.get('special_ad_categories', [])
            is_special_ad = bool(special_cats and 'NONE' not in special_cats)
            
            if is_special_ad:
                print(f"⚠️ Updating Ad Set in Special Category Campaign: {special_cats}")

            # --- 💰 STEP 3: BUDGET CONFLICT CHECK ---
            user_trying_to_set_budget = 'daily_budget' in data or 'lifetime_budget' in data
            if is_cbo and user_trying_to_set_budget:
                return Response({
                    "error": "Budget Conflict",
                    "message": "This Campaign is using CBO. You cannot set Ad Set budget.",
                }, status=400)

            # --- 🔄 STEP 4: BUILD UPDATE PARAMETERS ---
            params = {}

            if 'name' in data: params['name'] = data['name']
            if 'status' in data: params['status'] = data['status']
            
            # Budget Updates (Only if NOT CBO)
            if not is_cbo:
                if 'daily_budget' in data: params['daily_budget'] = int(data['daily_budget'] * 100)
                if 'lifetime_budget' in data: params['lifetime_budget'] = int(data['lifetime_budget'] * 100)
            
            if 'bid_amount' in data: params['bid_amount'] = data['bid_amount']

            # Time Updates
            if 'start_time' in data:
                params['start_time'] = data['start_time'].astimezone(local_tz).strftime('%Y-%m-%dT%H:%M:%S%z')
            if 'end_time' in data:
                params['end_time'] = data['end_time'].astimezone(local_tz).strftime('%Y-%m-%dT%H:%M:%S%z')

            # --- 🎯 STEP 5: TARGETING MERGE & FIX (CORE LOGIC) ---
            targeting_fields = ['geo_locations', 'age_min', 'age_max', 'genders', 'interest_ids', 'behavior_ids', 'life_event_ids']
            has_targeting_change = any(field in data for field in targeting_fields)

            if has_targeting_change:
                # 1. Load Existing Targeting
                raw_targeting = current_adset.get('targeting', {})
                # Meta Object to Dict Conversion
                if hasattr(raw_targeting, 'export_all_data'):
                    new_targeting = raw_targeting.export_all_data()
                else:
                    new_targeting = dict(raw_targeting)

                # 2. Update Geo Location
                if 'geo_locations' in data: 
                    new_targeting['geo_locations'] = data['geo_locations']

                # 🛑 3. APPLY SPECIAL AD RULES (Auto-Fix) 🛑
                if is_special_ad:
                    # == FORCE RULES ==
                    new_targeting['age_min'] = 18
                    new_targeting['age_max'] = 65
                    
                    # Remove Gender (Meta auto selects All)
                    if 'genders' in new_targeting:
                        del new_targeting['genders']
                    
                    print("ℹ️ Update: Enforcing Special Ad Rules (Age 18-65+, All Genders).")
                    
                else:
                    # == NORMAL RULES ==
                    if 'age_min' in data: new_targeting['age_min'] = data['age_min']
                    if 'age_max' in data: new_targeting['age_max'] = data['age_max']
                    if 'genders' in data: new_targeting['genders'] = data['genders']

                # 4. Handle Detailed Targeting (Interests/Behaviors)
                # Logic: Agar user naya data bhej raha hai, to purana replace karo.
                # Agar user kuch nahi bhej raha, to purana rehne do.
                
                if 'interest_ids' in data or 'behavior_ids' in data or 'life_event_ids' in data:
                    
                    # Check: Agar Special Ad hai, to kya hum targeting allow karein?
                    # Safe Mode: Agar Housing hai, aur user ghalat interest bhej raha hai, to error ayega.
                    # Behtar ye hai k hum user ka data process karein, lekin error handling call k waqt hogi.
                    
                    flexible_spec_item = {}
                    
                    if data.get('interest_ids'):
                        flexible_spec_item['interests'] = [{'id': i, 'name': 'Unknown'} for i in data['interest_ids']]
                    
                    if data.get('behavior_ids'):
                        flexible_spec_item['behaviors'] = [{'id': i, 'name': 'Unknown'} for i in data['behavior_ids']]
                        
                    if data.get('life_event_ids'):
                        flexible_spec_item['life_events'] = [{'id': i, 'name': 'Unknown'} for i in data['life_event_ids']]
                    
                    # Update Spec
                    if flexible_spec_item:
                        new_targeting['flexible_spec'] = [flexible_spec_item]
                    else:
                        # Agar user ne empty lists bheji hain to clear kar do
                        # (Taake agar user 'Cricket' remove karna chahe to kar sake)
                        if 'flexible_spec' in new_targeting:
                            del new_targeting['flexible_spec']

                params['targeting'] = new_targeting

            # --- 🚀 STEP 6: EXECUTE ---
            if params:
                print(f"🔄 Updating Ad Set {adset_id} with params: {params}")
                adset.remote_update(params=params)
                
                return Response({
                    "message": "Ad Set Updated Successfully!",
                    "id": adset_id,
                    "updated_fields": list(params.keys()),
                    "warning": "Special Ad Rules Applied (Age/Gender reset)" if is_special_ad else None
                })
            else:
                return Response({"message": "No changes provided."}, status=200)

        except FacebookRequestError as e:
            # Error Handling ko thora smart banaya hai
            error_msg = e.api_error_message()
            
            # Special Ad Specific Error Catch
            if "Special ad category" in error_msg or "2909036" in str(e.body()):
                return Response({
                    "error": "Restricted Targeting",
                    "message": "You are updating a Special Ad Category Campaign. Some interests or behaviors are NOT allowed (e.g., Cricket, Shoppers). Please remove them.",
                    "details": e.body()
                }, status=400)

            return Response({
                "error": "Meta API Error",
                "message": error_msg,
                "details": e.body()
            }, status=400)
            
        except Exception as e:
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)
        
#=================================================================================================
    @action(detail=False, methods=['post'])
    def delete_ad_set(self, request):
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        adset_id = request.data.get('adset_id')
        
        if not adset_id:
            return Response({"error": "Ad Set ID is required"}, status=400)

        try:
            adset = AdSet(adset_id)
            adset.remote_delete()
            
            return Response({
                "message": "Ad Set Deleted (Archived) Successfully!", 
                "id": adset_id,
                "status": "DELETED"
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
#================================================================================================= 

    @action(detail=False, methods=['get'])
    def get_ad_sets(self, request):
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        campaign_id = request.query_params.get('campaign_id')

        if not campaign_id:
            return Response({"error": "Campaign ID is required"}, status=400)

        try:
            campaign = Campaign(campaign_id)
            
            # Ad Set k zaroori fields
            fields = [
                AdSet.Field.id,
                AdSet.Field.name,
                AdSet.Field.status,
                AdSet.Field.daily_budget,
                AdSet.Field.targeting,
                AdSet.Field.start_time,
                AdSet.Field.end_time,
                AdSet.Field.billing_event,
            ]
            
            # API Call: Campaign se Ad Sets mangwana
            ad_sets = campaign.get_ad_sets(fields=fields)
            
            data = []
            for adset in ad_sets:
                data.append({
                    'id': adset.get('id'),
                    'name': adset.get('name'),
                    'status': adset.get('status'),
                    'daily_budget': adset.get('daily_budget'),
                    'targeting': adset.get('targeting'), # Age, Location waghaira
                    'start_time': adset.get('start_time'),
                })

            return Response({"campaign_id": campaign_id, "count": len(data), "ad_sets": data})

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
#=================================================================================================

    @action(detail=False, methods=['get'])
    def get_ad_set_detail(self, request):
       
        # 1. Auth Check
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        # 2. Input Check
        adset_id = request.query_params.get('adset_id')
        if not adset_id:
            return Response({"error": "Ad Set ID is required"}, status=400)

        try:
            FacebookAdsApi.init(access_token=access_token)
            
            # --- ✅ COMPLETE AD SET FIELDS LIST ---
            # Humne wo sab fields shamil ki hain jo Frontend ko chahiye hoti hain
            fields = [
                'id',
                'name',
                'status',
                'effective_status',    # Asal status (Active, Paused, Deleted, Archived)
                'campaign_id',
                'account_id',
                
                # 💰 Budget & Schedule
                'daily_budget',
                'lifetime_budget',
                'budget_remaining',
                'start_time',
                'end_time',
                
                # ⚙️ Optimization & Bidding
                'optimization_goal',   # REACH, IMPRESSIONS, LINK_CLICKS etc.
                'billing_event',       # IMPRESSIONS vs CLICKS
                'bid_amount',          # Bid Cap (agar manual bidding ho)
                'bid_strategy',
                
                # 🎯 Targeting (The Most Important Part)
                'targeting',
                
                # 📊 Delivery Info
                'promoted_object',     # Kis cheez ki promotion ho rahi hai (Page, Pixel, App)
                'pacing_type',         # Standard vs Accelerated
                'destination_type',    # Website, App, Messenger etc.
                
                # 🕒 Metadata
                'created_time',
                'updated_time',
                'issues_info'          # Errors/Warnings (e.g. Budget too low)
            ]
            
            # 3. Fetch Data
            adset_data = AdSet(adset_id).api_get(fields=fields)
            
            # 4. Clean Data & Return
            data = adset_data.export_all_data()

            return Response(data)

        except FacebookRequestError as e:
            return Response({
                "error": "Meta API Error",
                "message": e.api_error_message(),
                "details": e.body()
            }, status=400)
        except Exception as e:
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)


#=================================================================================================

    @action(detail=False, methods=['post'])
    def toggle_adset_status(self, request):
        
        # 1. Auth Check
        user = request.user
        if user.is_anonymous: user = User.objects.first()
        
        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        # 2. Validation via Serializer
        serializer = AdSetToggleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        adset_id = data['adset_id']
        target_status = data['status']

        try:
            FacebookAdsApi.init(access_token=access_token)
            
            # AdSet Object banaya
            adset = AdSet(adset_id)
            
            # 3. Status Update Call
            print(f"🔌 Toggling Ad Set {adset_id} to {target_status}")
            
            # Meta ko update bheja
            adset.remote_update(params={
                'status': target_status
            })
            
            return Response({
                "message": f"Ad Set is now {target_status}", 
                "adset_id": adset_id,
                "status": target_status,
                "success": True
            }, status=status.HTTP_200_OK)
            
        except FacebookRequestError as e:
            # Safe Error Handling
            return Response({
                "error": "Meta API Error",
                "message": e.api_error_message(),
                "code": e.api_error_code(),
                "details": e.body()
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)

#=================================================================================================

    @action(detail=False, methods=['post'])
    def create_ad_creative(self, request):

        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        FacebookAdsApi.init(access_token=token)

        # 1. Inputs
        ad_account_id = request.data.get('ad_account_id')
        page_id = request.data.get('page_id')
        image_url = request.data.get('image_url')
        headline = request.data.get('headline', 'Chat with us!')
        primary_text = request.data.get('primary_text', 'Best Dental Services in Town.')
        link_url = request.data.get('link_url', 'https://www.example.com')
        
        if not ad_account_id or not page_id or not image_url:
            return Response({"error": "Ad Account ID, Page ID and Image URL are required"}, status=400)

        try:
            account = AdAccount(ad_account_id)

            # --- A. Image Download (Memory) ---
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(image_url, headers=headers)
            if response.status_code != 200:
                return Response({"error": "Failed to download image."}, status=400)
            
            image_bytes = base64.b64encode(response.content).decode('utf-8')
            image_filename = 'ad_image.jpg'

            # --- B. Upload to Facebook ---
            image_response = account.create_ad_image(params={
                'name': image_filename,
                'bytes': image_bytes, 
            })
            
            # --- C. Hash Extraction (SIMPLIFIED FIX) ---
            # Error log ne bataya k 'hash' top level par hi mojood hai.
            # Hum pehle direct check karenge, phir list fallback rakhenge.
            
            image_hash = None
            
            # 1. Direct Access (Jo apke error log mein tha)
            if hasattr(image_response, 'get'):
                image_hash = image_response.get('hash')
            
            # 2. Agar List ho (Fallback)
            if not image_hash and isinstance(image_response, list) and len(image_response) > 0:
                 image_hash = image_response[0].get('hash')

            if not image_hash:
                 # Debugging k liye wapis pura response bhej denge agar fail hua
                 return Response({"error": f"Hash not found. Response: {str(image_response)}"}, status=400)

            # --- D. Creative Create ---
            creative_params = {
                'name': 'Creative - ' + headline,
                'object_story_spec': {
                    'page_id': page_id,
                    'link_data': {
                        'image_hash': image_hash,
                        'link': link_url,
                        'message': primary_text,
                        'name': headline,
                        'call_to_action': {
                            'type': 'LEARN_MORE',
                            'value': {'link': link_url}
                        }
                    }
                }
            }
            
            creative = account.create_ad_creative(params=creative_params)

            return Response({
                "message": "Creative Created Successfully!",
                "creative_id": creative['id'],
                "image_hash": image_hash
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    

    @action(detail=False, methods=['get'])
    def get_ad_creatives(self, request):
        
        # --- 1. Auth Check ---
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)

        # --- 2. Input Validation ---
        # GET request mein data 'query_params' mein aata hai
        ad_account_id = request.query_params.get('ad_account_id')
        
        if not ad_account_id:
            return Response({"error": "ad_account_id is required in query params"}, status=400)

        try:
            FacebookAdsApi.init(access_token=access_token)
            account = AdAccount(ad_account_id)

            # --- 3. Define Fields ---
            # Hamein Meta se kya kya chahiye?
            fields = [
                'id',
                'name',
                'status',
                'thumbnail_url',     # Ad ka chota image
                'image_url',         # Original image (kabhi kabhi null hota hai)
                'object_story_spec', # Ismein Headline/Primary Text hota hai
                'instagram_actor_id' # Agar Insta se juda hai
            ]

            # --- 4. Fetch From Meta ---
            # limit=50 rakha hai taake load jaldi ho
            creatives = account.get_ad_creatives(fields=fields, params={'limit': 50})
            
            # --- 5. Data Cleaning (Parsing) ---
            # Meta ka data bohot complex hota hai, usay simple banayenge
            data = []
            
            for creative in creatives:
                
                # a. Safe Extraction for Headline & Text
                headline = "N/A"
                primary_text = "N/A"
                page_id = "N/A"
                
                # Meta ka structure: object_story_spec -> link_data -> message/name
                spec = creative.get('object_story_spec', {})
                link_data = spec.get('link_data', {})
                
                if link_data:
                    headline = link_data.get('name', 'No Headline')
                    primary_text = link_data.get('message', 'No Text')
                
                if spec:
                    page_id = spec.get('page_id')

                # b. Image Logic (Thumbnail vs Image URL)
                final_image = creative.get('image_url') or creative.get('thumbnail_url')

                # c. Final Clean Dictionary
                clean_creative = {
                    'id': creative['id'],
                    'name': creative['name'],
                    'status': creative.get('status'),
                    'headline': headline,
                    'primary_text': primary_text,
                    'image_url': final_image,
                    'page_id': page_id,
                    'is_instagram_connected': bool(creative.get('instagram_actor_id'))
                }
                
                data.append(clean_creative)

            return Response({
                "count": len(data),
                "creatives": data
            }, status=200)

        except FacebookRequestError as e:
            return Response({
                "error": "Meta API Error",
                "message": e.api_error_message(),
                "details": e.body()
            }, status=400)
        except Exception as e:
            return Response({"error": "Internal Server Error", "details": str(e)}, status=500)
        
    # @action(detail=False, methods=['get'])
    # def get_creatives_with_campaigns(self, request):
        
        # 1. Auth & Validation
        user = request.user
        if user.is_anonymous: user = User.objects.first()

        try:
            profile = FacebookProfile.objects.get(user=user)
            access_token = profile.access_token
        except: return Response({"error": "User not connected."}, status=400)

        ad_account_id = request.query_params.get('ad_account_id')
        if not ad_account_id: return Response({"error": "ad_account_id required"}, status=400)

        try:
            FacebookAdsApi.init(access_token=access_token)
            account = AdAccount(ad_account_id)

            # --- 2. JADOO FIELDS (The Magic) ---
            # Hum maang 'Ad' rahay hain, par focus Creative par hai
            fields = [
                'id',
                'name',
                'status',
                'campaign{id, name, status}',  # ✅ Campaign ID yahan se milegi
                'adset{id, name, status}',     # ✅ AdSet ID yahan se milegi
                'creative{id, name, thumbnail_url, image_url, object_story_spec}' # ✅ Creative Data
            ]

            # --- 3. Fetch Data ---
            # Limit barha dein taake saray ads aajayen
            ads = account.get_ads(fields=fields, params={'limit': 100})
            
            data = []
            
            for ad in ads:
                # Meta ka data nested hota hai, hum usay 'Flat' (Seedha) karenge
                
                # A. Safe Extraction
                camp = ad.get('campaign', {})
                adset = ad.get('adset', {})
                creative = ad.get('creative', {})
                
                # B. Image Logic
                # Kabhi image_url hota hai, kabhi thumbnail_url
                final_image = creative.get('image_url') or creative.get('thumbnail_url')
                
                # C. Headline/Text Logic
                headline = "N/A"
                primary_text = "N/A"
                
                story_spec = creative.get('object_story_spec', {})
                # Nested structure: object_story_spec -> link_data -> name (headline)
                if story_spec and 'link_data' in story_spec:
                    link_data = story_spec['link_data']
                    headline = link_data.get('name', '')
                    primary_text = link_data.get('message', '')

                # D. Final Clean JSON Object
                ad_data = {
                    # --- 1. Ad Info ---
                    'ad_id': ad['id'],
                    'ad_name': ad['name'],
                    'ad_status': ad['status'],
                    
                    # --- 2. Campaign Info (Jo aapko chahiye tha) ---
                    'campaign_id': camp.get('id'),
                    'campaign_name': camp.get('name'),
                    'campaign_status': camp.get('status'),

                    # --- 3. Ad Set Info ---
                    'adset_id': adset.get('id'),
                    'adset_name': adset.get('name'),
                    
                    # --- 4. Creative Info ---
                    'creative_id': creative.get('id'),
                    'creative_name': creative.get('name'),
                    'image_url': final_image,
                    'headline': headline,
                    'primary_text': primary_text
                }
                
                data.append(ad_data)

            return Response({
                "count": len(data),
                "data": data
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        


#====================================================================================
    @action(detail=False, methods=['post'])
    def create_ad(self, request):
        user = request.user
        if user.is_anonymouse: user = user.objects.first()

        try: 
            profile = FacebookProfile.objects.get(user=user)
            token = profile.access_token
        except FacebookProfile.DoesNotExist:
            return Response({"error": "User not connected."}, status=400)
        
        FacebookAdsApi.init(access_token=token)

        serializer = AdCreateSerializer(data=request.data)

        
        if serializer.is_valid():
            
            data = serializer.validated_data
            
            try:
                account = AdAccount(data['ad_account_id'])
                params = {
                    'name': data['name'],
                    'adset_id': data['adset_id'],
                    'creative': {'creative_id': data['creative_id']},
                    'status': data['status'],
                }
                
                ad = account.create_ad(params=params)
                
                return Response({
                    "message": "Ad Created Successfully",
                    "ad_id": ad['id'],
                    "status": data['status']
                })
            except Exception as e:
                return Response({"error": str(e)}, status=500)
        
        else:
            # 3. Agar data ghalat hai, to Serializer khud error detail dega
            return Response(serializer.errors, status=400)