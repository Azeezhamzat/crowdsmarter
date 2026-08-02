# Generated manually for CrowdSmarter Phase 13.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("foresight", "0003_systems_mapping"),
        ("decisions", "0003_decision_template_provenance"),
        ("decision_options", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScenarioSet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=240)),
                ("purpose", models.TextField()),
                ("axis_x_low_label", models.CharField(max_length=160)),
                ("axis_x_high_label", models.CharField(max_length=160)),
                ("axis_y_low_label", models.CharField(max_length=160)),
                ("axis_y_high_label", models.CharField(max_length=160)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("active", "Active"),
                            ("complete", "Complete"),
                            ("archived", "Archived"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "axis_x_driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scenario_sets_as_x_axis",
                        to="foresight.driver",
                    ),
                ),
                (
                    "axis_y_driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scenario_sets_as_y_axis",
                        to="foresight.driver",
                    ),
                ),
                (
                    "canvas",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scenario_sets",
                        to="foresight.foresightcanvas",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_scenario_sets",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "linked_decision",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="foresight_scenario_sets",
                        to="decisions.decision",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="owned_scenario_sets",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at", "title"],
                "constraints": [
                    models.CheckConstraint(
                        condition=~models.Q(title=""),
                        name="scenario_set_title_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(
                            axis_x_driver=models.F("axis_y_driver")
                        ),
                        name="scenario_set_axes_distinct",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            status__in=["draft", "active", "complete", "archived"]
                        ),
                        name="scenario_set_status_valid",
                    ),
                    models.UniqueConstraint(
                        fields=("canvas", "title"),
                        name="unique_scenario_set_title_per_canvas",
                    ),
                ],
                "indexes": [
                    models.Index(
                        fields=["canvas", "status", "-updated_at"],
                        name="scenario_set_canvas_idx",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Scenario",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=240)),
                ("code", models.CharField(max_length=40)),
                (
                    "axis_x_position",
                    models.CharField(
                        choices=[("low", "Low"), ("high", "High")], max_length=10
                    ),
                ),
                (
                    "axis_y_position",
                    models.CharField(
                        choices=[("low", "Low"), ("high", "High")], max_length=10
                    ),
                ),
                ("headline", models.CharField(max_length=320)),
                ("narrative", models.TextField()),
                ("key_assumptions", models.TextField()),
                ("opportunities", models.TextField(blank=True)),
                ("threats", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("reviewed", "Reviewed")],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_scenarios",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "scenario_set",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scenarios",
                        to="foresight.scenarioset",
                    ),
                ),
            ],
            options={
                "ordering": ["axis_y_position", "axis_x_position", "title"],
                "constraints": [
                    models.CheckConstraint(
                        condition=~models.Q(title=""), name="scenario_title_not_empty"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(axis_x_position__in=["low", "high"]),
                        name="scenario_x_position_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(axis_y_position__in=["low", "high"]),
                        name="scenario_y_position_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(status__in=["draft", "reviewed"]),
                        name="scenario_status_valid",
                    ),
                    models.UniqueConstraint(
                        fields=("scenario_set", "axis_x_position", "axis_y_position"),
                        name="unique_scenario_quadrant",
                    ),
                    models.UniqueConstraint(
                        fields=("scenario_set", "code"),
                        name="unique_scenario_code_per_set",
                    ),
                    models.UniqueConstraint(
                        fields=("scenario_set", "title"),
                        name="unique_scenario_title_per_set",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ScenarioDriverState",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("strengthening", "Strengthening"),
                            ("weakening", "Weakening"),
                            ("stable", "Stable"),
                            ("volatile", "Volatile"),
                            ("transformed", "Transformed"),
                            ("uncertain", "Uncertain"),
                        ],
                        max_length=20,
                    ),
                ),
                ("salience", models.PositiveSmallIntegerField(default=3)),
                ("description", models.TextField()),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_scenario_driver_states",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scenario_states",
                        to="foresight.driver",
                    ),
                ),
                (
                    "scenario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="driver_states",
                        to="foresight.scenario",
                    ),
                ),
            ],
            options={
                "ordering": ["-salience", "driver__title"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(salience__gte=1, salience__lte=5),
                        name="scenario_driver_salience_valid",
                    ),
                    models.UniqueConstraint(
                        fields=("scenario", "driver"),
                        name="unique_driver_state_per_scenario",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ScenarioReview",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plausibility", models.PositiveSmallIntegerField(default=3)),
                ("internal_consistency", models.PositiveSmallIntegerField(default=3)),
                ("distinctiveness", models.PositiveSmallIntegerField(default=3)),
                ("usefulness", models.PositiveSmallIntegerField(default=3)),
                ("confidence", models.PositiveSmallIntegerField(default=3)),
                ("comment", models.TextField(blank=True)),
                (
                    "reviewer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scenario_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "scenario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="foresight.scenario",
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(plausibility__gte=1, plausibility__lte=5),
                        name="scenario_review_plausibility_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            internal_consistency__gte=1,
                            internal_consistency__lte=5,
                        ),
                        name="scenario_review_consistency_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            distinctiveness__gte=1, distinctiveness__lte=5
                        ),
                        name="scenario_review_distinctiveness_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(usefulness__gte=1, usefulness__lte=5),
                        name="scenario_review_usefulness_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(confidence__gte=1, confidence__lte=5),
                        name="scenario_review_confidence_valid",
                    ),
                    models.UniqueConstraint(
                        fields=("scenario", "reviewer"),
                        name="unique_member_review_per_scenario",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="WindTunnelAssessment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "verdict",
                    models.CharField(
                        choices=[
                            ("robust", "Robust"),
                            ("adaptable", "Adaptable with conditions"),
                            ("vulnerable", "Vulnerable"),
                            ("infeasible", "Infeasible"),
                            ("uncertain", "Uncertain"),
                        ],
                        max_length=20,
                    ),
                ),
                ("desirability", models.PositiveSmallIntegerField(default=3)),
                ("feasibility", models.PositiveSmallIntegerField(default=3)),
                ("resilience", models.PositiveSmallIntegerField(default=3)),
                ("rationale", models.TextField()),
                ("conditions_for_success", models.TextField(blank=True)),
                ("vulnerabilities", models.TextField(blank=True)),
                ("mitigations", models.TextField(blank=True)),
                (
                    "assessed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="wind_tunnel_assessments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "option",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scenario_assessments",
                        to="decision_options.decisionoption",
                    ),
                ),
                (
                    "scenario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wind_tunnel_assessments",
                        to="foresight.scenario",
                    ),
                ),
            ],
            options={
                "ordering": ["option__title", "scenario__title"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(desirability__gte=1, desirability__lte=5),
                        name="wind_tunnel_desirability_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(feasibility__gte=1, feasibility__lte=5),
                        name="wind_tunnel_feasibility_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(resilience__gte=1, resilience__lte=5),
                        name="wind_tunnel_resilience_valid",
                    ),
                    models.UniqueConstraint(
                        fields=("scenario", "option"),
                        name="unique_option_assessment_per_scenario",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Signpost",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=240)),
                ("description", models.TextField()),
                ("indicator", models.CharField(max_length=500)),
                ("threshold", models.CharField(max_length=500)),
                (
                    "direction",
                    models.CharField(
                        choices=[
                            ("above", "Above threshold"),
                            ("below", "Below threshold"),
                            ("rising", "Rising"),
                            ("falling", "Falling"),
                            ("change", "Material change"),
                            ("qualitative", "Qualitative judgement"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "review_cadence",
                    models.CharField(
                        choices=[
                            ("monthly", "Monthly"),
                            ("quarterly", "Quarterly"),
                            ("semiannual", "Every six months"),
                            ("annual", "Annual"),
                            ("event_driven", "Event-driven"),
                        ],
                        max_length=20,
                    ),
                ),
                ("source_notes", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("paused", "Paused"),
                            ("retired", "Retired"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_foresight_signposts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="owned_foresight_signposts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "scenario_set",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="signposts",
                        to="foresight.scenarioset",
                    ),
                ),
            ],
            options={
                "ordering": ["status", "title"],
                "constraints": [
                    models.CheckConstraint(
                        condition=~models.Q(title=""), name="signpost_title_not_empty"
                    ),
                    models.UniqueConstraint(
                        fields=("scenario_set", "title"),
                        name="unique_signpost_title_per_set",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ScenarioSignpost",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "relationship",
                    models.CharField(
                        choices=[
                            ("supports", "Supports"),
                            ("contradicts", "Contradicts"),
                            ("contextual", "Contextual"),
                        ],
                        max_length=20,
                    ),
                ),
                ("rationale", models.TextField()),
                (
                    "linked_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="linked_scenario_signposts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "scenario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="signpost_links",
                        to="foresight.scenario",
                    ),
                ),
                (
                    "signpost",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scenario_links",
                        to="foresight.signpost",
                    ),
                ),
            ],
            options={
                "ordering": ["scenario__title"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("signpost", "scenario"),
                        name="unique_signpost_scenario_link",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="signpost",
            name="scenarios",
            field=models.ManyToManyField(
                related_name="signposts",
                through="foresight.ScenarioSignpost",
                to="foresight.scenario",
            ),
        ),
        migrations.CreateModel(
            name="SignpostObservation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("observed_on", models.DateField()),
                ("value", models.CharField(max_length=500)),
                (
                    "assessment",
                    models.CharField(
                        choices=[
                            ("no_change", "No meaningful change"),
                            ("weak", "Weak movement"),
                            ("moderate", "Moderate movement"),
                            ("strong", "Strong movement"),
                            ("contradictory", "Contradictory evidence"),
                        ],
                        max_length=20,
                    ),
                ),
                ("evidence", models.TextField()),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_signpost_observations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "signpost",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="observations",
                        to="foresight.signpost",
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="signpost_observations",
                        to="foresight.source",
                    ),
                ),
            ],
            options={"ordering": ["-observed_on", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ScenarioImplicationLink",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "effect",
                    models.CharField(
                        choices=[
                            ("amplifies", "Amplifies"),
                            ("reduces", "Reduces"),
                            ("changes", "Changes"),
                            ("triggers", "Triggers"),
                        ],
                        max_length=20,
                    ),
                ),
                ("rationale", models.TextField()),
                (
                    "implication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scenario_links",
                        to="foresight.strategicimplication",
                    ),
                ),
                (
                    "linked_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="linked_scenario_implications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "scenario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="implication_links",
                        to="foresight.scenario",
                    ),
                ),
            ],
            options={
                "ordering": ["implication__title"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("scenario", "implication"),
                        name="unique_implication_per_scenario",
                    )
                ],
            },
        ),
    ]
