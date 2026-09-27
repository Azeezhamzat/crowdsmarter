"""Tenant-safe selectors for scenario planning and adaptive signposts."""

from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404

from .models import (
    Scenario,
    ScenarioDriverState,
    ScenarioImplicationLink,
    ScenarioReview,
    ScenarioSet,
    ScenarioSignpost,
    Signpost,
    SignpostObservation,
    WindTunnelAssessment,
)
from .selectors import user_organisations


def scenario_sets_for_canvas(*, user, canvas_id):  # type: ignore[no-untyped-def]
    return (
        ScenarioSet.objects.filter(
            canvas_id=canvas_id,
            canvas__organisation__in=user_organisations(user),
        )
        .select_related(
            "canvas__organisation",
            "axis_x_driver",
            "axis_y_driver",
            "linked_decision",
            "owner",
            "created_by",
        )
        .annotate(
            scenario_count=Count("scenarios", distinct=True),
            signpost_count=Count("signposts", distinct=True),
        )
    )


def scenario_set_for_user(*, user, scenario_set_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        ScenarioSet.objects.filter(
            canvas__organisation__in=user_organisations(user)
        ).select_related(
            "canvas__organisation",
            "axis_x_driver",
            "axis_y_driver",
            "linked_decision",
            "owner",
            "created_by",
        ),
        id=scenario_set_id,
    )


def scenario_set_workspace_for_user(*, user, scenario_set_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        ScenarioSet.objects.filter(canvas__organisation__in=user_organisations(user))
        .select_related(
            "canvas__organisation",
            "axis_x_driver",
            "axis_y_driver",
            "linked_decision",
            "owner",
            "created_by",
        )
        .prefetch_related(
            "linked_decision__options",
            Prefetch(
                "scenarios",
                queryset=Scenario.objects.select_related("created_by").prefetch_related(
                    Prefetch(
                        "driver_states",
                        queryset=ScenarioDriverState.objects.select_related("driver", "created_by"),
                    ),
                    Prefetch(
                        "reviews",
                        queryset=ScenarioReview.objects.select_related("reviewer"),
                    ),
                    Prefetch(
                        "wind_tunnel_assessments",
                        queryset=WindTunnelAssessment.objects.select_related(
                            "option", "option__decision", "assessed_by"
                        ),
                    ),
                    Prefetch(
                        "implication_links",
                        queryset=ScenarioImplicationLink.objects.select_related(
                            "implication", "linked_by"
                        ),
                    ),
                    Prefetch(
                        "signpost_links",
                        queryset=ScenarioSignpost.objects.select_related("signpost", "linked_by"),
                    ),
                ),
            ),
            Prefetch(
                "signposts",
                queryset=Signpost.objects.select_related("owner", "created_by").prefetch_related(
                    Prefetch(
                        "scenario_links",
                        queryset=ScenarioSignpost.objects.select_related("scenario", "linked_by"),
                    ),
                    Prefetch(
                        "observations",
                        queryset=SignpostObservation.objects.select_related("source", "created_by"),
                    ),
                ),
            ),
        ),
        id=scenario_set_id,
    )


def scenario_for_user(*, user, scenario_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        Scenario.objects.filter(
            scenario_set__canvas__organisation__in=user_organisations(user)
        ).select_related(
            "scenario_set__canvas__organisation",
            "scenario_set__linked_decision",
            "created_by",
        ),
        id=scenario_id,
    )


def signpost_for_user(*, user, signpost_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        Signpost.objects.filter(
            scenario_set__canvas__organisation__in=user_organisations(user)
        ).select_related("scenario_set__canvas__organisation", "owner", "created_by"),
        id=signpost_id,
    )
