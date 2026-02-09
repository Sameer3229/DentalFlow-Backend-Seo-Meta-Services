from django.contrib import admin
from seo.models import(
    SERankingKeyword,
    Competitor,
    SimilarKeyword,
    RelatedKeyword,
    DomainHistory,
    AuditReport,
    SEOAuditLink,
    SEOAuditIssue,
    SEOAIDescription
)

admin.site.register(SERankingKeyword)
admin.site.register(Competitor)
admin.site.register(SimilarKeyword)
admin.site.register(RelatedKeyword)
admin.site.register(DomainHistory)
admin.site.register(AuditReport)
admin.site.register(SEOAuditLink)
admin.site.register(SEOAuditIssue)
admin.site.register(SEOAIDescription)