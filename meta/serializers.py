from rest_framework import serializers
from .models import FacebookProfile

class FacebookConnectSerializer(serializers.Serializer):
    """Frontend se humein ye 3 cheezein milengi"""
    access_token = serializers.CharField(required=True)
    page_id = serializers.CharField(required=True)
    page_name = serializers.CharField(required=True)

class PostContentSerializer(serializers.Serializer):
    """Post karne k liye sirf message chahiye (Image optional hai)"""
    message = serializers.CharField(required=True)
    image_url = serializers.URLField(required=False, allow_blank=True)



#===================================================================

class AdCreateSerializer(serializers.Serializer):
    ad_account_id = serializers.CharField(required=True)
    adset_id = serializers.CharField(required=True)
    creative_id = serializers.CharField(required=True)
    name = serializers.CharField(required=False, default="New Ad via API")
    status = serializers.ChoiceField(choices=['ACTIVE', 'PAUSED'], default='PAUSED')
      
#===================================================================

class CampaignCreateSerializer(serializers.Serializer):
    # --- 1. Basic Identity ---
    ad_account_id = serializers.CharField(
        required=True, 
        help_text="e.g. act_12345678"
    )
    name = serializers.CharField(required=True, max_length=255)
    
    status = serializers.ChoiceField(
        choices=['ACTIVE', 'PAUSED'], 
        default='PAUSED'
    )

    OBJECTIVE_CHOICES = [
        ('OUTCOME_SALES', 'Sales'),
        ('OUTCOME_LEADS', 'Leads'),
        ('OUTCOME_TRAFFIC', 'Traffic'),
        ('OUTCOME_AWARENESS', 'Awareness'),
        ('OUTCOME_ENGAGEMENT', 'Engagement'),
        ('OUTCOME_APP_PROMOTION', 'App Promotion'),
    ]
    objective = serializers.ChoiceField(choices=OBJECTIVE_CHOICES)

    special_ad_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False, 
        default=list,
        help_text="Send ['HOUSING'] or [] if none."
    )

    # --- 2. CBO Settings (Campaign Budget Optimization) ---
    is_cbo_enabled = serializers.BooleanField(
        default=False, 
        help_text="Set True to manage budget at Campaign Level"
    )
    
    daily_budget = serializers.FloatField(required=False, min_value=1.0)
    lifetime_budget = serializers.FloatField(required=False, min_value=1.0)
    
    bid_strategy = serializers.ChoiceField(
        choices=[
            ('LOWEST_COST_WITHOUT_CAP', 'Highest Volume'), 
            ('COST_CAP', 'Cost Cap'), 
            ('BID_CAP', 'Bid Cap')
        ],
        required=False
    )

    # --- 3. NEW FEATURE: Spend Cap (Campaign Limit) ---
    spend_cap = serializers.FloatField(
        required=False, 
        min_value=1.0, 
        help_text="Overall limit for campaign spending (e.g., 500.00)"
    )

    # --- 4. NEW FEATURE: iOS 14+ Settings ---
    is_ios14_campaign = serializers.BooleanField(
        required=False, 
        default=False,
        help_text="Set to True for iOS 14.5+ SKAdNetwork campaigns"
    )
    
    # User ko App ID dena hoga (Search Box logic)
    ios14_app_id = serializers.CharField(
        required=False,
        help_text="Required if is_ios14_campaign is True. e.g. '123456789' (App Store ID)"
    )

    # --- VALIDATION LOGIC ---
    def validate(self, data):
        # A. CBO Validation (Existing Logic)
        is_cbo = data.get('is_cbo_enabled', False)
        daily = data.get('daily_budget')
        lifetime = data.get('lifetime_budget')

        if is_cbo:
            if not daily and not lifetime:
                raise serializers.ValidationError(
                    "When CBO is active, Daily Budget or Lifetime Budget is necessary."
                )
            if daily and lifetime:
                raise serializers.ValidationError(
                    "Cannot select both Daily and Lifetime budget. Please choose one."
                )

        if not is_cbo and (daily or lifetime):
             raise serializers.ValidationError(
                "CBO is disabled. Budget will be set on Ad Set level. Please remove budget from here."
            )

        # B. iOS 14 Validation (New Logic)
        if data.get('is_ios14_campaign'):
            # Rule 1: Objective must be App Promotion
            if data.get('objective') != 'OUTCOME_APP_PROMOTION':
                 raise serializers.ValidationError(
                    "iOS 14+ Campaign option is only valid for 'App Promotion' objective."
                )
            
            # Rule 2: App ID is required
            if not data.get('ios14_app_id'):
                raise serializers.ValidationError(
                    "For iOS 14+ campaigns, 'ios14_app_id' is required. Please provide the App Store ID."
                )

        return data
    

#===========================================================================================


class CampaignUpdateSerializer(serializers.Serializer):

    
    campaign_id = serializers.CharField(
        required=True, 
        help_text="The unique ID of the campaign to update"
    )

    #  (Optional) ---
    name = serializers.CharField(required=False, max_length=255)
    
    status = serializers.ChoiceField(
        choices=['ACTIVE', 'PAUSED', 'ARCHIVED'], 
        required=False
    )

    special_ad_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    # --- FINANCIALS ---
    spend_cap = serializers.FloatField(required=False, min_value=1.0)
    daily_budget = serializers.FloatField(required=False, min_value=1.0)
    lifetime_budget = serializers.FloatField(required=False, min_value=1.0)
    
    bid_strategy = serializers.ChoiceField(
        choices=[
            ('LOWEST_COST_WITHOUT_CAP', 'Highest Volume'), 
            ('COST_CAP', 'Cost Cap'), 
            ('BID_CAP', 'Bid Cap')
        ],
        required=False
    )

    def validate(self, data):
        
        if data.get('daily_budget') and data.get('lifetime_budget'):
            raise serializers.ValidationError(
                "You cannot update both Daily and Lifetime budgets at the same time."
            )

        return data
    

