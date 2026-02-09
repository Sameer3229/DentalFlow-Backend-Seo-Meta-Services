from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class FacebookProfile(models.Model):
    # User ko link kar rahe hain taa ke pata ho ye kis client ka data hai
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='facebook')
    
    # Ye wo 'Chabi' (Token) hai jo hum Facebook se le kar save karenge
    access_token = models.TextField()
    
    # Ye wo Page hai jo User ne select kiya hai (e.g. mo_elias_d)
    page_id = models.CharField(max_length=50, blank=True, null=True)
    page_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Time stamp (kabhi debug karna para to kaam ayega)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FB Connection: {self.user.username} - {self.page_name}"
    



#==================================================================================

# class FacebookCampaign(models.Model):
#     class Status(models.TextChoices):
#         ACTIVE = 'ACTIVE', 'Active'
#         PAUSED = 'PAUSED', 'Paused'
#         ARCHIVED = 'ARCHIVED', 'Archived'

#     class Objective(models.TextChoices):
#         OUTCOME_SALES = 'OUTCOME_SALES', 'Sales'
#         OUTCOME_LEADS = 'OUTCOME_LEADS', 'Leads'
#         OUTCOME_TRAFFIC = 'OUTCOME_TRAFFIC', 'Traffic'
#         OUTCOME_AWARENESS = 'OUTCOME_AWARENESS', 'Awareness'
#         OUTCOME_ENGAGEMENT = 'OUTCOME_ENGAGEMENT', 'Engagement'
#         OUTCOME_APP_PROMOTION = 'OUTCOME_APP_PROMOTION', 'App Promotion'
    
#     class BidStrategy(models.TextChoices):
#         LOWEST_COST_WITHOUT_CAP = 'LOWEST_COST_WITHOUT_CAP', 'Highest Volume'
#         COST_CAP = 'COST_CAP', 'Cost per Result Goal'
#         BID_CAP = 'BID_CAP', 'Bid Cap'

#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="fb_campaigns"
#     )
#     campaign_id = models.CharField(max_length=50, unique=True)
#     ad_account_id = models.CharField(max_length=50)
#     name = models.CharField(max_length=255)
