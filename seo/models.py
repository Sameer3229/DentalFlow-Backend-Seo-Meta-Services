from django.db import models
from core.base_model import BaseModel
from user.models import User

class SERankingKeyword(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    block_type = models.CharField(max_length=50, blank=True, null=True)
    block_position = models.IntegerField(blank=True, null=True)
    position = models.IntegerField(blank=True, null=True)
    prev_pos = models.IntegerField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    cpc = models.FloatField(blank=True, null=True)
    competition = models.FloatField(blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    difficulty = models.IntegerField(blank=True, null=True)
    total_sites = models.IntegerField(blank=True, null=True)
    traffic = models.IntegerField(blank=True, null=True)
    traffic_percent = models.FloatField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.keyword} - {self.domain}"

class Competitor(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    domain = models.CharField(max_length=255)
    common_keywords = models.IntegerField()

    def __str__(self):
        return self.domain
    
class SimilarKeyword(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    cpc = models.FloatField(default=0)
    difficulty = models.IntegerField(default=0)
    volume = models.IntegerField(default=0)
    competition = models.FloatField(default=0)
    serp_features = models.JSONField(default=list)
    intents = models.JSONField(default=list)
    history_trend = models.JSONField(default=dict)

    def __str__(self):
        return self.keyword

class RelatedKeyword(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    cpc = models.FloatField(default=0)
    difficulty = models.IntegerField(default=0)
    volume = models.IntegerField(default=0)
    competition = models.FloatField(default=0)
    serp_features = models.JSONField(default=list)
    intents = models.JSONField(default=list)
    history_trend = models.JSONField(default=dict)

    def __str__(self):
        return self.keyword
    
class DomainHistory(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    domain = models.CharField(max_length=255)
    year = models.IntegerField()
    month = models.IntegerField()
    keywords_count = models.IntegerField()
    traffic_sum = models.IntegerField()
    top1_2 = models.IntegerField()
    top3_5 = models.IntegerField()
    top6_8 = models.IntegerField()
    top9_11 = models.IntegerField()
    price_sum = models.FloatField()

    def __str__(self):
        return f"{self.domain} - {self.year}/{self.month}"
    
class AuditReport(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    total_pages = models.IntegerField(null=True, blank=True)
    total_warnings = models.IntegerField(null=True, blank=True)
    total_errors = models.IntegerField(null=True, blank=True)
    total_passed = models.IntegerField(null=True, blank=True)
    total_notices = models.IntegerField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)
    dp_dt = models.IntegerField(null=True, blank=True)
    dp_domain = models.CharField(max_length=255, null=True, blank=True)
    dp_domains = models.CharField(max_length=255, null=True, blank=True)
    dp_expdate = models.CharField(max_length=50, null=True, blank=True)
    dp_updated = models.CharField(max_length=50, null=True, blank=True)
    dp_backlinks = models.CharField(max_length=50, null=True, blank=True)
    dp_all_checked = models.BooleanField(default=False)
    dp_index_google = models.CharField(max_length=50, null=True, blank=True)
    score_percent = models.IntegerField(null=True, blank=True)
    weighted_score_percent = models.IntegerField(null=True, blank=True)
    screenshot = models.TextField(null=True, blank=True)
    audit_time = models.CharField(max_length=50, null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    chromeux_mobile = models.JSONField(null=True, blank=True)
    chromeux_desktop = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Audit Report - {self.dp_domain} ({self.score_percent}%)"
    

class SEOAuditLink(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    url = models.URLField(max_length=500)
    link_id = models.CharField(max_length=100)
    status = models.CharField(max_length=10)
    type = models.CharField(max_length=50)
    source_url = models.URLField(max_length=500, blank=True, null=True)
    source_noindex = models.CharField(max_length=10, blank=True, null=True)
    nofollow = models.CharField(max_length=10, blank=True, null=True)
    alt = models.TextField(blank=True, null=True)
    anchor_type = models.CharField(max_length=50, blank=True, null=True)
    anchor = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Link {self.url}"

class SEOAuditIssue(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    url = models.URLField(max_length=500)
    issue_code = models.CharField(max_length=50)
    issue_type = models.CharField(max_length=50)
    group = models.CharField(max_length=50)
    snippet_value = models.JSONField()  
    time_check = models.DateTimeField()
    inlinks = models.IntegerField(default=0)
    redirect = models.URLField(max_length=500, blank=True, null=True)
    refpages = models.IntegerField(default=0)
    issues_count = models.IntegerField(default=0)
    num_keywords = models.CharField(max_length=255, blank=True, null=True)
    warnings_count = models.IntegerField(default=0)
    traffic_forecast = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Issue {self.issue_code} for {self.url}"
    
class SEOAIDescription(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    description = models.TextField()

    def __str__(self):
        return f"name {self.user.first_name}"