"""Privacy-conscious public demo-request records."""

from django.db import models

from apps.core.models import UUIDTimeStampedModel


class DemoRequest(UUIDTimeStampedModel):
    """A prospective-customer request submitted through the public website."""

    class OrganisationSize(models.TextChoices):
        ONE_TO_TEN = "1-10", "1-10 people"
        ELEVEN_TO_FIFTY = "11-50", "11-50 people"
        FIFTY_ONE_TO_TWO_HUNDRED = "51-200", "51-200 people"
        TWO_HUNDRED_ONE_TO_THOUSAND = "201-1000", "201-1,000 people"
        OVER_THOUSAND = "1000+", "More than 1,000 people"
        NOT_SURE = "not_sure", "Not sure"

    class PrimaryNeed(models.TextChoices):
        STRATEGIC_FORESIGHT = "strategic_foresight", "Strategic foresight"
        DECISION_GOVERNANCE = "decision_governance", "Decision governance"
        COLLECTIVE_INTELLIGENCE = "collective_intelligence", "Collective intelligence"
        PORTFOLIO_PRIORITISATION = "portfolio_prioritisation", "Portfolio prioritisation"
        ORGANISATIONAL_LEARNING = "organisational_learning", "Organisational learning"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        CLOSED = "closed", "Closed"

    full_name = models.CharField(max_length=160)
    work_email = models.EmailField()
    organisation_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=160, blank=True)
    organisation_size = models.CharField(
        max_length=20,
        choices=OrganisationSize.choices,
        default=OrganisationSize.NOT_SURE,
    )
    primary_need = models.CharField(max_length=40, choices=PrimaryNeed.choices)
    message = models.TextField(blank=True, max_length=2000)
    consent_to_contact = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="demo_status_created_idx"),
            models.Index(fields=["work_email", "created_at"], name="demo_email_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(full_name=""),
                name="demo_request_full_name_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(organisation_name=""),
                name="demo_request_organisation_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(consent_to_contact=True),
                name="demo_request_contact_consent_required",
            ),
        ]

    def clean(self) -> None:
        """Normalise public inputs before persistence."""
        super().clean()
        self.full_name = self.full_name.strip()
        self.work_email = self.work_email.strip().lower()
        self.organisation_name = self.organisation_name.strip()
        self.job_title = self.job_title.strip()
        self.message = self.message.strip()

    def __str__(self) -> str:
        return f"{self.full_name} - {self.organisation_name}"
