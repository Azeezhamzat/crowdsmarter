from django.contrib import admin

from .models import (
    ContributionPreference,
    ContributionRequest,
    ContributionReview,
    ContributionSubmission,
    FacilitationAgendaItem,
    FacilitationAuthorityResponse,
    FacilitationQualityReview,
    FacilitationRecord,
    FacilitationSession,
    SessionParticipant,
)

admin.site.register(ContributionRequest)
admin.site.register(ContributionSubmission)
admin.site.register(ContributionReview)
admin.site.register(FacilitationSession)
admin.site.register(FacilitationAgendaItem)
admin.site.register(SessionParticipant)
admin.site.register(FacilitationRecord)
admin.site.register(FacilitationAuthorityResponse)
admin.site.register(FacilitationQualityReview)
admin.site.register(ContributionPreference)
