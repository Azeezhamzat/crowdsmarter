"""Seed the flagship anticipatory-commons demonstration: a free, self-organising
group deciding together about local flood-season resilience, driven entirely
through the real service layer (the same functions the product itself uses,
including ``apps.accounts.services.sign_up`` - the exact self-serve entry
point a real visitor uses).

This is the worked example for the "start your own commons" pitch: a concrete,
inspectable instance of the ``anticipatory_commons`` template moving through
Anticipate (open signal-sharing), Deliberate, Decide, Act, and Learn.

Run with --dry-run first to preview without committing.
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.services import sign_up
from apps.collaboration.models import DiscussionEntry
from apps.collaboration.services import create_discussion_entry
from apps.decision_options.models import DecisionOption
from apps.decision_options.services import create_option
from apps.decisions.finalisation import finalise_decision
from apps.decisions.models import Decision
from apps.decisions.services import create_decision, transition_decision
from apps.evidence.services import create_evidence
from apps.assumptions.services import create_assumption
from apps.ideation.services import cast_vote, create_session, identify_participant, open_session, post_comment, submit_idea
from apps.lessons.services import create_lesson
from apps.organisations.models import Membership, Organisation
from apps.participants.models import Participant
from apps.participants.services import add_participant
from apps.positions.services import submit_position
from apps.reviews.services import complete_outcome_review, open_outcome_review, record_commitment, start_implementation
from apps.risks.services import create_risk
from apps.workspaces.models import Workspace

ORG_SLUG = "riverside-climate-resilience-commons"
DECISION_TITLE = "Prepare the riverside neighbourhood for the next flood season"

# (first, last, is_steward)
MEMBERS = [
    ("Nia", "Osei", True),
    ("Tomas", "Reyes", False),
    ("Halima", "Warsame", False),
    ("Jonas", "Berger", False),
    ("Priya", "Chandran", False),
    ("Leilani", "Kahale", False),
    ("Femi", "Adeyemi", False),
    ("Sana", "Rahimi", False),
]
assert len(MEMBERS) == 8

SIGNAL_NOTES = [
    "Water levels at the old mill gauge were the highest recorded for this time of year.",
    "Three households on Elm Court reported basement seepage after last week's rain.",
    "The regional forecast is calling for a wetter-than-average season again.",
    "The community garden's drainage ditch is silted up and hasn't been cleared this year.",
    "Insurance renewal notices this year flagged the block as higher flood risk than before.",
    "The old warning siren at the footbridge has not worked reliably in two seasons.",
    "A neighbouring watershed group upstream shared their culvert-capacity survey with us.",
    "Several elders remember a worse flood two decades ago and how the response fell short.",
]

DISCUSSION_NOTES = [
    "Worth checking this against what the upstream watershed group is seeing.",
    "This matches what a few of us have noticed on our own streets.",
    "We should weigh this against what we could actually get done before the season starts.",
    "I'd want to hear from the households most affected before we settle on one response.",
    "This is useful, but we should be honest about what we can't fix this season.",
]

POSITION_BODIES = [
    "Supportable given what we've heard, as long as someone is clearly accountable for it.",
    "I can back this, but only if the timeline is realistic before the season starts.",
    "The households most at risk should carry real weight here, not just a vote each.",
    "Reasonable, though I'd want a clear point at which we check whether it's working.",
]

IMPLEMENTATION_UPDATES = [
    "Drainage ditch clearing is scheduled with the borough for next week.",
    "Three households have been connected with the flood-response contact list.",
    "The warning system check is delayed a few days waiting on a part.",
    "Sandbag stock has been confirmed and located at the community hall.",
]

LESSON_NOTES = [
    "Starting the signal-sharing earlier in the season would have given more lead time.",
    "Involving the most-affected households from the start made the response more realistic.",
    "We underestimated how long the borough's own scheduling would take.",
    "Keeping the record open, not just the final decision, made it easier to explain later.",
]


class Command(BaseCommand):
    help = "Seed the flagship anticipatory-commons demonstration end to end, through the real service layer."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Roll back all changes at the end.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        random.seed(20260826)

        with transaction.atomic():
            org = self._get_or_create_org()
            members = self._get_or_create_members(org)
            steward = members[0]

            self._stage_anticipate(org, members)
            decision = self._run_commons_decision(org, members)
            self._verify(org, decision, members)

            if dry_run:
                self.stdout.write(self.style.WARNING("--dry-run: rolling back."))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS("Committed."))

    # ------------------------------------------------------------------ setup

    def _get_or_create_org(self) -> Organisation:
        existing = Organisation.objects.filter(slug=ORG_SLUG).first()
        if existing is not None:
            return existing
        first, last, _ = MEMBERS[0]
        email = f"{first.lower()}.{last.lower()}@{ORG_SLUG}.example"
        # The exact self-serve entry point a real visitor uses: apps.accounts.services.sign_up.
        _steward_user, organisation = sign_up(
            email=email,
            password="not-a-real-login-Cs!20260826",
            first_name=first,
            last_name=last,
            organisation_name="Riverside Climate Resilience Commons",
        )
        return organisation

    def _get_or_create_members(self, org: Organisation) -> list:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        people = []
        for index, (first, last, is_steward) in enumerate(MEMBERS):
            email = f"{first.lower()}.{last.lower()}@{ORG_SLUG}.example"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"first_name": first, "last_name": last, "is_active": True},
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            if not Membership.objects.filter(organisation=org, user=user).exists():
                role = Membership.Role.OWNER if is_steward else Membership.Role.CONTRIBUTOR
                Membership.objects.create(
                    organisation=org, user=user, role=role, status=Membership.Status.ACTIVE
                )
            people.append(user)
        return people

    def _role_for(self, i: int) -> str:
        return [Participant.Role.DECISION_MAKER, Participant.Role.REVIEWER, Participant.Role.CONTRIBUTOR][i % 3]

    def _ensure_participants(self, *, decision: Decision, people: list, actor) -> None:
        for index, person in enumerate(people):
            if Participant.objects.filter(decision=decision, user=person, status=Participant.Status.ACTIVE).exists():
                continue
            add_participant(actor=actor, decision=decision, user=person, role=self._role_for(index))

    # ------------------------------------------------------------- 1. Anticipate

    def _stage_anticipate(self, org: Organisation, members: list) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Stage 1/5 - Anticipate (open signal-sharing)"))
        steward = members[0]
        session = None
        from apps.ideation.models import OpenSession

        session = OpenSession.objects.filter(organisation=org, title="Community flood-season signal watch").first()
        if session is None:
            session = create_session(
                actor=steward,
                organisation=org,
                title="Community flood-season signal watch",
                prompt="What are you seeing or hearing that suggests this flood season needs attention?",
                description="Open to anyone in the neighbourhood. No account needed - just a name and email.",
                voting_enabled=True,
            )
            open_session(actor=steward, session=session)

        if session.ideas.exists():
            self.stdout.write("  Signals already present; skipping re-seed.")
            return

        ideas = []
        for person, note in zip(members, SIGNAL_NOTES):
            participant, _ = identify_participant(session=session, name=f"{person.first_name} {person.last_name}", email=person.email)
            idea = submit_idea(session=session, participant=participant, title=note[:80], description=note)
            ideas.append((participant, idea))
        for index, (participant, _) in enumerate(ideas):
            other_idea = ideas[index - 1][1]
            cast_vote(idea=other_idea, participant=participant)
            post_comment(idea=other_idea, participant=participant, body=random.choice(DISCUSSION_NOTES))
        self.stdout.write(f"  {len(ideas)} signals shared; every member voted and commented on a peer's signal.")

    # ------------------------------------------------------- 2-5. lifecycle

    def _run_commons_decision(self, org: Organisation, members: list) -> Decision:
        existing = Decision.objects.filter(organisation=org, title=DECISION_TITLE).first()
        if existing is not None:
            self.stdout.write("  Commons decision already exists; skipping re-seed.")
            return existing

        self.stdout.write(self.style.MIGRATE_HEADING("Creating the commons decision"))
        steward = members[0]
        workspace = Workspace.objects.filter(organisation=org, is_default=True).first()
        if workspace is None:
            raise CommandError(f"Organisation '{org.slug}' has no default workspace.")

        decision = create_decision(
            actor=steward,
            workspace=workspace,
            title=DECISION_TITLE,
            decision_question="What should this commons do, together, to reduce flood-season risk to the neighbourhood?",
            purpose="Reduce preventable flood damage and confusion during the next flood season, using what members are already seeing.",
            context="Several members have independently flagged rising water signals, drainage neglect, and an unreliable warning system.",
            scope="Covers the riverside blocks represented in this commons for the current flood season only.",
            contribution_guidance="Bring what you have seen or heard directly. Note if you have a personal stake in a particular response.",
            target_decision_date=(timezone.now() + timedelta(days=30)).date(),
            contribution_deadline=timezone.now() + timedelta(days=7),
            template_key="anticipatory_commons",
            owner_id=steward.id,
        )
        self._ensure_participants(decision=decision, people=members, actor=steward)
        transition_decision(actor=steward, decision=decision, expected_status=Decision.Status.DRAFT, rationale="Framing is complete: question, purpose, and scope are documented.")
        decision.refresh_from_db()
        transition_decision(actor=steward, decision=decision, expected_status=Decision.Status.FRAMING, rationale="All members are onboarded; opening for contribution.")
        decision.refresh_from_db()

        self.stdout.write(self.style.MIGRATE_HEADING("Stage 2/5 - Deliberate"))
        for person in members:
            create_discussion_entry(actor=person, decision=decision, kind=random.choice(list(DiscussionEntry.Kind.values)), body=random.choice(DISCUSSION_NOTES))
        option_titles = [
            ("Clear the drainage ditch and repair the warning siren before the season starts", "Directly addresses the two concrete infrastructure gaps members flagged."),
            ("Coordinate a household-level flood-readiness check for the most exposed streets", "Puts effort where the signals show the most immediate personal risk."),
            ("Do nothing beyond monitoring this season and revisit before next year", "The status-quo option, kept active so it is honestly compared, not assumed away."),
        ]
        for person, (title, benefit) in zip(members[0:3], option_titles):
            create_option(actor=person, decision=decision, title=title, description=f"Proposed by {person.first_name} during open contribution.", expected_benefits=benefit, tradeoffs="Requires real follow-through from someone named, not just agreement in the room.")
        for person in members[3:5]:
            create_risk(
                actor=person, decision=decision,
                title=f"Risk flagged by {person.first_name}: response starts too late",
                description="If this decision takes too long, any chosen response may not be ready before the season's usual onset.",
                likelihood=random.randint(2, 4), impact=random.randint(3, 5),
                response_strategy="mitigate", mitigation_plan="Set a firm decision date and a named owner for whatever is chosen.",
            )
        self.stdout.write(f"  {len(members)} discussion entries; {len(option_titles)} options; 2 risks.")
        transition_decision(actor=steward, decision=decision, expected_status=Decision.Status.OPEN_FOR_CONTRIBUTION, rationale="Ordinary contribution window is closed; moving into structured review.")
        decision.refresh_from_db()

        self.stdout.write(self.style.MIGRATE_HEADING("Stage 3/5 - Decide"))
        active_options = list(decision.options.filter(status=DecisionOption.Status.ACTIVE).order_by("created_at", "id"))
        for person in members:
            recommendation = random.choice(["support", "support_with_conditions", "support_with_conditions", "abstain"])
            submit_position(
                actor=person, decision=decision,
                preferred_option_id=None if recommendation == "abstain" else random.choice(active_options).id,
                recommendation=recommendation, rationale=random.choice(POSITION_BODIES),
                confidence=random.choice(["low", "medium", "medium", "high"]),
                conditions="Contingent on a named person actually owning the follow-through." if recommendation == "support_with_conditions" else "",
            )
        create_evidence(
            actor=steward, decision=decision, title="Old mill gauge readings, this season",
            summary="Water level readings at the old mill gauge, compared against the same period in prior years.",
            source_type="internal_data", source_reference="Community-maintained gauge log, shared by members.",
            stance="supports", strength="high",
        )
        create_assumption(
            actor=members[1], decision=decision,
            statement="The borough will still clear the drainage ditch on request within the contribution window.",
            impact_if_false="The infrastructure-focused response would need a different, slower path.",
            confidence="medium",
        )
        self.stdout.write(f"  {len(members)} positions submitted; evidence and assumption recorded.")
        transition_decision(actor=steward, decision=decision, expected_status=Decision.Status.UNDER_REVIEW, rationale="Structured review is complete: positions, evidence, and assumptions are recorded.")
        decision.refresh_from_db()

        selected_option = active_options[0]
        finalise_decision(
            actor=steward, decision=decision, expected_status=Decision.Status.READY_FOR_DECISION,
            selected_option_id=selected_option.id,
            rationale=f"Selecting '{selected_option.title}' as the response the commons can realistically follow through on this season.",
            conditions="Revisit before next season regardless of outcome.",
            dissent_summary="Some members preferred the household-check response or abstained; positions are preserved in the record.",
            positions_reviewed=True,
        )
        decision.refresh_from_db()
        self.stdout.write(f"  Decision finalised: selected response '{selected_option.title}'.")

        record_commitment(
            actor=steward, decision=decision, expected_status=Decision.Status.DECISION_FINALISED,
            implementation_owner_id=members[1].id,
            commitment_statement="The commons commits to clearing the drainage ditch and repairing the warning siren before the season starts.",
            success_measures="Ditch cleared and siren tested before the season's usual onset, confirmed by a named member.",
            review_due_date=timezone.localdate() + timedelta(days=90),
            rationale="Commitment recorded immediately following finalisation.",
        )
        decision.refresh_from_db()
        start_implementation(
            actor=steward, decision=decision, expected_status=Decision.Status.COMMITMENT,
            implementation_plan="Contact the borough for ditch clearing, source the siren part, and check in weekly on progress.",
            rationale="Commitment is recorded; implementation begins.",
        )
        decision.refresh_from_db()

        self.stdout.write(self.style.MIGRATE_HEADING("Stage 4/5 - Act"))
        for person in members:
            create_discussion_entry(actor=person, decision=decision, kind=DiscussionEntry.Kind.UPDATE, body=random.choice(IMPLEMENTATION_UPDATES))
        self.stdout.write(f"  {len(members)} implementation-update discussion entries posted.")
        open_outcome_review(
            actor=steward, decision=decision, expected_status=Decision.Status.IMPLEMENTATION,
            implementation_summary="The ditch was cleared and the siren repaired ahead of the season's usual onset.",
            rationale="Implementation work is complete; opening evidence-based outcome review.",
        )
        decision.refresh_from_db()

        self.stdout.write(self.style.MIGRATE_HEADING("Stage 5/5 - Learn"))
        complete_outcome_review(
            actor=steward, decision=decision, expected_status=Decision.Status.OUTCOME_REVIEW,
            outcome_summary="No basement flooding was reported on the previously affected streets this season.",
            outcome_assessment="met",
            review_evidence="Follow-up check-ins with the previously affected households, cross-checked against the gauge log.",
            unintended_consequences="",
            rationale="Outcome review is complete based on the season's actual conditions.",
        )
        decision.refresh_from_db()
        for person in members:
            create_discussion_entry(actor=person, decision=decision, kind=DiscussionEntry.Kind.NOTE, body=random.choice(LESSON_NOTES))
        create_lesson(
            actor=steward, decision=decision, title="Lesson: name the owner before the season, not after",
            insight=random.choice(LESSON_NOTES), category="process",
            applicability="Applies to any future anticipatory-commons decision this group runs.",
            recommended_change="Bring this into the framing stage of the next comparable decision.",
        )
        self.stdout.write(f"  {len(members)} retrospective notes posted; 1 formal lesson captured.")
        return decision

    # -------------------------------------------------------------- verify

    def _verify(self, org: Organisation, decision: Decision, members: list) -> None:
        from apps.ideation.models import Idea, OpenSession

        session = OpenSession.objects.get(organisation=org, title="Community flood-season signal watch")
        gaps = []
        for person in members:
            if not Idea.objects.filter(session=session, submitted_by_participant__email=person.email).exists():
                gaps.append((person.email, "anticipate"))
            if not DiscussionEntry.objects.filter(decision=decision, author=person).exists():
                gaps.append((person.email, "deliberate/act/learn"))
        if gaps:
            raise CommandError(f"Coverage gaps found (person, stage): {gaps}")
        self.stdout.write(self.style.SUCCESS(
            f"Verified: '{decision.title}' reached {decision.status} with all {len(members)} members represented."
        ))
