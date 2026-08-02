"""Read models for platform administration."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Q
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.demo_requests.models import DemoRequest
from apps.organisations.models import Membership, Organisation

from .models import SupportAccessGrant

User = get_user_model()


def platform_organisations(*, query: str = "", status: str = ""):
    owner_memberships = Membership.objects.filter(
        role=Membership.Role.OWNER,
        status=Membership.Status.ACTIVE,
    ).select_related("user")
    queryset = (
        Organisation.objects.all()
        .annotate(
            member_count=Count(
                "memberships",
                filter=Q(memberships__status=Membership.Status.ACTIVE),
                distinct=True,
            ),
            active_owner_count=Count(
                "memberships",
                filter=Q(
                    memberships__role=Membership.Role.OWNER,
                    memberships__status=Membership.Status.ACTIVE,
                ),
                distinct=True,
            ),
            workspace_count=Count("workspaces", distinct=True),
            decision_count=Count("decisions", distinct=True),
            active_decision_count=Count(
                "decisions",
                filter=~Q(decisions__status="archived"),
                distinct=True,
            ),
            pending_invitation_count=Count(
                "invitations",
                filter=Q(invitations__status="pending"),
                distinct=True,
            ),
        )
        .prefetch_related(
            Prefetch(
                "memberships",
                queryset=owner_memberships,
                to_attr="prefetched_platform_owners",
            )
        )
        .order_by("name", "id")
    )
    query = query.strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(slug__icontains=query)
            | Q(brand_name__icontains=query)
            | Q(memberships__user__email__icontains=query)
        ).distinct()
    if status in {Organisation.Status.ACTIVE, Organisation.Status.DEACTIVATED}:
        queryset = queryset.filter(status=status)
    return queryset


def platform_organisation_detail(*, organisation_id, administrator):
    organisation = (
        platform_organisations()
        .prefetch_related(
            Prefetch(
                "memberships",
                queryset=Membership.objects.select_related("user").order_by("user__email"),
            ),
            "invitations__invited_by",
            "workspaces",
        )
        .get(id=organisation_id)
    )
    organisation.current_platform_support_grant = (
        SupportAccessGrant.objects.filter(
            organisation=organisation,
            administrator=administrator,
            status=SupportAccessGrant.Status.ACTIVE,
            expires_at__gt=timezone.now(),
        )
        .select_related("administrator", "organisation", "revoked_by")
        .order_by("-expires_at")
        .first()
    )
    return organisation


def platform_users(*, query: str = "", state: str = ""):
    queryset = User.objects.annotate(
        organisation_count=Count(
            "organisation_memberships",
            filter=Q(organisation_memberships__status=Membership.Status.ACTIVE),
            distinct=True,
        ),
        active_owned_organisation_count=Count(
            "organisation_memberships",
            filter=Q(
                organisation_memberships__role=Membership.Role.OWNER,
                organisation_memberships__status=Membership.Status.ACTIVE,
            ),
            distinct=True,
        ),
    ).order_by("email")
    query = query.strip()
    if query:
        queryset = queryset.filter(
            Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    if state == "active":
        queryset = queryset.filter(is_active=True)
    elif state == "suspended":
        queryset = queryset.filter(is_active=False)
    elif state == "platform_admin":
        queryset = queryset.filter(platform_administrator__status="active")
    return queryset


def platform_audit_events(*, query: str = "", action: str = ""):
    queryset = AuditEvent.objects.select_related("actor", "organisation").order_by("-created_at")
    if action:
        queryset = queryset.filter(action__icontains=action.strip())
    if query.strip():
        needle = query.strip()
        queryset = queryset.filter(
            Q(action__icontains=needle)
            | Q(object_type__icontains=needle)
            | Q(object_id__icontains=needle)
            | Q(actor__email__icontains=needle)
            | Q(organisation__name__icontains=needle)
        )
    return queryset


def platform_demo_requests(*, status: str = "", query: str = ""):
    queryset = DemoRequest.objects.all().order_by("-created_at")
    if status in {choice for choice, _ in DemoRequest.Status.choices}:
        queryset = queryset.filter(status=status)
    if query.strip():
        needle = query.strip()
        queryset = queryset.filter(
            Q(full_name__icontains=needle)
            | Q(work_email__icontains=needle)
            | Q(organisation_name__icontains=needle)
            | Q(message__icontains=needle)
        )
    return queryset
