"""Tenant-safe selectors for systems and futures mapping."""

from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404

from apps.organisations.selectors import organisation_for_user

from .models import (
    CausalRelationship,
    Driver,
    FeedbackLoop,
    FeedbackLoopDriver,
    ForesightCanvas,
    FuturesWheelConsequence,
    ScenarioSet,
    StrategicImplication,
    SystemStakeholder,
    ThreeHorizonItem,
)
from .selectors import user_organisations


def canvases_for_organisation(*, user, organisation_id):  # type: ignore[no-untyped-def]
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    return (
        ForesightCanvas.objects.filter(organisation=organisation)
        .select_related("owner", "created_by")
        .annotate(
            driver_count=Count("drivers", distinct=True),
            implication_count=Count("implications", distinct=True),
        )
    )


def canvas_for_user(*, user, canvas_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        ForesightCanvas.objects.filter(organisation__in=user_organisations(user)).select_related(
            "organisation", "owner", "created_by"
        ),
        id=canvas_id,
    )


def canvas_workspace_for_user(*, user, canvas_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        ForesightCanvas.objects.filter(organisation__in=user_organisations(user))
        .select_related("organisation", "owner", "created_by")
        .prefetch_related(
            Prefetch(
                "drivers",
                queryset=Driver.objects.select_related("owner", "created_by").prefetch_related(
                    "signal_links__signal"
                ),
            ),
            Prefetch("stakeholders", queryset=SystemStakeholder.objects.select_related("created_by")),
            Prefetch(
                "relationships",
                queryset=CausalRelationship.objects.select_related(
                    "source_driver", "target_driver", "created_by"
                ),
            ),
            Prefetch(
                "feedback_loops",
                queryset=FeedbackLoop.objects.select_related("created_by").prefetch_related(
                    Prefetch(
                        "driver_links",
                        queryset=FeedbackLoopDriver.objects.select_related("driver"),
                    )
                ),
            ),
            Prefetch(
                "consequences",
                queryset=FuturesWheelConsequence.objects.select_related(
                    "originating_driver", "parent", "created_by"
                ),
            ),
            Prefetch("horizon_items", queryset=ThreeHorizonItem.objects.select_related("created_by")),
            Prefetch(
                "scenario_sets",
                queryset=ScenarioSet.objects.select_related(
                    "axis_x_driver", "axis_y_driver", "linked_decision", "owner", "created_by"
                ).annotate(
                    scenario_count=Count("scenarios", distinct=True),
                    signpost_count=Count("signposts", distinct=True),
                ),
            ),
            Prefetch(
                "implications",
                queryset=StrategicImplication.objects.select_related(
                    "owner", "created_by", "linked_decision"
                ).prefetch_related("drivers"),
            ),
        ),
        id=canvas_id,
    )


def driver_for_user(*, user, driver_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        Driver.objects.filter(canvas__organisation__in=user_organisations(user)).select_related(
            "canvas__organisation", "owner", "created_by"
        ),
        id=driver_id,
    )


def implication_for_user(*, user, implication_id):  # type: ignore[no-untyped-def]
    return get_object_or_404(
        StrategicImplication.objects.filter(
            canvas__organisation__in=user_organisations(user)
        ).select_related("canvas__organisation", "owner", "created_by", "linked_decision"),
        id=implication_id,
    )
