"""Versioned built-in decision templates for guided creation.

Templates provide prompts and framing guidance only. They never create evidence,
select options, or make a decision on behalf of a user.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class DecisionTemplate:
    """A stable, provider-neutral prompt set for one decision pattern."""

    key: str
    name: str
    summary: str
    best_for: str
    question_prompt: str
    purpose_prompt: str
    context_prompt: str
    scope_prompt: str
    contribution_prompt: str
    suggested_urgency: str = "normal"
    checklist: tuple[str, ...] = ()
    version: int = 1

    def as_dict(self) -> dict:
        data = asdict(self)
        data["checklist"] = list(self.checklist)
        return data


TEMPLATES: tuple[DecisionTemplate, ...] = (
    DecisionTemplate(
        key="blank",
        name="Blank decision",
        summary="Start with a clean frame and write every field yourself.",
        best_for=(
            "Decisions that do not fit a standard organisational pattern."
        ),
        question_prompt=(
            "State one choice that a named human authority can answer."
        ),
        purpose_prompt=(
            "Explain what better outcome this decision should enable."
        ),
        context_prompt=(
            "Describe what changed, what is known, and why a decision is needed now."
        ),
        scope_prompt=(
            "Define what this decision includes and explicitly excludes."
        ),
        contribution_prompt=(
            "Tell contributors which evidence, expertise, and boundaries matter."
        ),
        checklist=(
            "Named decision authority",
            "Explicit alternatives",
            "Decision deadline",
        ),
    ),
    DecisionTemplate(
        key="technology_adoption",
        name="Technology adoption",
        summary=(
            "Evaluate whether to adopt, pilot, replace, or reject a technology."
        ),
        best_for=(
            "Software, AI systems, platforms, infrastructure, and technical tools."
        ),
        question_prompt=(
            "Should we adopt, pilot, replace, or reject the proposed technology "
            "for a defined use case?"
        ),
        purpose_prompt=(
            "Describe the customer or operational problem the technology must solve."
        ),
        context_prompt=(
            "Record the current process, pain points, existing systems, constraints, "
            "and trigger for change."
        ),
        scope_prompt=(
            "Define users, use cases, integrations, data, locations, budget, and "
            "what is out of scope."
        ),
        contribution_prompt=(
            "Request security, privacy, usability, cost, integration, lock-in, and "
            "operational evidence."
        ),
        suggested_urgency="high",
        checklist=(
            "Status quo option",
            "Exit and export requirements",
            "Security and privacy review",
        ),
    ),
    DecisionTemplate(
        key="pilot_experiment",
        name="Pilot or experiment",
        summary="Decide whether and how to run a bounded learning exercise.",
        best_for=(
            "Product pilots, field trials, experiments, and proof-before-scale decisions."
        ),
        question_prompt=(
            "Should we run the proposed pilot, and under what limits and success "
            "thresholds?"
        ),
        purpose_prompt=(
            "State the uncertainty the pilot must reduce before a larger commitment."
        ),
        context_prompt=(
            "Explain the current evidence gap, proposed intervention, and why "
            "observation is needed."
        ),
        scope_prompt=(
            "Define population, duration, locations, budget, controls, stop rules, "
            "and exclusions."
        ),
        contribution_prompt=(
            "Request measurable outcomes, safety constraints, implementation "
            "feasibility, and learning value."
        ),
        checklist=(
            "Success and failure thresholds",
            "Stop-or-modify rule",
            "Comparison baseline",
        ),
    ),
    DecisionTemplate(
        key="strategic_investment",
        name="Strategic investment",
        summary=(
            "Compare a material allocation of money, people, or organisational attention."
        ),
        best_for=(
            "New markets, major programmes, capital allocation, and strategic bets."
        ),
        question_prompt=(
            "Which investment option best advances the strategy within the "
            "organisation's constraints?"
        ),
        purpose_prompt=(
            "Connect the decision to a measurable strategic objective and customer value."
        ),
        context_prompt=(
            "Describe the opportunity, timing, alternatives, prior commitments, "
            "and uncertainty."
        ),
        scope_prompt=(
            "Define investment horizon, budget, resources, dependencies, and "
            "excluded commitments."
        ),
        contribution_prompt=(
            "Request financial, operational, market, capability, downside, and "
            "opportunity-cost evidence."
        ),
        suggested_urgency="high",
        checklist=(
            "Do-nothing option",
            "Opportunity cost",
            "Reversal or exit path",
        ),
    ),
    DecisionTemplate(
        key="vendor_selection",
        name="Vendor selection",
        summary=(
            "Select a supplier through explicit requirements and comparable evidence."
        ),
        best_for=(
            "Software, professional services, equipment, and outsourced capabilities."
        ),
        question_prompt=(
            "Which supplier, including an internal or no-purchase option, best meets "
            "the agreed requirements?"
        ),
        purpose_prompt=(
            "Define the business outcome the supplier must enable, not merely the "
            "product to buy."
        ),
        context_prompt=(
            "Describe the current arrangement, procurement trigger, market scan, and "
            "known constraints."
        ),
        scope_prompt=(
            "Define contract term, users, data, service levels, integrations, budget, "
            "and exclusions."
        ),
        contribution_prompt=(
            "Request comparable cost, capability, security, support, lock-in, and "
            "reference evidence."
        ),
        checklist=(
            "Comparable evaluation criteria",
            "Contract exit terms",
            "Internal or no-purchase option",
        ),
    ),
    DecisionTemplate(
        key="research_project",
        name="Research project approval",
        summary=(
            "Assess whether a proposed study is valuable, feasible, ethical, and "
            "decision-relevant."
        ),
        best_for=(
            "Field studies, organisational research, evaluations, and data-collection "
            "programmes."
        ),
        question_prompt=(
            "Should the organisation approve, revise, postpone, or reject the "
            "proposed research project?"
        ),
        purpose_prompt=(
            "State the decision or knowledge gap the research must address."
        ),
        context_prompt=(
            "Summarise prior evidence, proposed methods, affected groups, and why the "
            "study matters now."
        ),
        scope_prompt=(
            "Define research questions, population, methods, duration, resources, "
            "ethics, and exclusions."
        ),
        contribution_prompt=(
            "Request methodological, ethical, feasibility, data-quality, cost, and "
            "use-of-results input."
        ),
        checklist=(
            "Decision-relevant research question",
            "Ethics and consent",
            "Analysis and use plan",
        ),
    ),
    DecisionTemplate(
        key="policy_change",
        name="Policy or governance change",
        summary=(
            "Evaluate a rule, standard, governance, or operating-policy change."
        ),
        best_for=(
            "Internal policies, governance controls, compliance rules, and operating "
            "standards."
        ),
        question_prompt=(
            "Should the organisation introduce, amend, retain, or retire the proposed "
            "policy?"
        ),
        purpose_prompt=(
            "Describe the behaviour, risk, fairness, or accountability problem the "
            "policy should address."
        ),
        context_prompt=(
            "Record the current policy, incidents, obligations, stakeholder effects, "
            "and trigger for review."
        ),
        scope_prompt=(
            "Define affected people, processes, jurisdictions, exceptions, enforcement, "
            "and exclusions."
        ),
        contribution_prompt=(
            "Request legal, operational, fairness, accessibility, implementation, and "
            "unintended-effect evidence."
        ),
        checklist=(
            "Affected stakeholder voices",
            "Exceptions and appeals",
            "Implementation and review plan",
        ),
    ),
)

TEMPLATE_BY_KEY = {template.key: template for template in TEMPLATES}


def list_templates() -> list[dict]:
    """Return stable serialisable templates in curated display order."""
    return [template.as_dict() for template in TEMPLATES]


def template_for_key(key: str) -> DecisionTemplate | None:
    """Return one built-in template, or ``None`` for an unknown key."""
    return TEMPLATE_BY_KEY.get(key)
