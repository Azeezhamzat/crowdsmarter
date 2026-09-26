"""Tenant-safe decision-method selectors."""

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404

from apps.organisations.models import Membership
from apps.organisations.selectors import organisation_for_user

from .models import DecisionMethod, DecisionMethodUsage, DecisionMethodVersion


def _membership(*, user, organisation):  # type: ignore[no-untyped-def]
    return Membership.objects.filter(
        organisation=organisation, user=user, status=Membership.Status.ACTIVE
    ).first()


def methods_for_organisation(*, user, organisation_id):  # type: ignore[no-untyped-def]
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    membership = _membership(user=user, organisation=organisation)
    queryset = DecisionMethod.objects.filter(organisation=organisation).select_related(
        "current_version", "created_by"
    )
    if membership and membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        return queryset.prefetch_related("versions")
    return queryset.filter(status=DecisionMethod.Status.APPROVED).prefetch_related(
        Prefetch(
            "versions",
            queryset=DecisionMethodVersion.objects.filter(
                status=DecisionMethodVersion.Status.APPROVED
            ),
        )
    )


def approved_methods_for_organisation(*, user, organisation_id):  # type: ignore[no-untyped-def]
    return methods_for_organisation(user=user, organisation_id=organisation_id).filter(
        status=DecisionMethod.Status.APPROVED, current_version__isnull=False
    )


def method_for_user(*, user, method_id):  # type: ignore[no-untyped-def]
    manageable_orgs = Membership.objects.filter(
        user=user,
        status=Membership.Status.ACTIVE,
        role__in=[Membership.Role.OWNER, Membership.Role.ADMIN],
    ).values("organisation_id")
    queryset = (
        DecisionMethod.objects.select_related("organisation", "current_version", "created_by")
        .filter(
            organisation__memberships__user=user,
            organisation__memberships__status=Membership.Status.ACTIVE,
        )
        .filter(Q(status=DecisionMethod.Status.APPROVED) | Q(organisation_id__in=manageable_orgs))
        .distinct()
    )
    method = get_object_or_404(queryset, id=method_id)
    membership = _membership(user=user, organisation=method.organisation)
    versions = DecisionMethodVersion.objects.all()
    if not membership or membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        versions = versions.filter(status=DecisionMethodVersion.Status.APPROVED)
    return (
        DecisionMethod.objects.filter(id=method.id)
        .select_related("organisation", "current_version", "created_by")
        .prefetch_related(Prefetch("versions", queryset=versions))
        .get()
    )


def version_for_user(*, user, version_id):  # type: ignore[no-untyped-def]
    manageable_orgs = Membership.objects.filter(
        user=user,
        status=Membership.Status.ACTIVE,
        role__in=[Membership.Role.OWNER, Membership.Role.ADMIN],
    ).values("organisation_id")
    return get_object_or_404(
        DecisionMethodVersion.objects.select_related(
            "method", "organisation", "created_by", "approved_by"
        )
        .filter(
            organisation__memberships__user=user,
            organisation__memberships__status=Membership.Status.ACTIVE,
        )
        .filter(
            Q(status=DecisionMethodVersion.Status.APPROVED) | Q(organisation_id__in=manageable_orgs)
        )
        .distinct(),
        id=version_id,
    )


def usages_for_organisation(*, user, organisation_id):  # type: ignore[no-untyped-def]
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    return DecisionMethodUsage.objects.filter(organisation=organisation).select_related(
        "method_version__method", "decision", "applied_by"
    )
