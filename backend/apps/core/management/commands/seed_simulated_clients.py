"""Create three clearly fictional, research-grounded CrowdSmarter demo clients."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.assumptions.models import Assumption
from apps.collaboration.models import DiscussionEntry
from apps.contributions.models import (
    ContributionRequest,
    ContributionReview,
    ContributionSubmission,
    FacilitationSession,
    SessionParticipant,
)
from apps.decision_analysis.models import (
    DecisionIssue,
    DecisionQualityReview,
    ExecutiveDecisionSummary,
)
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision, DecisionFinalisation, DecisionTransition
from apps.evaluations.models import (
    EvaluationCriterion,
    EvaluationExercise,
    EvaluationResponse,
    EvaluationRound,
    EvaluationSubmission,
    MinorityReport,
)
from apps.evidence.models import Evidence
from apps.foresight.models import (
    CausalRelationship,
    Driver,
    DriverSignal,
    ForesightCanvas,
    Scenario,
    ScenarioDriverState,
    ScenarioImplicationLink,
    ScenarioReview,
    ScenarioSet,
    ScenarioSignpost,
    Signal,
    SignalDecisionLink,
    Signpost,
    SignpostObservation,
    Source,
    StrategicImplication,
    SystemStakeholder,
    Watchlist,
    WatchlistSignal,
    WindTunnelAssessment,
)
from apps.lessons.models import Lesson
from apps.organisations.models import Membership, Organisation
from apps.platform_admin.models import PlatformAdministrator
from apps.participants.models import Participant
from apps.positions.models import Position
from apps.reviews.models import DecisionReview
from apps.risks.models import Risk
from apps.workspaces.models import Workspace

SIMULATION_MARKER = "[SIMULATED CLIENT - NOT A REAL ORGANISATION]"
SIMULATED_SLUGS = (
    "northstar-grid-services-sim",
    "careweave-regional-health-sim",
    "terrafood-futures-institute-sim",
)


@dataclass(frozen=True)
class PersonSpec:
    email: str
    first_name: str
    last_name: str
    role: str


@dataclass(frozen=True)
class ClientSpec:
    slug: str
    name: str
    brand_name: str
    colour: str
    description: str
    workspace_name: str
    workspace_slug: str
    workspace_description: str
    decision_title: str
    decision_question: str
    purpose: str
    context: str
    scope: str
    guidance: str
    urgency: str
    status: str
    people: tuple[PersonSpec, PersonSpec, PersonSpec]
    options: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]
    sources: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]
    signals: tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]
    drivers: tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]
    scenario_axes: tuple[str, str, str, str]
    scenarios: tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]
    assumptions: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]
    risks: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]
    selected_option_index: int | None = None


CLIENTS: tuple[ClientSpec, ...] = (
    ClientSpec(
        slug="northstar-grid-services-sim",
        name="NorthStar Grid Services",
        brand_name="NorthStar Grid",
        colour="#185c4f",
        description=(
            f"{SIMULATION_MARKER} A fictional electricity-network organisation used to demonstrate "
            "stakeholder engagement, foresight, scenario testing, collective evaluation, and a governed "
            "investment decision."
        ),
        workspace_name="Energy Transition Portfolio",
        workspace_slug="energy-transition-portfolio",
        workspace_description="Strategic choices for network resilience, flexibility, and customer value.",
        decision_title="Select the 2027-2029 flexibility investment portfolio",
        decision_question=(
            "Which investment portfolio should NorthStar commit to for 2027-2029 to improve network "
            "resilience and customer value while preserving regulatory and community trust?"
        ),
        purpose="Authorise a staged, evidence-based portfolio before the next regulatory submission.",
        context=(
            "Electrification is increasing local peak demand while connection queues, community acceptance, "
            "cyber resilience, and regulatory incentives remain uncertain."
        ),
        scope=(
            "Distribution-level flexibility, targeted reinforcement, digital control capabilities, customer "
            "participation, and a three-year delivery envelope. National generation policy is out of scope."
        ),
        guidance=(
            "Contributors must distinguish observed evidence from assumptions, identify distributional effects, "
            "and state conditions under which their preferred option should be reconsidered."
        ),
        urgency="high",
        status="ready_for_decision",
        people=(
            PersonSpec("aoife.byrne@northstar.example", "Aoife", "Byrne", "Programme Director"),
            PersonSpec("kwame.mensah@northstar.example", "Kwame", "Mensah", "System Planning Lead"),
            PersonSpec("niamh.oconnor@northstar.example", "Niamh", "O'Connor", "Community Engagement Lead"),
        ),
        options=(
            {
                "title": "Local flexibility market first",
                "description": "Prioritise local demand response, storage aggregation, and flexibility procurement.",
                "expected_benefits": "Faster learning, lower capital exposure, and stronger customer participation.",
                "tradeoffs": "Depends on market liquidity, digital interoperability, and sustained participation.",
                "is_status_quo": False,
            },
            {
                "title": "Targeted reinforcement first",
                "description": "Accelerate conventional reinforcement at the most constrained substations.",
                "expected_benefits": "Predictable engineering performance and clearer delivery accountability.",
                "tradeoffs": "Higher capital commitment and less flexibility if demand patterns change.",
                "is_status_quo": False,
            },
            {
                "title": "Staged hybrid portfolio",
                "description": "Combine no-regret reinforcement with time-boxed flexibility pilots and decision gates.",
                "expected_benefits": "Balances reliability, learning, customer value, and future adaptability.",
                "tradeoffs": "Requires stronger portfolio governance and explicit stop-or-scale criteria.",
                "is_status_quo": False,
            },
        ),
        sources=(
            {"title": "Regional peak-demand outlook 2026", "source_type": "dataset", "publisher": "NorthStar Analytics", "credibility": "high"},
            {"title": "Community energy participation review", "source_type": "stakeholder", "publisher": "Independent Engagement Panel", "credibility": "moderate"},
            {"title": "Flexibility market design consultation", "source_type": "government", "publisher": "Fictional Energy Regulator", "credibility": "high"},
        ),
        signals=(
            {"title": "Connection demand is concentrating faster than forecast", "summary": "Three growth zones account for most new connection requests.", "future_implication": "Portfolio value will depend on geographic targeting rather than system-wide averages.", "steep_category": "economic", "time_horizon": "near", "maturity": "established", "polarity": "both", "impact": 5, "uncertainty": 2},
            {"title": "Household flexibility participation remains uneven", "summary": "Participation is higher among digitally confident and higher-income customers.", "future_implication": "A flexibility-first strategy could create distributional and legitimacy risks.", "steep_category": "social", "time_horizon": "near", "maturity": "emerging", "polarity": "threat", "impact": 4, "uncertainty": 3},
            {"title": "Interoperable control standards are converging", "summary": "Vendors are adopting common interfaces for storage and demand-response assets.", "future_implication": "Vendor lock-in risk may decline, improving scale economics.", "steep_category": "technological", "time_horizon": "medium", "maturity": "emerging", "polarity": "opportunity", "impact": 4, "uncertainty": 3},
            {"title": "Regulatory incentives are shifting toward outcomes", "summary": "Consultation language emphasises customer value and verified system outcomes.", "future_implication": "A staged portfolio with measurable gates may be rewarded over one-off capital programmes.", "steep_category": "legal", "time_horizon": "medium", "maturity": "emerging", "polarity": "opportunity", "impact": 5, "uncertainty": 3},
        ),
        drivers=(
            {"title": "Electrification pace", "description": "Speed and concentration of transport, heat, and industrial electrification.", "driver_type": "critical_uncertainty", "steep_category": "technological", "direction": "increasing", "impact": 5, "uncertainty": 5},
            {"title": "Public and customer trust", "description": "Willingness to participate in flexibility and accept network interventions.", "driver_type": "critical_uncertainty", "steep_category": "social", "direction": "volatile", "impact": 5, "uncertainty": 4},
            {"title": "Interoperability maturity", "description": "Availability of secure, open, and scalable control interfaces.", "driver_type": "driver", "steep_category": "technological", "direction": "increasing", "impact": 4, "uncertainty": 3},
            {"title": "Outcome-based regulation", "description": "Strength of incentives tied to measurable customer and resilience outcomes.", "driver_type": "trend", "steep_category": "legal", "direction": "increasing", "impact": 4, "uncertainty": 3},
        ),
        scenario_axes=("Managed electrification", "Rapid electrification", "Low trust", "High trust"),
        scenarios=(
            {"code": "A", "title": "Trusted acceleration", "x": "high", "y": "high", "headline": "Rapid demand growth is matched by strong participation and institutional trust.", "narrative": "Flexible assets scale quickly and communities accept staged investment when benefits are transparent.", "opportunities": "Scale local markets; defer selected capital works; build new customer services.", "threats": "Operational complexity and cyber exposure rise quickly."},
            {"code": "B", "title": "Contested acceleration", "x": "high", "y": "low", "headline": "Demand rises quickly but customer participation and trust fragment.", "narrative": "The network faces urgent constraints while flexibility programmes are challenged on fairness and control.", "opportunities": "Target trusted intermediaries and protected-customer programmes.", "threats": "Connection delays, political pressure, and expensive emergency reinforcement."},
            {"code": "C", "title": "Collaborative transition", "x": "low", "y": "high", "headline": "Demand grows steadily with time to co-design new services.", "narrative": "A slower transition enables careful pilots, standards alignment, and community capacity building.", "opportunities": "Optimise learning and sequence investment with evidence.", "threats": "Complacency may delay essential capability building."},
            {"code": "D", "title": "Defensive grid", "x": "low", "y": "low", "headline": "Weak participation and uncertain demand favour conservative delivery.", "narrative": "The organisation protects reliability while preserving options for later acceleration.", "opportunities": "Focus on no-regret reinforcement and operational discipline.", "threats": "Missed innovation and higher long-run system costs."},
        ),
        evidence=(
            {"title": "Constraint concentration analysis", "summary": "Most forecast overload risk is concentrated in a small number of zones.", "source_type": "internal_data", "stance": "supports", "strength": "high", "option": 2},
            {"title": "Pilot participation findings", "summary": "Participation improves when benefits are visible and trusted intermediaries are involved.", "source_type": "stakeholder_input", "stance": "supports", "strength": "moderate", "option": 0},
            {"title": "Whole-life cost comparison", "summary": "The hybrid portfolio has a higher governance cost but lower regret across demand ranges.", "source_type": "research", "stance": "supports", "strength": "high", "option": 2},
            {"title": "Cyber assurance gap", "summary": "Current third-party control assurance is insufficient for immediate large-scale deployment.", "source_type": "expert_judgement", "stance": "challenges", "strength": "high", "option": 0},
        ),
        assumptions=(
            {"statement": "At least two credible aggregators will enter each pilot zone.", "rationale": "Market sounding indicates interest but no binding commitment.", "impact_if_false": "Flexibility prices could become uncompetitive and pilots would not provide transferable evidence.", "confidence": "medium"},
            {"statement": "Regulatory treatment will recognise verified deferral value.", "rationale": "Consultation direction is favourable but final methodology is pending.", "impact_if_false": "The hybrid option could underperform financially despite operational value.", "confidence": "medium"},
            {"statement": "Critical interoperability controls can be assured within twelve months.", "rationale": "Standards are converging and vendors have published roadmaps.", "impact_if_false": "Scale-up gates must be delayed and reinforcement brought forward.", "confidence": "low"},
        ),
        risks=(
            {"title": "Participation inequity", "description": "Benefits may accrue disproportionately to customers with capital and digital capability.", "likelihood": 4, "impact": 4, "response_strategy": "mitigate", "mitigation_plan": "Fund inclusive participation, publish distributional metrics, and use community intermediaries."},
            {"title": "Cyber compromise through distributed assets", "description": "Third-party devices expand the operational attack surface.", "likelihood": 3, "impact": 5, "response_strategy": "mitigate", "mitigation_plan": "Require assurance gates, segmentation, incident drills, and vendor exit provisions."},
            {"title": "Reinforcement lead-time shock", "description": "If demand accelerates, physical works may not be deliverable quickly enough.", "likelihood": 3, "impact": 5, "response_strategy": "monitor", "mitigation_plan": "Protect permits and designs for no-regret schemes while pilots run."},
        ),
    ),
    ClientSpec(
        slug="careweave-regional-health-sim",
        name="CareWeave Regional Health",
        brand_name="CareWeave",
        colour="#365a84",
        description=(
            f"{SIMULATION_MARKER} A fictional regional health transformation organisation used to demonstrate "
            "inclusive contribution, patient and workforce perspectives, operating-model comparison, and implementation risk."
        ),
        workspace_name="Care Model Transformation",
        workspace_slug="care-model-transformation",
        workspace_description="Cross-service decisions for accessible, safe, and sustainable care delivery.",
        decision_title="Choose the first regional virtual-care operating model",
        decision_question=(
            "Which virtual-care operating model should CareWeave launch first to improve access without worsening "
            "clinical workload, digital exclusion, or continuity of care?"
        ),
        purpose="Select a twelve-month operating model for two specialties and define evidence-based scale gates.",
        context=(
            "Waiting lists are rising, workforce capacity is constrained, and home-monitoring tools are maturing. "
            "Patients and clinical teams report uneven readiness across localities."
        ),
        scope=(
            "Two specialties, three localities, referral pathways, clinical governance, patient support, workforce design, "
            "and evaluation. Procurement of the enterprise electronic health record is out of scope."
        ),
        guidance=(
            "Contributions must identify safety implications, workload transfer, accessibility barriers, and the evidence "
            "needed before expansion. Patient experience is evidence, not an optional consultation layer."
        ),
        urgency="high",
        status="open_for_contribution",
        people=(
            PersonSpec("sofia.malik@careweave.example", "Sofia", "Malik", "Transformation Director"),
            PersonSpec("david.osei@careweave.example", "David", "Osei", "Clinical Operations Lead"),
            PersonSpec("elena.rossi@careweave.example", "Elena", "Rossi", "Patient Partnership Lead"),
        ),
        options=(
            {"title": "Central virtual-care hub", "description": "Create one regional multidisciplinary hub that owns triage and remote monitoring.", "expected_benefits": "Concentrated expertise, standard protocols, and easier performance management.", "tradeoffs": "Risk of weak local integration and perceived transfer of control from clinical teams.", "is_status_quo": False},
            {"title": "Distributed clinical network", "description": "Embed virtual-care capability within each locality using shared standards and peer support.", "expected_benefits": "Stronger continuity and local ownership.", "tradeoffs": "Variable implementation quality and duplicated coordination effort.", "is_status_quo": False},
            {"title": "Staged specialty pathway", "description": "Launch one common pathway in two specialties with a small regional enablement team.", "expected_benefits": "Focused learning, bounded risk, and a clearer route to adaptation.", "tradeoffs": "Benefits arrive more slowly and require disciplined scale criteria.", "is_status_quo": False},
        ),
        sources=(
            {"title": "Virtual-care access baseline", "source_type": "internal", "publisher": "CareWeave Analytics", "credibility": "high"},
            {"title": "Patient digital inclusion listening sessions", "source_type": "stakeholder", "publisher": "CareWeave Patient Council", "credibility": "high"},
            {"title": "Clinical workload and safety review", "source_type": "expert", "publisher": "Independent Clinical Panel", "credibility": "moderate"},
        ),
        signals=(
            {"title": "Remote-monitoring demand is rising faster than support capacity", "summary": "Referrals for home monitoring are increasing while onboarding support remains fixed.", "future_implication": "Scale without service design could shift burden to patients and frontline teams.", "steep_category": "social", "time_horizon": "near", "maturity": "established", "polarity": "both", "impact": 5, "uncertainty": 2},
            {"title": "Clinical teams are adopting asynchronous review unevenly", "summary": "Some specialties use asynchronous review routinely; others rely on synchronous appointments.", "future_implication": "A single operating model may create hidden workload and professional resistance.", "steep_category": "technological", "time_horizon": "near", "maturity": "emerging", "polarity": "both", "impact": 4, "uncertainty": 3},
            {"title": "Digital exclusion is becoming more visible", "summary": "Language, disability, connectivity, and confidence barriers are increasingly documented.", "future_implication": "Access metrics must include who is excluded, not only total virtual contacts.", "steep_category": "ethical", "time_horizon": "near", "maturity": "established", "polarity": "threat", "impact": 5, "uncertainty": 2},
            {"title": "Outcome-based service funding is gaining support", "summary": "Commissioning discussions increasingly emphasise access, safety, and avoided acute activity.", "future_implication": "A staged model with explicit outcomes may attract stronger institutional support.", "steep_category": "political", "time_horizon": "medium", "maturity": "emerging", "polarity": "opportunity", "impact": 4, "uncertainty": 3},
        ),
        drivers=(
            {"title": "Workforce availability", "description": "Availability of clinical and coordination capacity for redesigned pathways.", "driver_type": "critical_uncertainty", "steep_category": "social", "direction": "decreasing", "impact": 5, "uncertainty": 5},
            {"title": "Patient digital readiness", "description": "Ability and willingness of diverse patient groups to use virtual pathways.", "driver_type": "critical_uncertainty", "steep_category": "ethical", "direction": "volatile", "impact": 5, "uncertainty": 4},
            {"title": "Clinical interoperability", "description": "Reliable flow of referrals, observations, escalation, and documentation.", "driver_type": "driver", "steep_category": "technological", "direction": "increasing", "impact": 4, "uncertainty": 3},
            {"title": "Local leadership commitment", "description": "Consistency of clinical and operational sponsorship across localities.", "driver_type": "driver", "steep_category": "political", "direction": "volatile", "impact": 4, "uncertainty": 4},
        ),
        scenario_axes=("Severe workforce constraint", "Manageable workforce constraint", "Low patient readiness", "High patient readiness"),
        scenarios=(
            {"code": "A", "title": "Supported adoption", "x": "high", "y": "high", "headline": "Capacity and readiness allow virtual care to become a normal pathway.", "narrative": "Clinical teams, patients, and support services adapt together with visible safeguards.", "opportunities": "Scale pathways and redeploy capacity to higher-acuity care.", "threats": "Success may encourage over-expansion before evidence stabilises."},
            {"code": "B", "title": "Demand without capacity", "x": "low", "y": "high", "headline": "Patients are ready but workforce constraints limit safe delivery.", "narrative": "Demand grows faster than clinical review and coordination capacity.", "opportunities": "Automate low-risk tasks and redesign roles.", "threats": "Backlogs move rather than disappear; burnout and safety incidents increase."},
            {"code": "C", "title": "Protected transition", "x": "high", "y": "low", "headline": "Capacity exists, but many patients need alternatives and active support.", "narrative": "The service invests in blended access, navigation, and assisted digital pathways.", "opportunities": "Build an equitable model with stronger trust.", "threats": "Costs rise if inclusion is treated as a parallel service."},
            {"code": "D", "title": "Fragmented care", "x": "low", "y": "low", "headline": "Low capacity and low readiness make rapid scale unsafe.", "narrative": "Virtual care remains limited to narrowly selected pathways while core services stabilise.", "opportunities": "Focus on high-value, low-complexity use cases.", "threats": "Regional inequity and duplicated local solutions persist."},
        ),
        evidence=(
            {"title": "Specialty pathway baseline", "summary": "Two specialties have measurable delays that virtual review could reduce.", "source_type": "internal_data", "stance": "supports", "strength": "high", "option": 2},
            {"title": "Patient partnership findings", "summary": "Patients prefer choice, assisted access, and clear escalation routes over digital-only pathways.", "source_type": "stakeholder_input", "stance": "challenges", "strength": "high", "option": 0},
            {"title": "Clinical governance review", "summary": "A shared protocol is feasible if responsibility for escalation remains explicit.", "source_type": "expert_judgement", "stance": "supports", "strength": "moderate", "option": 2},
            {"title": "Locality readiness survey", "summary": "Readiness varies substantially by specialty and locality.", "source_type": "internal_data", "stance": "challenges", "strength": "high", "option": 1},
        ),
        assumptions=(
            {"statement": "Clinical teams can protect weekly redesign time during the pilot.", "rationale": "Local leaders support the pilot but rota changes are not yet agreed.", "impact_if_false": "The pathway could be layered onto existing workload and fail for avoidable reasons.", "confidence": "low"},
            {"statement": "Assisted-digital support can be commissioned before launch.", "rationale": "Potential partners exist and funding has been identified.", "impact_if_false": "Excluded patients may experience worse access and confidence.", "confidence": "medium"},
            {"statement": "Outcome data can be linked across referral and acute-care systems.", "rationale": "Data teams have a feasible design but information-governance approval is pending.", "impact_if_false": "The organisation cannot distinguish activity transfer from genuine improvement.", "confidence": "medium"},
        ),
        risks=(
            {"title": "Hidden workload transfer", "description": "Remote pathways may shift administrative and monitoring work to clinicians without removing other tasks.", "likelihood": 4, "impact": 5, "response_strategy": "mitigate", "mitigation_plan": "Baseline workload, redesign roles, cap caseloads, and review weekly during launch."},
            {"title": "Digital exclusion", "description": "Patients facing language, disability, connectivity, or confidence barriers may receive worse access.", "likelihood": 4, "impact": 5, "response_strategy": "avoid", "mitigation_plan": "Guarantee non-digital routes, assisted access, accessibility testing, and equity metrics."},
            {"title": "Unclear escalation accountability", "description": "Delayed or abnormal readings may not reach the right clinical owner quickly.", "likelihood": 3, "impact": 5, "response_strategy": "mitigate", "mitigation_plan": "Define escalation ownership, simulation-test protocols, and audit response times."},
        ),
    ),
    ClientSpec(
        slug="terrafood-futures-institute-sim",
        name="TerraFood Futures Institute",
        brand_name="TerraFood Futures",
        colour="#6c5b2e",
        description=(
            f"{SIMULATION_MARKER} A fictional agri-food research institute used to demonstrate technology foresight, "
            "portfolio prioritisation, final decision records, implementation commitments, and organisational learning."
        ),
        workspace_name="Research and Innovation Portfolio",
        workspace_slug="research-innovation-portfolio",
        workspace_description="Long-horizon research choices for resilient and sustainable food systems.",
        decision_title="Prioritise the first 2035 climate-resilient research programme",
        decision_question=(
            "Which cross-disciplinary research programme should TerraFood implement first to strengthen farm resilience, "
            "environmental performance, and adoption by 2035?"
        ),
        purpose="Commit the first multi-year programme and preserve a traceable rationale for future portfolio reviews.",
        context=(
            "Climate volatility, input costs, regulation, labour availability, and uneven technology adoption are changing "
            "the value of traditional discipline-specific research programmes."
        ),
        scope=(
            "A five-year research programme combining field trials, decision support, stakeholder participation, and policy evidence. "
            "Routine extension services and commercial product development are out of scope."
        ),
        guidance=(
            "Assess system effects across farms, value chains, environment, and rural communities. State adoption assumptions and "
            "identify evidence that would cause the programme to pivot."
        ),
        urgency="normal",
        status="implementation",
        people=(
            PersonSpec("maeve.sullivan@terrafood.example", "Maeve", "Sullivan", "Research Strategy Director"),
            PersonSpec("ibrahim.diallo@terrafood.example", "Ibrahim", "Diallo", "Climate Systems Scientist"),
            PersonSpec("laura.chen@terrafood.example", "Laura", "Chen", "Industry Partnership Lead"),
        ),
        options=(
            {"title": "Climate-resilient genetics programme", "description": "Concentrate on resilient crop and livestock genetics with long-term field validation.", "expected_benefits": "Deep scientific capability and potentially durable productivity gains.", "tradeoffs": "Long time to impact and dependence on adoption, regulation, and complementary practices.", "is_status_quo": False},
            {"title": "Circular bioeconomy programme", "description": "Prioritise nutrient recovery, side-stream valorisation, and low-waste value chains.", "expected_benefits": "New revenue pathways and measurable environmental benefits.", "tradeoffs": "Complex coordination and uncertain market development.", "is_status_quo": False},
            {"title": "Integrated resilient farm-systems programme", "description": "Combine climate analytics, practice trials, farmer decision support, and policy learning.", "expected_benefits": "Earlier usable outcomes, stronger adoption evidence, and cross-system learning.", "tradeoffs": "Broad scope requires disciplined programme governance and shared methods.", "is_status_quo": False},
        ),
        sources=(
            {"title": "Farm resilience longitudinal dataset", "source_type": "dataset", "publisher": "TerraFood Research Data Office", "credibility": "high"},
            {"title": "Farmer and adviser futures workshops", "source_type": "stakeholder", "publisher": "TerraFood Engagement Unit", "credibility": "high"},
            {"title": "2035 agri-food policy pathways review", "source_type": "government", "publisher": "Fictional Food Systems Department", "credibility": "moderate"},
        ),
        signals=(
            {"title": "Climate variability is outpacing static recommendations", "summary": "Seasonal patterns and extremes are reducing the reliability of fixed advisory calendars.", "future_implication": "Research must produce adaptive decision rules, not only average-response guidance.", "steep_category": "environmental", "time_horizon": "near", "maturity": "established", "polarity": "threat", "impact": 5, "uncertainty": 2},
            {"title": "Farm data tools are becoming cheaper but more fragmented", "summary": "Sensor and analytics adoption is rising without common interpretation standards.", "future_implication": "Decision-support interoperability may matter more than any single tool.", "steep_category": "technological", "time_horizon": "medium", "maturity": "emerging", "polarity": "both", "impact": 4, "uncertainty": 3},
            {"title": "Environmental performance is moving into market access", "summary": "Buyers increasingly request verified emissions, biodiversity, and nutrient data.", "future_implication": "Research value will be judged partly by credible measurement and implementation pathways.", "steep_category": "economic", "time_horizon": "medium", "maturity": "emerging", "polarity": "both", "impact": 5, "uncertainty": 3},
            {"title": "Farmers prefer co-designed, testable recommendations", "summary": "Engagement shows stronger trust where farmers can challenge assumptions and see local evidence.", "future_implication": "Participatory research design may become a core capability rather than dissemination activity.", "steep_category": "social", "time_horizon": "near", "maturity": "established", "polarity": "opportunity", "impact": 4, "uncertainty": 2},
        ),
        drivers=(
            {"title": "Climate volatility", "description": "Frequency and severity of weather and biological shocks.", "driver_type": "critical_uncertainty", "steep_category": "environmental", "direction": "increasing", "impact": 5, "uncertainty": 5},
            {"title": "Farmer adoption capacity", "description": "Financial, cognitive, labour, and advisory capacity to implement new practices.", "driver_type": "critical_uncertainty", "steep_category": "social", "direction": "volatile", "impact": 5, "uncertainty": 4},
            {"title": "Outcome verification requirements", "description": "Market and policy demand for credible environmental and resilience evidence.", "driver_type": "trend", "steep_category": "legal", "direction": "increasing", "impact": 4, "uncertainty": 3},
            {"title": "Cross-disciplinary research capability", "description": "Ability to integrate biological, digital, economic, and behavioural research.", "driver_type": "driver", "steep_category": "technological", "direction": "increasing", "impact": 4, "uncertainty": 3},
        ),
        scenario_axes=("Moderate climate volatility", "Severe climate volatility", "Low adoption capacity", "High adoption capacity"),
        scenarios=(
            {"code": "A", "title": "Adaptive acceleration", "x": "high", "y": "high", "headline": "Severe pressure combines with strong adoption and learning capacity.", "narrative": "Demand for integrated evidence is high and farms rapidly test adaptive practices.", "opportunities": "Scale decision support and system-level trials.", "threats": "Research cycles may be pushed faster than quality assurance allows."},
            {"code": "B", "title": "Resilience divide", "x": "high", "y": "low", "headline": "Severe shocks meet limited capacity to respond.", "narrative": "Benefits concentrate among well-resourced farms unless programmes include transition support.", "opportunities": "Target vulnerable systems and simplify adoption pathways.", "threats": "Exit, inequality, and policy conflict increase."},
            {"code": "C", "title": "Steady transformation", "x": "low", "y": "high", "headline": "Moderate pressure allows cumulative, evidence-led improvement.", "narrative": "Research partnerships mature and practices spread through trusted networks.", "opportunities": "Build durable platforms and longitudinal evidence.", "threats": "Urgency may fade and investment may fragment."},
            {"code": "D", "title": "Incremental lock-in", "x": "low", "y": "low", "headline": "Moderate pressure and low capacity reinforce incremental programmes.", "narrative": "Existing systems persist while strategic capability erodes.", "opportunities": "Use low-cost demonstration and advisory integration.", "threats": "The sector is unprepared when volatility increases."},
        ),
        evidence=(
            {"title": "Longitudinal resilience analysis", "summary": "Integrated management practices explain more resilience variance than isolated technology adoption.", "source_type": "research", "stance": "supports", "strength": "high", "option": 2},
            {"title": "Farmer futures workshops", "summary": "Participants favour testable packages with transparent trade-offs over single-solution programmes.", "source_type": "stakeholder_input", "stance": "supports", "strength": "high", "option": 2},
            {"title": "Commercial pathway review", "summary": "Circular bioeconomy opportunities are material but depend on infrastructure and offtake coordination.", "source_type": "expert_judgement", "stance": "mixed", "strength": "moderate", "option": 1},
            {"title": "Genetics impact horizon", "summary": "Genetics remains strategically important but near-term resilience benefits require complementary management changes.", "source_type": "research", "stance": "mixed", "strength": "high", "option": 0},
        ),
        assumptions=(
            {"statement": "Research teams will adopt shared system-level outcome measures.", "rationale": "Leadership supports integration but disciplines use different success conventions.", "impact_if_false": "The programme may become a bundle of projects rather than a coherent learning system.", "confidence": "medium"},
            {"statement": "A representative farm network can be maintained for five years.", "rationale": "Existing relationships are strong but participation costs are rising.", "impact_if_false": "External validity and adoption evidence would weaken.", "confidence": "medium"},
            {"statement": "Policy partners will use interim evidence before final programme completion.", "rationale": "Partners requested annual synthesis but governance is informal.", "impact_if_false": "Useful learning may arrive too late to shape policy cycles.", "confidence": "low"},
        ),
        risks=(
            {"title": "Programme breadth dilutes accountability", "description": "Cross-disciplinary scope could obscure ownership and produce disconnected work packages.", "likelihood": 3, "impact": 4, "response_strategy": "mitigate", "mitigation_plan": "Use shared outcomes, integration reviews, and explicit stop-or-merge decisions."},
            {"title": "Participation bias", "description": "Research farms may over-represent organisations already able to adopt innovation.", "likelihood": 4, "impact": 4, "response_strategy": "mitigate", "mitigation_plan": "Recruit stratified cohorts, fund participation, and publish representation gaps."},
            {"title": "Policy timing mismatch", "description": "Policy decisions may precede robust programme evidence.", "likelihood": 4, "impact": 3, "response_strategy": "monitor", "mitigation_plan": "Publish bounded interim findings with uncertainty and pre-agreed review dates."},
        ),
        selected_option_index=2,
    ),
)


class Command(BaseCommand):
    help = "Create three fictional CrowdSmarter client organisations with rich decision and foresight data."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Build and validate the complete data set, then roll the transaction back.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        existing = list(
            Organisation.objects.filter(slug__in=SIMULATED_SLUGS).values_list("slug", flat=True)
        )
        if existing:
            raise CommandError(
                "Simulated clients already exist: "
                + ", ".join(sorted(existing))
                + ". This command is intentionally non-destructive and will not overwrite them."
            )

        administrators = [
            item.user
            for item in PlatformAdministrator.objects.select_related("user").filter(
                status=PlatformAdministrator.Status.ACTIVE,
                user__is_active=True,
            ).order_by("user__email")
        ]
        if not administrators:
            administrators = list(
                get_user_model().objects.filter(is_active=True, is_superuser=True).order_by("email")
            )
        if not administrators:
            raise CommandError(
                "No active administrator account exists. Create or activate an owner account before seeding simulations."
            )

        primary_admin = administrators[0]
        now = timezone.now()
        self.stdout.write(f"Primary simulated-client owner: {primary_admin.email}")
        if len(administrators) > 1:
            self.stdout.write(
                "Additional active platform administrators will receive owner membership in the simulations: "
                + ", ".join(user.email for user in administrators[1:])
            )

        with transaction.atomic():
            summary = {"organisations": 0, "users": 0, "decisions": 0, "signals": 0, "scenarios": 0}
            for spec in CLIENTS:
                counts = self._create_client(spec, primary_admin, administrators, now)
                for key, value in counts.items():
                    summary[key] += value

            if options["dry_run"]:
                transaction.set_rollback(True)
                label = "Dry run passed; all simulated data was rolled back."
            else:
                label = "Simulated client data committed successfully."

        self.stdout.write(self.style.SUCCESS(label))
        self.stdout.write(
            "Created/validated: "
            f"{summary['organisations']} organisations, {summary['users']} fictional users, "
            f"{summary['decisions']} decisions, {summary['signals']} signals, "
            f"and {summary['scenarios']} scenarios."
        )
        self.stdout.write(
            "All organisations and users are fictional. Their descriptions contain an explicit simulation marker."
        )

    def _create_client(
        self,
        spec: ClientSpec,
        primary_admin: Any,
        administrators: list[Any],
        now: Any,
    ) -> dict[str, int]:
        organisation = Organisation.objects.create(
            name=spec.name,
            slug=spec.slug,
            description=spec.description,
            website_url=f"https://{spec.slug}.example",
            brand_name=spec.brand_name,
            primary_colour=spec.colour,
            retention_days=365,
            created_by=primary_admin,
        )
        Membership.objects.create(
            organisation=organisation,
            user=primary_admin,
            role="owner",
            status="active",
        )
        for administrator in administrators[1:]:
            Membership.objects.create(
                organisation=organisation,
                user=administrator,
                role="owner",
                status="active",
            )

        fictional_users: list[Any] = []
        for index, person in enumerate(spec.people):
            user = get_user_model().objects.create_user(
                email=person.email,
                password=None,
                first_name=person.first_name,
                last_name=person.last_name,
                is_active=True,
            )
            fictional_users.append(user)
            Membership.objects.create(
                organisation=organisation,
                user=user,
                role="admin" if index == 0 else "contributor",
                status="active",
            )

        workspace = Workspace.objects.create(
            organisation=organisation,
            name=spec.workspace_name,
            slug=spec.workspace_slug,
            description=spec.workspace_description,
            is_default=True,
            created_by=primary_admin,
        )
        decision = Decision.objects.create(
            organisation=organisation,
            workspace=workspace,
            title=spec.decision_title,
            decision_question=spec.decision_question,
            purpose=spec.purpose,
            context=spec.context,
            scope=spec.scope,
            contribution_guidance=spec.guidance,
            urgency=spec.urgency,
            target_decision_date=date.today() + timedelta(days=60),
            contribution_deadline=now + timedelta(days=21),
            status=spec.status,
            status_changed_at=now,
            owner=fictional_users[0],
            created_by=primary_admin,
        )

        options = [
            DecisionOption.objects.create(
                organisation=organisation,
                decision=decision,
                proposed_by=fictional_users[index % len(fictional_users)],
                created_by=primary_admin,
                **option,
            )
            for index, option in enumerate(spec.options)
        ]

        participants = [
            Participant.objects.create(
                organisation=organisation,
                decision=decision,
                user=fictional_users[0],
                role="decision_owner",
                added_by=primary_admin,
            ),
            Participant.objects.create(
                organisation=organisation,
                decision=decision,
                user=fictional_users[1],
                role="contributor",
                added_by=primary_admin,
            ),
            Participant.objects.create(
                organisation=organisation,
                decision=decision,
                user=fictional_users[2],
                role="reviewer",
                added_by=primary_admin,
            ),
            Participant.objects.create(
                organisation=organisation,
                decision=decision,
                user=primary_admin,
                role="decision_maker",
                added_by=primary_admin,
            ),
        ]

        Position.objects.create(
            organisation=organisation,
            decision=decision,
            participant=participants[1],
            participant_role=participants[1].role,
            preferred_option=options[2],
            recommendation="support_with_conditions",
            rationale="The staged option preserves learning while addressing the most immediate system need.",
            conditions="Publish decision gates, equity measures, and evidence that would trigger a pivot.",
            confidence="high",
            version=1,
            submitted_by=fictional_users[1],
        )
        Position.objects.create(
            organisation=organisation,
            decision=decision,
            participant=participants[2],
            participant_role=participants[2].role,
            preferred_option=options[2],
            recommendation="support_with_conditions",
            rationale="The preferred option is acceptable only if affected stakeholders remain involved in implementation review.",
            conditions="Maintain accessible alternatives and publish distributional outcomes.",
            confidence="medium",
            version=1,
            submitted_by=fictional_users[2],
        )

        sources = [
            Source.objects.create(
                organisation=organisation,
                title=item["title"],
                source_type=item["source_type"],
                author="Simulation Research Team",
                publisher=item["publisher"],
                published_on=date.today() - timedelta(days=45 + index * 20),
                reference=f"SIM-{spec.slug.upper()}-{index + 1}",
                credibility=item["credibility"],
                credibility_rationale="Credibility rating is part of the fictional demonstration data.",
                notes=SIMULATION_MARKER,
                created_by=primary_admin,
            )
            for index, item in enumerate(spec.sources)
        ]
        signals = [
            Signal.objects.create(
                organisation=organisation,
                source=sources[index % len(sources)],
                geography="Fictional demonstration region",
                domain=spec.workspace_name,
                status="monitoring",
                owner=fictional_users[index % len(fictional_users)],
                created_by=primary_admin,
                last_reviewed_at=now - timedelta(days=index * 4),
                last_reviewed_by=fictional_users[0],
                **item,
            )
            for index, item in enumerate(spec.signals)
        ]
        watchlist = Watchlist.objects.create(
            organisation=organisation,
            name=f"{spec.brand_name} strategic watchlist",
            description="Signals that could change the decision, its implementation gates, or review timing.",
            owner=fictional_users[1],
            created_by=primary_admin,
        )
        for index, signal in enumerate(signals):
            WatchlistSignal.objects.create(
                watchlist=watchlist,
                signal=signal,
                added_by=primary_admin,
                note=f"Review at decision gate {index + 1} or earlier if movement is material.",
            )
            SignalDecisionLink.objects.create(
                signal=signal,
                decision=decision,
                relevance=signal.future_implication,
                linked_by=primary_admin,
            )

        evidence_items = []
        for index, item in enumerate(spec.evidence):
            evidence_items.append(
                Evidence.objects.create(
                    organisation=organisation,
                    decision=decision,
                    source=sources[index % len(sources)],
                    option=options[item["option"]],
                    title=item["title"],
                    summary=item["summary"],
                    source_type=item["source_type"],
                    source_reference=f"Simulation evidence {index + 1}",
                    stance=item["stance"],
                    strength=item["strength"],
                    created_by=primary_admin,
                )
            )

        assumptions = [
            Assumption.objects.create(
                organisation=organisation,
                decision=decision,
                option=options[2] if index == 0 else None,
                statement=item["statement"],
                rationale=item["rationale"],
                impact_if_false=item["impact_if_false"],
                confidence=item["confidence"],
                verification_status="partially_verified" if index == 1 else "unverified",
                verification_notes="Simulation: verification evidence remains intentionally incomplete.",
                owner=fictional_users[index % len(fictional_users)],
                review_date=date.today() + timedelta(days=30 + index * 15),
                created_by=primary_admin,
            )
            for index, item in enumerate(spec.assumptions)
        ]
        risks = [
            Risk.objects.create(
                organisation=organisation,
                decision=decision,
                option=options[2] if index < 2 else None,
                owner=fictional_users[index % len(fictional_users)],
                review_date=date.today() + timedelta(days=21 + index * 14),
                created_by=primary_admin,
                **item,
            )
            for index, item in enumerate(spec.risks)
        ]

        canvas = ForesightCanvas.objects.create(
            organisation=organisation,
            title=f"{spec.brand_name} 2035 system canvas",
            focal_question=spec.decision_question,
            scope=spec.scope,
            horizon_year=2035,
            owner=fictional_users[1],
            created_by=primary_admin,
            status="active",
        )
        drivers = [
            Driver.objects.create(
                canvas=canvas,
                owner=fictional_users[index % len(fictional_users)],
                created_by=primary_admin,
                **item,
            )
            for index, item in enumerate(spec.drivers)
        ]
        for index, driver in enumerate(drivers):
            DriverSignal.objects.create(
                driver=driver,
                signal=signals[index],
                rationale="The signal provides observable evidence about the direction or uncertainty of this driver.",
                linked_by=primary_admin,
            )
        SystemStakeholder.objects.bulk_create(
            [
                SystemStakeholder(canvas=canvas, name="Operational teams", stakeholder_type="internal", role="Deliver and govern the chosen model.", interests="Safety, feasibility, workload, and clear accountability.", influence=5, exposure=5, stance="mixed", created_by=primary_admin),
                SystemStakeholder(canvas=canvas, name="Customers and service users", stakeholder_type="customer", role="Experience the benefits, burdens, and access conditions.", interests="Fair outcomes, understandable choices, and reliable service.", influence=3, exposure=5, stance="mixed", created_by=primary_admin),
                SystemStakeholder(canvas=canvas, name="Regulators and public authorities", stakeholder_type="regulator", role="Set constraints, incentives, and assurance expectations.", interests="Public value, compliance, resilience, and evidence.", influence=5, exposure=3, stance="neutral", created_by=primary_admin),
                SystemStakeholder(canvas=canvas, name="Delivery partners", stakeholder_type="partner", role="Provide capability, infrastructure, and specialist knowledge.", interests="Stable requirements, viable contracts, and trusted collaboration.", influence=4, exposure=4, stance="supportive", created_by=primary_admin),
            ]
        )
        CausalRelationship.objects.create(canvas=canvas, source_driver=drivers[0], target_driver=drivers[1], polarity="reinforcing", strength=4, delay="short", rationale="Faster external change increases pressure on trust, adoption, and perceived fairness.", created_by=primary_admin)
        CausalRelationship.objects.create(canvas=canvas, source_driver=drivers[2], target_driver=drivers[1], polarity="reinforcing", strength=3, delay="medium", rationale="Better enabling capability can improve confidence and participation when governance is visible.", created_by=primary_admin)

        implication = StrategicImplication.objects.create(
            canvas=canvas,
            title="Use explicit scale, stop, and pivot gates",
            description="The preferred option should be implemented as a learning portfolio with observable decision gates rather than an irreversible programme.",
            implication_type="decision_requirement",
            priority=5,
            owner=fictional_users[0],
            linked_decision=decision,
            status="open",
            created_by=primary_admin,
        )
        implication.drivers.add(drivers[0], drivers[1], drivers[2])

        scenario_set = ScenarioSet.objects.create(
            canvas=canvas,
            title=f"{spec.brand_name} critical uncertainty scenarios",
            purpose="Test the strategic options against materially different operating environments.",
            axis_x_driver=drivers[0],
            axis_x_low_label=spec.scenario_axes[0],
            axis_x_high_label=spec.scenario_axes[1],
            axis_y_driver=drivers[1],
            axis_y_low_label=spec.scenario_axes[2],
            axis_y_high_label=spec.scenario_axes[3],
            linked_decision=decision,
            owner=fictional_users[1],
            created_by=primary_admin,
            status="complete",
        )
        scenarios = []
        for index, item in enumerate(spec.scenarios):
            scenario = Scenario.objects.create(
                scenario_set=scenario_set,
                title=item["title"],
                code=item["code"],
                axis_x_position=item["x"],
                axis_y_position=item["y"],
                headline=item["headline"],
                narrative=item["narrative"],
                key_assumptions="This is a deliberately plausible, not predictive, scenario used for decision testing.",
                opportunities=item["opportunities"],
                threats=item["threats"],
                status="reviewed",
                created_by=primary_admin,
            )
            scenarios.append(scenario)
            for d_index, driver in enumerate(drivers):
                ScenarioDriverState.objects.create(
                    scenario=scenario,
                    driver=driver,
                    state=("strengthening", "volatile", "transformed", "stable")[(index + d_index) % 4],
                    salience=5 if d_index < 2 else 3,
                    description=f"In {scenario.title}, {driver.title.lower()} materially shapes feasibility and timing.",
                    created_by=primary_admin,
                )
            ScenarioReview.objects.create(
                scenario=scenario,
                reviewer=fictional_users[2],
                plausibility=4,
                internal_consistency=4,
                distinctiveness=4,
                usefulness=5,
                confidence=4,
                comment="The scenario is sufficiently distinct and decision-relevant for wind-tunnelling.",
            )
            ScenarioImplicationLink.objects.create(
                scenario=scenario,
                implication=implication,
                effect="amplifies" if index in (1, 3) else "changes",
                rationale="The scenario changes the urgency and design of staged decision gates.",
                linked_by=primary_admin,
            )
            for option_index, option in enumerate(options):
                base = 3 + ((2 - abs(option_index - 2)) if option_index == 2 else 0)
                WindTunnelAssessment.objects.create(
                    scenario=scenario,
                    option=option,
                    verdict="robust" if option_index == 2 else ("adaptable" if index % 2 == 0 else "vulnerable"),
                    desirability=min(5, base),
                    feasibility=4 if option_index == 2 else 3,
                    resilience=5 if option_index == 2 else 3,
                    rationale="Assessment compares strategic fit, feasibility, resilience, and reversibility in this scenario.",
                    conditions_for_success="Maintain transparent gates, accountable owners, and measurable outcomes.",
                    vulnerabilities="Resource, adoption, and timing assumptions may move together.",
                    mitigations="Preserve fallback capacity and review signposts before each scale decision.",
                    assessed_by=fictional_users[1],
                )

        signpost = Signpost.objects.create(
            scenario_set=scenario_set,
            title="Material movement in the primary uncertainty",
            description="A monitored indicator that would change the preferred implementation path or review date.",
            indicator=drivers[0].title,
            threshold="Two consecutive reporting periods outside the current planning range.",
            direction="change",
            review_cadence="quarterly",
            source_notes="Simulation indicator assembled from the fictional source set.",
            owner=fictional_users[1],
            created_by=primary_admin,
            status="active",
        )
        for scenario in scenarios:
            ScenarioSignpost.objects.create(
                signpost=signpost,
                scenario=scenario,
                relationship="supports" if scenario.axis_x_position == "high" else "contextual",
                rationale="Observed movement would increase or decrease the relevance of this scenario.",
                linked_by=primary_admin,
            )
        SignpostObservation.objects.create(
            signpost=signpost,
            observed_on=date.today() - timedelta(days=14),
            value="Early movement, still inside the planning range",
            assessment="weak",
            evidence="The latest fictional monitoring note shows movement but not enough to trigger a decision gate.",
            source=sources[0],
            created_by=primary_admin,
        )

        exercise = EvaluationExercise.objects.create(
            organisation=organisation,
            decision=decision,
            title="Cross-functional option evaluation",
            purpose="Compare options transparently while preserving objections and confidence.",
            method="scorecard",
            status="closed" if spec.status in {"ready_for_decision", "implementation"} else "open",
            anonymity="peer_anonymous",
            blind_results_until_close=True,
            quorum_count=3,
            approval_threshold=65,
            objection_threshold=20,
            owner=fictional_users[0],
            created_by=primary_admin,
        )
        criteria = [
            EvaluationCriterion.objects.create(organisation=organisation, exercise=exercise, title="Strategic value", description="Contribution to the stated outcomes.", weight=Decimal("1.40"), order=1),
            EvaluationCriterion.objects.create(organisation=organisation, exercise=exercise, title="Feasibility", description="Operational, technical, and capability feasibility.", weight=Decimal("1.20"), order=2),
            EvaluationCriterion.objects.create(organisation=organisation, exercise=exercise, title="Equity and legitimacy", description="Distributional effects, inclusion, and stakeholder trust.", weight=Decimal("1.30"), order=3),
            EvaluationCriterion.objects.create(organisation=organisation, exercise=exercise, title="Scenario robustness", description="Performance across the four scenarios.", weight=Decimal("1.50"), order=4),
        ]
        evaluation_round = EvaluationRound.objects.create(
            organisation=organisation,
            exercise=exercise,
            number=1,
            title="Initial independent scoring",
            status="closed" if exercise.status == "closed" else "open",
            feedback_summary="The staged option scores highest overall; concerns focus on governance capacity and inclusion.",
            opens_at=now - timedelta(days=14),
            closes_at=now - timedelta(days=2) if exercise.status == "closed" else now + timedelta(days=7),
            opened_by=primary_admin,
            closed_by=primary_admin if exercise.status == "closed" else None,
        )
        for user_index, user in enumerate(fictional_users):
            submission = EvaluationSubmission.objects.create(
                organisation=organisation,
                round=evaluation_round,
                submitted_by=user,
                status="submitted",
                confidence=4 - (user_index % 2),
                overall_rationale="Scores reflect evidence, scenario performance, implementation constraints, and stakeholder effects.",
                submitted_at=now - timedelta(days=5 - user_index),
            )
            for option_index, option in enumerate(options):
                for criterion_index, criterion in enumerate(criteria):
                    score = Decimal(str(3 + (2 if option_index == 2 else 0) - (1 if criterion_index == 2 and option_index == 0 else 0)))
                    EvaluationResponse.objects.create(
                        organisation=organisation,
                        submission=submission,
                        option=option,
                        criterion=criterion,
                        score=max(Decimal("1"), min(Decimal("5"), score)),
                        rationale="Simulation score with a concise, attributable rationale.",
                    )
        MinorityReport.objects.create(
            organisation=organisation,
            exercise=exercise,
            round=evaluation_round,
            author=fictional_users[2],
            title="Do not treat the staged option as automatically inclusive",
            analysis="A staged approach can still reproduce inequity if participation, access, and burden are not measured at each gate.",
            recommendation="Make distributional evidence a mandatory scale criterion and publish unresolved concerns.",
        )

        session = FacilitationSession.objects.create(
            organisation=organisation,
            decision=decision,
            title="Assumptions, evidence, and stakeholder challenge session",
            objective="Challenge the preferred option before authority is exercised.",
            agenda="1. Evidence gaps\n2. Assumptions\n3. Stakeholder effects\n4. Scenario vulnerabilities\n5. Decision conditions",
            participation_guidance="Write first, distinguish evidence from judgement, and record unresolved disagreement.",
            facilitator=fictional_users[0],
            starts_at=now - timedelta(days=12),
            ends_at=now - timedelta(days=12) + timedelta(hours=2),
            status="closed",
            created_by=primary_admin,
            closed_at=now - timedelta(days=12) + timedelta(hours=2),
        )
        for user in fictional_users:
            SessionParticipant.objects.create(
                session=session,
                organisation=organisation,
                user=user,
                role="participant",
                attendance="attended",
                added_by=primary_admin,
            )
        request = ContributionRequest.objects.create(
            organisation=organisation,
            decision=decision,
            option=options[2],
            session=session,
            requested_by=fictional_users[0],
            assignee=fictional_users[2],
            reviewer=fictional_users[0],
            kind="stakeholder",
            title="Document the strongest stakeholder challenge",
            instructions="Describe who bears risk, what evidence is missing, and the condition that should be attached to the preferred option.",
            priority="high",
            status="accepted",
            due_at=now - timedelta(days=7),
            opened_at=now - timedelta(days=12),
            submitted_at=now - timedelta(days=9),
            reviewed_at=now - timedelta(days=8),
            completed_at=now - timedelta(days=8),
        )
        submission = ContributionSubmission.objects.create(
            organisation=organisation,
            decision=decision,
            request=request,
            author=fictional_users[2],
            sequence=1,
            body="The preferred option remains credible only if underserved groups and operational teams influence each scale gate, not merely the initial design.",
            references="Simulation listening sessions; equity analysis; workload review.",
            status="submitted",
            submitted_at=now - timedelta(days=9),
        )
        ContributionReview.objects.create(
            organisation=organisation,
            decision=decision,
            request=request,
            submission=submission,
            reviewer=fictional_users[0],
            outcome="accepted",
            note="Accepted as a binding design condition and linked to the executive summary.",
        )

        discussion = DiscussionEntry.objects.create(
            organisation=organisation,
            decision=decision,
            author=fictional_users[1],
            kind="concern",
            body="The preferred option is robust only if governance capacity is funded before scale begins.",
        )
        discussion.mentioned_users.add(fictional_users[0], primary_admin)
        DiscussionEntry.objects.create(
            organisation=organisation,
            decision=decision,
            author=fictional_users[0],
            kind="update",
            body="Governance capacity has been added as an explicit implementation condition and review item.",
            reply_to=discussion,
        )

        DecisionIssue.objects.create(
            organisation=organisation,
            decision=decision,
            assumption=assumptions[0],
            evaluation_exercise=exercise,
            scenario_set=scenario_set,
            issue_type="implementation_uncertainty",
            title="Governance capacity is not yet fully resourced",
            description="The preferred staged option requires portfolio management, evidence review, and authority for stop-or-scale decisions.",
            severity="high",
            status="in_progress",
            owner=fictional_users[0],
            due_date=date.today() + timedelta(days=21),
            created_by=primary_admin,
        )
        DecisionQualityReview.objects.create(
            organisation=organisation,
            decision=decision,
            version=1,
            status="published",
            judgement="ready_with_conditions" if spec.status != "open_for_contribution" else "not_ready",
            answers={
                "framing": "clear",
                "evidence": "mixed_but_traceable",
                "stakeholders": "material_views_recorded",
                "scenarios": "wind_tunnel_complete",
                "implementation": "conditions_required",
            },
            strengths="The decision has a clear question, attributable evidence, explicit assumptions, scenarios, and recorded minority concerns.",
            blockers="Governance capacity and one adoption assumption remain unresolved.",
            conditions="Fund implementation governance, publish decision gates, and review the leading signpost quarterly.",
            author=primary_admin,
            published_at=now - timedelta(days=1),
        )
        ExecutiveDecisionSummary.objects.create(
            organisation=organisation,
            decision=decision,
            version=1,
            status="approved" if spec.status in {"ready_for_decision", "implementation"} else "draft",
            context_summary=spec.context,
            options_summary="Three options were compared: concentrated change, distributed change, and a staged hybrid path.",
            evidence_summary="Evidence favours a staged option but also exposes capability and inclusion constraints.",
            uncertainty_summary="The two critical uncertainties are represented in four scenarios and monitored through signposts.",
            stakeholder_summary="Operational, service-user, partner, and regulatory perspectives are recorded; minority concerns remain visible.",
            scenario_summary="The staged option is the most adaptable across all four scenarios, provided decision gates are enforced.",
            evaluation_summary="Independent scoring ranks the staged option highest; objections concern governance and equity rather than strategic direction.",
            risk_summary="Top risks relate to burden transfer, unequal participation, capability, and timing.",
            unresolved_issues="Governance capacity and one adoption assumption require closure before unrestricted scale.",
            proposed_judgement="Proceed with the staged option under explicit scale, stop, and pivot conditions.",
            conditions="Publish gate criteria, fund accountable owners, preserve accessible alternatives, and review signposts quarterly.",
            implementation_implications="Begin with bounded pilots, protected fallback capacity, and an evidence review before each expansion.",
            created_by=primary_admin,
            approved_by=primary_admin if spec.status in {"ready_for_decision", "implementation"} else None,
            approved_at=now if spec.status in {"ready_for_decision", "implementation"} else None,
        )

        self._create_transitions(decision, organisation, primary_admin, spec.status)

        if spec.selected_option_index is not None:
            selected = options[spec.selected_option_index]
            DecisionFinalisation.objects.create(
                organisation=organisation,
                decision=decision,
                selected_option=selected,
                decided_by=primary_admin,
                rationale="The selected programme offers the strongest balance of usable near-term outcomes, long-horizon resilience, adoption evidence, and adaptability across scenarios.",
                conditions="Use annual portfolio gates, maintain a representative participation network, and preserve distinct genetics and circular-economy work packages where evidence supports them.",
                dissent_summary="A minority preferred deeper single-discipline investment and warned that integration could dilute scientific accountability.",
                position_snapshot=[
                    {"participant": participants[1].user.email, "recommendation": "support_with_conditions", "preferred_option": selected.title},
                    {"participant": participants[2].user.email, "recommendation": "support_with_conditions", "preferred_option": selected.title},
                ],
                decided_at=now - timedelta(days=30),
            )
            DecisionReview.objects.create(
                organisation=organisation,
                decision=decision,
                implementation_owner=fictional_users[0],
                commitment_statement="Launch the integrated resilient farm-systems programme with a bounded first-year portfolio and annual human-authorised review gates.",
                success_measures="Representative farm network established; shared outcome framework adopted; first field trials launched; policy synthesis published; participation gaps reported.",
                review_due_date=date.today() + timedelta(days=180),
                commitment_rationale="The commitment preserves the selected option's learning value while preventing automatic scale.",
                commitment_recorded_by=primary_admin,
                commitment_recorded_at=now - timedelta(days=28),
                implementation_plan="Appoint programme integration lead; confirm cohorts; approve shared measures; launch first trials; review signposts quarterly.",
                implementation_started_by=fictional_users[0],
                implementation_started_at=now - timedelta(days=21),
                implementation_summary="Programme governance is established and the first cohort is being recruited.",
            )
            Lesson.objects.create(
                organisation=organisation,
                decision=decision,
                title="Integration needs explicit authority, not only shared ambition",
                insight="Cross-disciplinary decisions become actionable only when integration responsibilities, evidence standards, and stop-or-scale authority are assigned.",
                category="process",
                applicability="Future research portfolios, multi-partner programmes, and any decision combining several disciplines or delivery organisations.",
                recommended_change="Require an integration owner and shared evidence framework before approving a cross-disciplinary programme.",
                created_by=primary_admin,
            )

        return {
            "organisations": 1,
            "users": len(fictional_users),
            "decisions": 1,
            "signals": len(signals),
            "scenarios": len(scenarios),
        }

    @staticmethod
    def _create_transitions(decision: Decision, organisation: Organisation, actor: Any, final_status: str) -> None:
        order = [
            "draft",
            "framing",
            "open_for_contribution",
            "under_review",
            "ready_for_decision",
            "decision_finalised",
            "commitment",
            "implementation",
        ]
        if final_status not in order:
            return
        target_index = order.index(final_status)
        for sequence, (from_status, to_status) in enumerate(
            zip(order[:target_index], order[1 : target_index + 1]), start=1
        ):
            DecisionTransition.objects.create(
                decision=decision,
                organisation=organisation,
                sequence=sequence,
                from_status=from_status,
                to_status=to_status,
                actor=actor,
                rationale="Simulation lifecycle transition created to demonstrate an auditable decision history.",
                warnings_acknowledged=[],
            )