class CampaignDeleteSerializer(serializers.Serializer):
    campaign_id = serializers.CharField(
        required=True, 
        help_text="The ID of the campaign to archive/delete"
    )


class CampaignToggleSerializer(serializers.Serializer):
    campaign_id = serializers.CharField(required=True)
    status = serializers.ChoiceField(
        choices=['ACTIVE', 'PAUSED'], 
        required=True,
        help_text="Send 'ACTIVE' to turn on, 'PAUSED' to turn off."
    )



class AdSetCreateSerializer(serializers.Serializer):
    
    # --- CONSTANTS (Dropdown Options) --
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused')
    ]

    GENDER_CHOICES = [
        (1, 'Male'),
        (2, 'Female')
    ]

    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('audience_network', 'Audience Network'),
        ('messenger', 'Messenger')
    ]

    GOAL_CHOICES = [
        ('LINK_CLICKS', 'Link Clicks'),
        ('IMPRESSIONS', 'Impressions'),
        ('REACH', 'Daily Unique Reach'),
        ('LANDING_PAGE_VIEWS', 'Landing Page Views')
    ]

    BILLING_CHOICES = [
        ('IMPRESSIONS', 'Impressions (CPM)'),
        ('LINK_CLICKS', 'Link Clicks (CPC)')
    ]

    # --- FIELDS ---

    # 1. Identity
    ad_account_id = serializers.CharField(required=True)
    campaign_id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    
    # ✅ Dropdown 1: Status
    status = serializers.ChoiceField(choices=STATUS_CHOICES, default='PAUSED')

    # 2. Budget & Schedule
    daily_budget = serializers.FloatField(required=False, min_value=1.0)
    lifetime_budget = serializers.FloatField(required=False, min_value=1.0)
    start_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField(required=False)

    # 3. Targeting
    geo_locations = serializers.JSONField(
        required=True, 
        initial={"countries": ["PK"]},
        help_text="Example: {'countries': ['PK']} or {'cities': [{'key': '...'}]}"
    )
    
    age_min = serializers.IntegerField(default=18, min_value=13)
    age_max = serializers.IntegerField(default=65, max_value=65)

    # ✅ Dropdown 2: Gender (Multi-Select)
    # ListField k andar ChoiceField lagaya hai taake list k andar bhi validation ho
    genders = serializers.ListField(
        child=serializers.ChoiceField(choices=GENDER_CHOICES),
        required=False,
        help_text="[1] for Male, [2] for Female"
    )
    
    interest_ids = serializers.ListField(child=serializers.CharField(), required=False)
    behavior_ids = serializers.ListField(child=serializers.CharField(), required=False)    # <-- NEW
    life_event_ids = serializers.ListField(child=serializers.CharField(), required=False)

    # ✅ Dropdown 3: Platforms (Multi-Select)
    publisher_platforms = serializers.ListField(
        child=serializers.ChoiceField(choices=PLATFORM_CHOICES),
        default=['facebook', 'instagram']
    )
    
    device_platforms = serializers.ListField(
        child=serializers.ChoiceField(choices=['mobile', 'desktop']),
        default=['mobile', 'desktop']
    )

    # ✅ Dropdown 4: Optimization Goals
    optimization_goal = serializers.ChoiceField(choices=GOAL_CHOICES, default='LINK_CLICKS')
    billing_event = serializers.ChoiceField(choices=BILLING_CHOICES, default='IMPRESSIONS')

    bid_amount = serializers.IntegerField(required=False)

    # --- VALIDATION ---
    def validate(self, data):
        # ... (Wohi purani validation logic budget wali) ...
        daily = data.get('daily_budget')
        lifetime = data.get('lifetime_budget')
        end = data.get('end_time')

        if daily and lifetime:
            raise serializers.ValidationError("Cannot set both Daily and Lifetime budget.")
        if lifetime and not end:
            raise serializers.ValidationError("Lifetime Budget requires an End Time.")
            
        return data
    


class AdSetUpdateSerializer(serializers.Serializer):
    # ID is Mandatory
    adset_id = serializers.CharField(required=True)

    # Optional Fields (User might send only one of these)
    name = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=['ACTIVE', 'PAUSED'], required=False)
    
    # Budget & Schedule
    daily_budget = serializers.FloatField(required=False, min_value=1.0)
    lifetime_budget = serializers.FloatField(required=False, min_value=1.0)
    start_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField(required=False)
    
    # Targeting (Optional Updates)
    geo_locations = serializers.JSONField(required=False)
    age_min = serializers.IntegerField(required=False, min_value=13)
    age_max = serializers.IntegerField(required=False, max_value=65)
    genders = serializers.ListField(child=serializers.IntegerField(), required=False)
    interest_ids = serializers.ListField(child=serializers.CharField(), required=False)
    
    # Bid Amount (If manual bidding is used)
    bid_amount = serializers.IntegerField(required=False)
