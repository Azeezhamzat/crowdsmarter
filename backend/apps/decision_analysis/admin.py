from django.contrib import admin

from .models import DecisionIssue, DecisionQualityReview, ExecutiveDecisionSummary

admin.site.register(DecisionIssue)
admin.site.register(DecisionQualityReview)
admin.site.register(ExecutiveDecisionSummary)
