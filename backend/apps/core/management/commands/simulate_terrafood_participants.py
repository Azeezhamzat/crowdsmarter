"""Simulate 20 distinct TerraFood Futures Institute members participating at
every stage of the decision lifecycle, through the real service layer.

Unlike ``seed_simulated_clients``, this command creates records via the
actual ``apps.*.services`` functions (not raw ORM ``.objects.create``), so it
exercises genuine permission gates, audit logging, and notification
side-effects - the same code path the product itself uses.

Stages covered (product terminology -> underlying Decision.Status):
  1. Anticipate  - ideation (Open Session idea/vote/comment on the
                   pre-existing draft decision's session)
  2. Deliberate  - open_for_contribution (discussion, options, criteria,
                   risks, a conflict of interest, a contribution request)
  3. Decide      - under_review (positions, a ranked-choice evaluation round,
                   plus evidence/assumptions so review can complete)
  4. Act         - implementation (discussion updates)
  5. Learn       - lessons_learned (discussion notes + formal lessons)

Stages 2-5 all happen on ONE freshly created decision, driven end-to-end
through its real lifecycle transitions (draft -> framing ->
open_for_contribution -> under_review -> ready_for_decision ->
decision_finalised -> commitment -> implementation -> outcome_review ->
lessons_learned). All 20 participants are added while the decision is still
in draft, which is the only window ``add_participant`` allows - once a
decision passes open_for_contribution, no one (including admins) can add a
new participant. Reusing several already-in-progress decisions for stages
2-5 was tried first and hits exactly this wall, so a single decision is
walked through every real transition instead, with each stage's participant
interaction happening the moment the decision legitimately reaches that
status.

Every one of the 20 people leaves at least one attributable record at every
stage. Run with --dry-run first to preview without committing.
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.assumptions.services import create_assumption
from apps.collaboration.models import DiscussionEntry
from apps.collaboration.services import create_discussion_entry
from apps.contributions.services import create_request, review_submission, submit_request
from apps.criteria.services import create_criterion
from apps.decision_options.models import DecisionOption
from apps.decision_options.services import create_option
from apps.decisions.finalisation import finalise_decision
from apps.decisions.models import Decision
from apps.decisions.services import create_decision, transition_decision
from apps.evaluations.models import EvaluationExercise, EvaluationRound
from apps.evaluations.services import (
    create_exercise,
    create_round,
    save_submission,
    transition_round,
)
from apps.evidence.services import create_evidence
from apps.ideation.models import Idea, OpenSession
from apps.ideation.services import cast_vote, post_comment, submit_idea
from apps.lessons.services import create_lesson
from apps.organisations.models import Membership, Organisation
from apps.participants.models import Participant
from apps.participants.services import add_participant, declare_conflict, withdraw_conflict
from apps.positions.models import Position
from apps.positions.services import submit_position
from apps.reviews.services import (
    complete_outcome_review,
    open_outcome_review,
    record_commitment,
    start_implementation,
)
from apps.risks.services import create_risk
from apps.workspaces.models import Workspace

ORG_SLUG = "terrafood-futures-institute-sim"
LIFECYCLE_DECISION_TITLE = "Consolidate the 2027 regional partner network"

# (first, last) - deliberately distinct from the existing fictional members
# and from the ideation-only @example.com pool, so these are genuinely new,
# identifiable people with real organisation membership.
PEOPLE = [
    ("Achieng", "Otieno"),
    ("Fatoumata", "Keita"),
    ("Rajiv", "Nair"),
    ("Chidinma", "Eze"),
    ("Solomon", "Haile"),
    ("Priya", "Balasubramaniam"),
    ("Tendai", "Moyo"),
    ("Amara", "Konate"),
    ("Yusuf", "Abdullahi"),
    ("Grace", "Wanjiru"),
    ("Kwesi", "Boateng"),
    ("Nomvula", "Dlamini"),
    ("Hassan", "Farah"),
    ("Ifeoma", "Nwosu"),
    ("Samuel", "Kiptoo"),
    ("Zanele", "Mokoena"),
    ("Ousmane", "Diallo"),
    ("Aster", "Tesfaye"),
    ("Beatrice", "Achola"),
    ("Emeka", "Okafor"),
]
assert len(PEOPLE) == 20

ADMIN_COUNT = 2  # first N people become org managers; the rest are contributors

DISCUSSION_NOTES = [
    "Flagging that the community consultation notes from last month should inform this.",
    "The regional partners we spoke to raised a similar point last quarter.",
    "Worth checking this against the field-station capacity numbers before we lock anything in.",
    "I'd like to see the smallholder feedback threaded into this before we move further.",
    "This lines up with what we heard during the last extension-officer briefing.",
    "Can we get a cost comparison against the status quo before the next round?",
    "The seasonal timing here matters more than the document currently reflects.",
    "Good to see the evidence base widening - this was a gap in the last cycle.",
    "We should loop in the water-use working group before this goes further.",
    "This matches the pattern we're seeing in the pilot sites.",
]

RANK_RATIONALES = [
    "Ranked on cost-effectiveness and delivery risk, in that order.",
    "Prioritised the option with the strongest evidence from the pilot phase.",
    "Weighed community preference above administrative simplicity.",
    "Ranked by expected time-to-impact for smallholder households.",
    "Preferred the option with the clearest accountability structure.",
]

POSITION_BODIES = [
    "Supportable given the evidence gathered so far, with monitoring built in.",
    "The tradeoffs are real but manageable if we phase the rollout.",
    "I'd want the mitigation plan tightened before this proceeds further.",
    "The community input on this has been consistent and should carry weight.",
    "Reasonable path forward; flagging capacity constraints as the main risk.",
]

IMPLEMENTATION_UPDATES = [
    "Field team confirms the first milestone is on track for this cycle.",
    "Local partners have signed off on the delivery schedule.",
    "We hit a short delay on procurement; revised timeline shared with the team.",
    "Early indicators from the rollout sites look consistent with the plan.",
    "Training sessions for the extension officers are now complete.",
]

LESSON_NOTES = [
    "In hindsight, the evidence review should have started a full cycle earlier.",
    "The stakeholder mapping we did here should become standard practice.",
    "We underestimated how long field verification would take - worth budgeting for next time.",
    "The criteria weighting held up well against the eventual outcome.",
    "Community feedback loops worked better once they were scheduled, not ad hoc.",
]


class Command(BaseCommand):
    help = "Simulate 20 TerraFood Futures Institute members participating at every decision-lifecycle stage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Roll back all changes at the end."
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        random.seed(20260822)  # deterministic, reproducible run

        with transaction.atomic():
            org = self._get_org()
            people = self._create_people(org)
            self.stdout.write(self.style.SUCCESS(f"{len(people)} people active in {org.name}."))

            touched: dict[str, set] = {"deliberate": set(), "act": set(), "learn": set()}

            self._stage_anticipate(org, people)
            decision = self._create_lifecycle_decision(org, people)
            self._stage_deliberate(decision, people, touched)
            self._stage_decide(decision, people)
            self._stage_act(decision, people, touched)
            self._stage_learn(decision, people, touched)

            self._verify_everyone_touched_every_stage(org, decision, people, touched)

            if dry_run:
                self.stdout.write(self.style.WARNING("--dry-run: rolling back."))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS("Committed."))

    # ------------------------------------------------------------------ setup

    def _get_org(self) -> Organisation:
        try:
            return Organisation.objects.get(slug=ORG_SLUG)
        except Organisation.DoesNotExist as exc:
            raise CommandError(
                f"Organisation '{ORG_SLUG}' does not exist - run seed_simulated_clients first."
            ) from exc

    def _create_people(self, org: Organisation) -> list[User]:
        people = []
        for index, (first, last) in enumerate(PEOPLE):
            email = f"{first.lower()}.{last.lower()}@terrafood.example"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"first_name": first, "last_name": last, "is_active": True},
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            role = Membership.Role.ADMIN if index < ADMIN_COUNT else Membership.Role.CONTRIBUTOR
            Membership.objects.get_or_create(
                organisation=org,
                user=user,
                defaults={"role": role, "status": Membership.Status.ACTIVE},
            )
            people.append(user)
        return people

    def _admins(self, people: list[User]) -> list[User]:
        return people[:ADMIN_COUNT]

    def _role_for(self, i: int) -> str:
        return [
            Participant.Role.DECISION_MAKER,
            Participant.Role.REVIEWER,
            Participant.Role.CONTRIBUTOR,
        ][i % 3]

    def _ensure_participants(
        self, *, decision: Decision, people: list[User], actor: User, role_for
    ) -> dict:
        """Add every person as an active participant with a role decided by role_for(index)."""
        participants = {}
        for index, person in enumerate(people):
            existing = Participant.objects.filter(
                decision=decision, user=person, status=Participant.Status.ACTIVE
            ).first()
            if existing:
                participants[person.id] = existing
                continue
            participants[person.id] = add_participant(
                actor=actor, decision=decision, user=person, role=role_for(index)
            )
        return participants

    # ------------------------------------------------------------- 1. Anticipate

    def _stage_anticipate(self, org: Organisation, people: list[User]) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Stage 1/5 - Anticipate (ideation)"))
        session = OpenSession.objects.get(
            organisation=org,
            status=OpenSession.Status.OPEN,
            decision__isnull=False,
            title__icontains="2026 Community Impact Grant Round",
        )
        ideas: list[Idea] = []
        for person in people:
            idea = submit_idea(
                session=session,
                user=person,
                title=f"{person.first_name}'s proposal: community-led monitoring for {random.choice(['seed banks', 'irrigation plots', 'field trials', 'advisory clinics'])}",
                description=(
                    f"Submitted by {person.first_name} {person.last_name} on behalf of the regional "
                    "working group, drawing on this season's field observations."
                ),
                category=random.choice(["community", "research", "infrastructure", "advisory"]),
                requested_amount=random.choice([2500, 4000, 6000, 8500, 12000]),
            )
            ideas.append(idea)
        # Ring voting + commenting: everyone interacts with someone else's idea.
        for index, person in enumerate(people):
            other_idea = ideas[index - 1]
            cast_vote(idea=other_idea, user=person)
            post_comment(idea=other_idea, user=person, body=random.choice(DISCUSSION_NOTES))
        self.stdout.write(
            f"  {len(ideas)} ideas submitted; every person voted and commented on a peer's idea."
        )

    # ------------------------------------------------------ decision creation

    def _create_lifecycle_decision(self, org: Organisation, people: list[User]) -> Decision:
        self.stdout.write(self.style.MIGRATE_HEADING("Creating the shared decision for stages 2-5"))
        admin0 = self._admins(people)[0]
        workspace = Workspace.objects.filter(organisation=org, is_default=True).first()
        if workspace is None:
            workspace = Workspace.objects.filter(organisation=org).order_by("created_at").first()
        if workspace is None:
            raise CommandError(
                f"Organisation '{org.slug}' has no workspace to create a decision in."
            )

        decision = create_decision(
            actor=admin0,
            workspace=workspace,
            title=LIFECYCLE_DECISION_TITLE,
            decision_question="Which regional partner-network consolidation option should the institute commit to for 2027?",
            purpose="Reduce duplicated administrative overhead across regional partners while preserving delivery reach.",
            context="Regional partnerships have grown organically since 2023; reporting overhead and inconsistent terms are increasing faster than delivery capacity.",
            scope="Applies to all active regional partnership agreements coming up for renewal in 2027.",
            contribution_guidance="Focus on delivery reach, administrative cost, and community trust. Do not re-litigate funding levels already agreed for the current cycle.",
            target_decision_date=(timezone.now() + timedelta(days=45)).date(),
            contribution_deadline=timezone.now() + timedelta(days=10),
            template_key="blank",
            owner_id=admin0.id,
        )

        # All 20 must be added while the decision is still draft - this is the
        # only window the real participant-management policy allows.
        self._ensure_participants(
            decision=decision, people=people, actor=admin0, role_for=self._role_for
        )

        transition_decision(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.DRAFT,
            rationale="Framing is complete: question, purpose, and scope are documented.",
        )
        decision.refresh_from_db()
        transition_decision(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.FRAMING,
            rationale="All 20 stakeholders are onboarded; opening for ordinary contribution.",
        )
        decision.refresh_from_db()
        self.stdout.write(
            f"  Decision '{decision.title}' created with all {len(people)} participants, now open for contribution."
        )
        return decision

    # ------------------------------------------------------------- 2. Deliberate

    def _stage_deliberate(self, decision: Decision, people: list[User], touched: dict) -> None:
        self.stdout.write(
            self.style.MIGRATE_HEADING("Stage 2/5 - Deliberate (open for contribution)")
        )
        admin0, admin1 = self._admins(people)

        for person in people:
            create_discussion_entry(
                actor=person,
                decision=decision,
                kind=random.choice(list(DiscussionEntry.Kind.values)),
                body=random.choice(DISCUSSION_NOTES),
            )
            touched["deliberate"].add(person.id)

        # Rotating breadth: options, criteria, risks, conflicts, contribution requests.
        option_authors, criterion_authors, risk_authors = people[0:4], people[4:8], people[8:12]
        for person in option_authors:
            create_option(
                actor=person,
                decision=decision,
                title=f"{person.first_name}'s proposed partnership variant",
                description="A variant surfaced during deliberation, with a distinct cost/benefit profile.",
                expected_benefits="Broadens the evidence base for the final recommendation.",
                tradeoffs="Requires additional review time before it can be scored.",
            )
        for person in criterion_authors:
            create_criterion(
                actor=person,
                decision=decision,
                title=f"{person.first_name}'s proposed measure: community reach",
                description="How directly the terms reach smallholder households, not just partner institutions.",
                direction="maximize",
                weight=random.randint(10, 40),
            )
        for person in risk_authors:
            create_risk(
                actor=person,
                decision=decision,
                title=f"Risk flagged by {person.first_name}: partner capacity",
                description="The regional partner may not have staffing to meet the proposed terms on schedule.",
                likelihood=random.randint(1, 5),
                impact=random.randint(1, 5),
                response_strategy=random.choice(["mitigate", "monitor", "accept"]),
                mitigation_plan="Confirm staffing commitments with the partner before the terms are finalised.",
            )
        # A conflict declared, then withdrawn once clarified.
        conflict_person = people[12]
        conflict_participant = Participant.objects.get(
            decision=decision, user=conflict_person, status=Participant.Status.ACTIVE
        )
        conflict = declare_conflict(
            actor=conflict_person,
            participant=conflict_participant,
            scope="decision",
            reason="Immediate family member works for one of the candidate partner organisations.",
        )
        withdraw_conflict(actor=admin1, conflict=conflict)

        # Contribution-request mini-cycle. Reviewer must hold a reviewer/decision_maker
        # participant role (role_for cycles [DECISION_MAKER, REVIEWER, CONTRIBUTOR]).
        assignee, reviewer = people[13], people[6]
        request = create_request(
            actor=admin0,
            decision=decision,
            assignee_id=assignee.id,
            reviewer_id=reviewer.id,
            kind="stakeholder",
            title="Summarise community consultation feedback",
            instructions="Pull together the last round of community consultation notes into a short brief.",
        )
        submit_request(
            actor=assignee,
            request=request,
            body="Consultation notes summarised: strong support for transparent terms, concern about timelines.",
        )
        review_submission(
            actor=reviewer, request=request, outcome="accepted", note="Clear and useful, thank you."
        )

        self.stdout.write(
            f"  {len(people)} discussion entries; "
            f"{len(option_authors)} options, {len(criterion_authors)} criteria, {len(risk_authors)} risks; "
            "1 conflict declared+withdrawn; 1 contribution request completed."
        )

        transition_decision(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.OPEN_FOR_CONTRIBUTION,
            rationale="Ordinary contribution window is closed; moving into structured review.",
        )
        decision.refresh_from_db()

    # ------------------------------------------------------------- 3. Decide

    def _stage_decide(self, decision: Decision, people: list[User]) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Stage 3/5 - Decide (under review)"))
        admin0, admin1 = self._admins(people)

        active_options = list(
            decision.options.filter(status=DecisionOption.Status.ACTIVE).order_by(
                "created_at", "id"
            )
        )
        if not active_options:
            raise CommandError(f"Decision '{decision.title}' has no active options to decide over.")

        for person in people:
            recommendation = random.choice(
                ["support", "support_with_conditions", "support_with_conditions", "abstain"]
            )
            submit_position(
                actor=person,
                decision=decision,
                preferred_option_id=None
                if recommendation == "abstain"
                else random.choice(active_options).id,
                recommendation=recommendation,
                rationale=random.choice(POSITION_BODIES),
                confidence=random.choice(["low", "medium", "medium", "high"]),
                conditions=(
                    "Contingent on confirmed staffing commitments from the partner before rollout."
                    if recommendation == "support_with_conditions"
                    else ""
                ),
            )

        # A ranked-choice evaluation round - the one method not yet exercised elsewhere in this data.
        exercise = create_exercise(
            actor=admin0,
            decision=decision,
            owner_id=admin0.id,
            title="Partner-network consolidation - community ranked-choice ballot",
            method=EvaluationExercise.Method.RANKED_CHOICE,
            purpose="A single-transferable-vote read on the consolidation options, alongside stakeholder positions.",
        )
        round_ = create_round(actor=admin0, exercise=exercise)
        transition_round(actor=admin0, round=round_, status=EvaluationRound.Status.OPEN)
        for person in people:
            ranks = list(range(1, len(active_options) + 1))
            random.shuffle(ranks)
            responses = [
                {"option_id": option.id, "rank": rank, "rationale": random.choice(RANK_RATIONALES)}
                for option, rank in zip(active_options, ranks, strict=False)
            ]
            save_submission(
                actor=person,
                round=round_,
                confidence=3,
                overall_rationale=random.choice(RANK_RATIONALES),
                responses=responses,
                submit=True,
            )
        transition_round(
            actor=admin0,
            round=round_,
            status=EvaluationRound.Status.CLOSED,
            feedback_summary="All 20 stakeholders returned a complete ballot.",
        )

        # Evidence + a non-invalidated assumption, required before review can complete.
        create_evidence(
            actor=admin0,
            decision=decision,
            title="Regional partner capacity survey, 2026",
            summary="A survey of the six candidate regional partners' current administrative and field staffing levels.",
            source_type="internal_data",
            source_reference="TerraFood Futures Institute internal partner capacity survey, Q4 2026.",
            stance="context",
            strength="high",
        )
        create_assumption(
            actor=admin1,
            decision=decision,
            statement="Candidate partners will maintain current staffing levels through the 2027 transition window.",
            impact_if_false="A consolidated partner could be under-resourced at handover, delaying delivery.",
            confidence="medium",
        )

        self.stdout.write(
            f"  {len(people)} positions submitted; {len(people)} ranked-choice ballots cast and round closed; "
            "evidence + assumption recorded."
        )

        transition_decision(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.UNDER_REVIEW,
            rationale="Structured review is complete: positions, ranked-choice results, evidence, and assumptions are recorded.",
        )
        decision.refresh_from_db()

        selected_option = active_options[0]
        finalise_decision(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.READY_FOR_DECISION,
            selected_option_id=selected_option.id,
            rationale=f"Selecting “{selected_option.title}” based on the ranked-choice result and stakeholder positions.",
            conditions="Implementation must confirm partner staffing commitments before rollout begins.",
            dissent_summary="Some stakeholders preferred a different option or recorded conditional support; positions are preserved in the record.",
            positions_reviewed=True,
        )
        decision.refresh_from_db()
        self.stdout.write(f"  Decision finalised: selected option '{selected_option.title}'.")

        record_commitment(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.DECISION_FINALISED,
            implementation_owner_id=admin1.id,
            commitment_statement="The institute commits to the selected partner-network consolidation for the 2027 renewal cycle.",
            success_measures="Reduced per-partner administrative overhead and no loss of active delivery sites within 12 months.",
            review_due_date=timezone.localdate() + timedelta(days=180),
            rationale="Commitment recorded immediately following finalisation.",
        )
        decision.refresh_from_db()
        start_implementation(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.COMMITMENT,
            implementation_plan="Notify all regional partners, migrate reporting templates, and confirm staffing commitments over the next quarter.",
            rationale="Commitment is recorded; implementation begins.",
        )
        decision.refresh_from_db()
        self.stdout.write("  Commitment recorded and implementation started.")

    # ------------------------------------------------------------- 4. Act

    def _stage_act(self, decision: Decision, people: list[User], touched: dict) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Stage 4/5 - Act (implementation)"))
        for person in people:
            create_discussion_entry(
                actor=person,
                decision=decision,
                kind=DiscussionEntry.Kind.UPDATE,
                body=random.choice(IMPLEMENTATION_UPDATES),
            )
            touched["act"].add(person.id)
        self.stdout.write(f"  {len(people)} implementation-update discussion entries posted.")

        admin0 = self._admins(people)[0]
        open_outcome_review(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.IMPLEMENTATION,
            implementation_summary="Regional partners transitioned to the consolidated terms on schedule, with staffing commitments confirmed.",
            rationale="Implementation work is complete; opening evidence-based outcome review.",
        )
        decision.refresh_from_db()

    # ------------------------------------------------------------- 5. Learn

    def _stage_learn(self, decision: Decision, people: list[User], touched: dict) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Stage 5/5 - Learn (lessons learned)"))
        admin0, admin1 = self._admins(people)

        complete_outcome_review(
            actor=admin0,
            decision=decision,
            expected_status=Decision.Status.OUTCOME_REVIEW,
            outcome_summary="The consolidated partner network is operating with lower overhead and no loss of delivery reach.",
            outcome_assessment="met",
            review_evidence="Quarterly reporting from all consolidated regional partners, cross-checked against the original success measures.",
            unintended_consequences="One smaller partner needed a short bridging arrangement during transition.",
            rationale="Outcome review is complete based on the first two quarters of reporting.",
        )
        decision.refresh_from_db()

        for person in people:
            create_discussion_entry(
                actor=person,
                decision=decision,
                kind=DiscussionEntry.Kind.NOTE,
                body=random.choice(LESSON_NOTES),
            )
            touched["learn"].add(person.id)
        for admin_person, category in zip(
            self._admins(people), ["process", "stakeholder"], strict=False
        ):
            create_lesson(
                actor=admin_person,
                decision=decision,
                title=f"Lesson captured by {admin_person.first_name}",
                insight=random.choice(LESSON_NOTES),
                category=category,
                applicability="Applies to future partner-network consolidation decisions across the organisation.",
                recommended_change="Bring this into the framing stage of the next comparable round.",
            )
        self.stdout.write(f"  {len(people)} retrospective notes posted; 2 formal lessons captured.")

    # -------------------------------------------------------------- verify

    def _verify_everyone_touched_every_stage(
        self, org: Organisation, decision: Decision, people: list[User], touched: dict
    ) -> None:
        anticipate = Decision.objects.get(
            organisation=org,
            status=Decision.Status.DRAFT,
            title__icontains="2026 Community Impact Grant Round",
        )

        gaps = []
        for person in people:
            if not Idea.objects.filter(
                session__decision=anticipate, submitted_by_user=person
            ).exists():
                gaps.append((person.email, "anticipate"))
            if person.id not in touched["deliberate"]:
                gaps.append((person.email, "deliberate"))
            if not Position.objects.filter(decision=decision, submitted_by=person).exists():
                gaps.append((person.email, "decide"))
            if person.id not in touched["act"]:
                gaps.append((person.email, "act"))
            if person.id not in touched["learn"]:
                gaps.append((person.email, "learn"))
        if gaps:
            raise CommandError(f"Coverage gaps found (person, stage): {gaps}")
        self.stdout.write(
            self.style.SUCCESS(
                "Verified: all 20 people have a real interaction at every one of the 5 stages."
            )
        )
