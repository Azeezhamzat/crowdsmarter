export type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff?: boolean;
  is_platform_administrator?: boolean;
};

export type LoginResult = User | { mfa_required: true };

export type MFAStatus = {
  is_enabled: boolean;
};

export type MFAEnrollment = {
  secret: string;
  provisioning_uri: string;
};

export type OrganisationRole = "owner" | "admin" | "contributor" | "viewer";

export type Organisation = {
  id: string;
  name: string;
  slug: string;
  description: string;
  website_url: string;
  brand_name: string;
  primary_colour: string;
  invitation_policy: "owners_and_admins" | "owners_only";
  default_invitation_role: "admin" | "contributor" | "viewer";
  retention_days: number | null;
  status: "active" | "deactivated";
  deactivated_at: string | null;
  current_user_role: OrganisationRole;
  created_at: string;
  updated_at: string;
};

export type Membership = {
  id: string;
  organisation_id: string;
  user: User;
  role: OrganisationRole;
  status: "active" | "suspended";
  created_at: string;
  updated_at: string;
};

export type PlanSupportLevel = "community" | "standard" | "priority";

export type Plan = {
  id: string;
  key: string;
  name: string;
  description: string;
  trial_days: number;
  max_active_decisions: number | null;
  max_active_members: number | null;
  includes_advanced_foresight: boolean;
  includes_ai_assistance: boolean;
  support_level: PlanSupportLevel;
  support_level_label: string;
};

export type OrganisationSubscription = {
  id: string;
  organisation_id: string;
  plan: Plan;
  status: "trialing" | "active" | "expired";
  status_label: string;
  trial_ends_at: string | null;
  is_trial_expired: boolean;
  billing_contact: User | null;
  started_at: string;
  active_decision_count: number;
  active_member_count: number;
  created_at: string;
  updated_at: string;
};

export type Workspace = {
  id: string;
  organisation_id: string;
  name: string;
  slug: string;
  description: string;
  is_default: boolean;
  can_manage: boolean;
  can_create_decisions: boolean;
  created_at: string;
  updated_at: string;
};

export type DecisionStatus =
  | "draft"
  | "framing"
  | "open_for_contribution"
  | "under_review"
  | "ready_for_decision"
  | "decision_finalised"
  | "commitment"
  | "implementation"
  | "outcome_review"
  | "lessons_learned"
  | "archived";

export type DecisionUrgency = "low" | "normal" | "high" | "critical";

export type DecisionTransitionAvailability = {
  from_status: DecisionStatus;
  to_status: DecisionStatus;
  enabled: boolean;
  blocked_reason: string;
  action: "transition" | "finalise" | "outcome_workflow";
};

export type DecisionSummary = {
  id: string;
  workspace_id: string;
  title: string;
  decision_question: string;
  status: DecisionStatus;
  status_label: string;
  urgency: DecisionUrgency;
  target_decision_date: string | null;
  owner: User;
  updated_at: string;
};

export type Decision = DecisionSummary & {
  organisation_id: string;
  purpose: string;
  context: string;
  scope: string;
  contribution_guidance: string;
  source_template_key: string;
  source_template_version: number | null;
  source_method_version_id?: string | null;
  contribution_deadline: string | null;
  status_changed_at: string;
  created_by: User;
  can_edit: boolean;
  can_transition: boolean;
  can_manage_participants: boolean;
  next_transition: DecisionTransitionAvailability | null;
  can_contribute_reasoning: boolean;
  reasoning_summary: ReasoningSummary;
  can_submit_position: boolean;
  can_finalise: boolean;
  position_summary: PositionSummary;
  created_at: string;
};

export type ParticipantRole =
  | "decision_owner"
  | "decision_maker"
  | "contributor"
  | "reviewer"
  | "observer";

export type Participant = {
  id: string;
  decision_id: string;
  user: User;
  role: ParticipantRole;
  role_label: string;
  status: "active" | "removed";
  created_at: string;
  updated_at: string;
};

export type DecisionTransition = {
  id: string;
  sequence: number;
  from_status: DecisionStatus;
  from_status_label: string;
  to_status: DecisionStatus;
  to_status_label: string;
  actor: User;
  rationale: string;
  warnings_acknowledged: string[];
  created_at: string;
};

export type ReasoningSummary = {
  active_options: number;
  active_evidence: number;
  active_assumptions: number;
  invalidated_assumptions: number;
  current_risks: number;
  active_criteria: number;
  ready_for_decision: boolean;
  blockers: string[];
};

export type OptionReversibility =
  | "easily_reversible"
  | "partially_reversible"
  | "difficult_to_reverse"
  | "irreversible";

export type DecisionOption = {
  id: string;
  decision_id: string;
  title: string;
  description: string;
  expected_benefits: string;
  tradeoffs: string;
  is_status_quo: boolean;
  estimated_cost: string | null;
  cost_notes: string;
  resource_notes: string;
  implementation_time_estimate: string;
  reversibility: OptionReversibility | "";
  reversibility_label: string;
  is_experiment: boolean;
  experiment_notes: string;
  depends_on_ids: string[];
  mutually_exclusive_with_ids: string[];
  status: "active" | "withdrawn";
  status_label: string;
  proposed_by: User;
  created_by: User;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type EvidenceSourceType =
  | "research"
  | "internal_data"
  | "expert_judgement"
  | "stakeholder_input"
  | "policy"
  | "other";

export type EvidenceItem = {
  id: string;
  decision_id: string;
  decision_title: string;
  option_id: string | null;
  source_id: string | null;
  title: string;
  summary: string;
  source_type: EvidenceSourceType;
  source_type_label: string;
  source_reference: string;
  source_url: string;
  stance: "supports" | "challenges" | "mixed" | "context";
  stance_label: string;
  strength: "low" | "moderate" | "high";
  strength_label: string;
  status: "active" | "withdrawn";
  status_label: string;
  created_by: User;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type Assumption = {
  id: string;
  decision_id: string;
  option_id: string | null;
  statement: string;
  rationale: string;
  impact_if_false: string;
  confidence: "low" | "medium" | "high";
  confidence_label: string;
  verification_status:
    | "unverified"
    | "partially_verified"
    | "verified"
    | "invalidated";
  verification_status_label: string;
  verification_notes: string;
  owner: User;
  review_date: string | null;
  status: "active" | "retired";
  status_label: string;
  created_by: User;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type Risk = {
  id: string;
  decision_id: string;
  option_id: string | null;
  title: string;
  description: string;
  likelihood: number;
  impact: number;
  score: number;
  response_strategy: "accept" | "avoid" | "mitigate" | "transfer" | "monitor";
  response_strategy_label: string;
  mitigation_plan: string;
  owner: User;
  review_date: string | null;
  status: "open" | "monitoring" | "mitigated" | "accepted" | "closed";
  status_label: string;
  created_by: User;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type Criterion = {
  id: string;
  decision_id: string;
  title: string;
  description: string;
  measurement_note: string;
  direction: "maximize" | "minimize";
  direction_label: string;
  weight: number;
  weight_rationale: string;
  is_must_have: boolean;
  threshold_note: string;
  owner: User;
  order: number;
  status: "active" | "retired";
  status_label: string;
  created_by: User;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type InvitationStatus = "pending" | "accepted" | "revoked" | "expired";

export type OrganisationInvitation = {
  id: string;
  organisation_id: string;
  email: string;
  role: OrganisationRole;
  role_label: string;
  status: InvitationStatus;
  invited_by: User;
  accepted_by: User | null;
  expires_at: string;
  accepted_at: string | null;
  revoked_at: string | null;
  last_sent_at: string | null;
  send_count: number;
  created_at: string;
  updated_at: string;
};

export type InvitationDispatch = {
  invitation: OrganisationInvitation;
  delivery: {
    status: "sent" | "failed";
    acceptance_url: string | null;
  };
};

export type InvitationPublicDetails = {
  organisation_id: string;
  organisation_name: string;
  email: string;
  role: OrganisationRole;
  role_label: string;
  status: InvitationStatus;
  expires_at: string;
  account_exists: boolean;
  current_user_email: string | null;
};

export type InvitationAcceptance = {
  user: User;
  membership: Membership;
  created_account: boolean;
};


export type PositionRecommendation =
  | "support"
  | "support_with_conditions"
  | "do_not_support_any"
  | "abstain";

export type StakeholderPosition = {
  id: string;
  decision_id: string;
  participant_id: string;
  participant_user: User;
  participant_role: ParticipantRole;
  participant_role_label: string;
  preferred_option_id: string | null;
  preferred_option_title: string | null;
  recommendation: PositionRecommendation;
  recommendation_label: string;
  rationale: string;
  conditions: string;
  confidence: "low" | "medium" | "high";
  confidence_label: string;
  version: number;
  created_at: string;
};

export type PositionSummary = {
  current_positions: number;
  required_authorities: number;
  submitted_authorities: number;
  missing_authorities: Array<{
    participant_id: string;
    email: string;
    role: ParticipantRole;
    role_label: string;
  }>;
  ready_to_finalise: boolean;
};

export type DecisionFinalisation = {
  id: string;
  decision_id: string;
  selected_option_id: string;
  selected_option_title: string;
  decided_by: User;
  rationale: string;
  conditions: string;
  dissent_summary: string;
  position_snapshot: Array<Record<string, unknown>>;
  decided_at: string;
  created_at: string;
};

export type AuditEvent = {
  id: string;
  action: string;
  object_type: string;
  object_id: string;
  actor: User | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type OutcomeAssessment =
  | "exceeded"
  | "met"
  | "partially_met"
  | "not_met"
  | "inconclusive";

export type DecisionReview = {
  id: string;
  decision_id: string;
  implementation_owner: User;
  commitment_statement: string;
  success_measures: string;
  review_due_date: string;
  commitment_rationale: string;
  commitment_recorded_by: User;
  commitment_recorded_at: string;
  implementation_plan: string;
  implementation_started_by: User | null;
  implementation_started_at: string | null;
  implementation_summary: string;
  outcome_summary: string;
  outcome_assessment: OutcomeAssessment | "";
  outcome_assessment_label: string;
  review_evidence: string;
  unintended_consequences: string;
  reviewed_by: User | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type LessonCategory =
  | "process"
  | "evidence"
  | "assumption"
  | "stakeholder"
  | "implementation"
  | "outcome"
  | "other";

export type Lesson = {
  id: string;
  decision_id: string;
  title: string;
  insight: string;
  category: LessonCategory;
  category_label: string;
  applicability: string;
  recommended_change: string;
  status: "active" | "retired";
  status_label: string;
  created_by: User;
  retired_by: User | null;
  created_at: string;
  updated_at: string;
};

export type SearchResult = {
  kind: string;
  object_id: string;
  decision_id: string;
  title: string;
  snippet: string;
  url: string;
  rank: number;
};

export type SearchResponse = {
  query: string;
  count: number;
  results: SearchResult[];
};

export type NotificationKind =
  | "assignment"
  | "lifecycle"
  | "review_due"
  | "ai_review"
  | "membership"
  | "collaboration"
  | "system";

export type Notification = {
  id: string;
  organisation_id: string;
  decision_id: string | null;
  kind: NotificationKind;
  kind_label: string;
  title: string;
  message: string;
  url: string;
  metadata: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type NotificationInbox = {
  unread_count: number;
  notifications: Notification[];
};

export type AIReviewFinding = {
  severity: "low" | "medium" | "high";
  title: string;
  detail: string;
  related_type: string;
  related_id: string;
};

export type SimilarDecision = {
  decision_id: string;
  title: string;
  status: DecisionStatus;
  similarity: number;
  url: string;
  reason: string;
};

export type AIReviewOutput = {
  summary: string;
  missing_evidence: AIReviewFinding[];
  unsupported_assumptions: AIReviewFinding[];
  contradictory_evidence: AIReviewFinding[];
  duplicate_evidence: AIReviewFinding[];
  missing_stakeholders: AIReviewFinding[];
  risk_highlights: AIReviewFinding[];
  review_triggers: AIReviewFinding[];
  similar_decisions: SimilarDecision[];
  limitations: string[];
};

export type AIReview = {
  id: string;
  decision_id: string;
  status: "pending" | "running" | "completed" | "failed";
  status_label: string;
  provider_key: string;
  provider_label: string;
  model_identifier: string;
  prompt_version: string;
  input_fingerprint: string;
  output: AIReviewOutput | Record<string, never>;
  error_message: string;
  requested_by: User;
  started_at: string | null;
  completed_at: string | null;
  is_reviewed: boolean;
  reviewed_by: User | null;
  reviewed_at: string | null;
  review_notes: string;
  is_dismissed: boolean;
  dismissed_by: User | null;
  dismissed_at: string | null;
  dismissal_reason: string;
  can_review: boolean;
  can_dismiss: boolean;
  created_at: string;
};

export type AIReviewList = {
  can_request: boolean;
  reviews: AIReview[];
};

export type AIReviewQualityMetrics = {
  total_completed: number;
  reviewed_count: number;
  dismissed_count: number;
  pending_disposition_count: number;
  correction_rate: number | null;
};

export type AnalyticsStatusCount = {
  status: DecisionStatus;
  label: string;
  count: number;
};

export type AnalyticsMonthlyTrendPoint = {
  month: string;
  label: string;
  created: number;
  finalised: number;
};

export type OrganisationAnalytics = {
  generated_at: string;
  totals: {
    decisions: number;
    open_decisions: number;
    finalised_decisions: number;
    archived_decisions: number;
    active_lessons: number;
  };
  flow: {
    status_counts: AnalyticsStatusCount[];
    created_last_90_days: number;
    finalised_last_90_days: number;
    monthly_trend: AnalyticsMonthlyTrendPoint[];
    median_days_to_finalise: number | null;
    overdue_target_decisions: number;
    contribution_coverage_percent: number | null;
  };
  learning: {
    outcome_reviews_completed: number;
    outcome_success_percent: number | null;
    outcome_assessment_counts: Array<{
      assessment: OutcomeAssessment;
      label: string;
      count: number;
    }>;
    reviews_due_or_overdue: number;
    active_lessons: number;
  };
  definitions: Record<string, string>;
};

export type AnalyticsObservation = {
  severity: "low" | "medium" | "high";
  title: string;
  detail: string;
};

export type AnalyticsInsight = {
  id: string;
  provider_key: string;
  provider_label: string;
  model_identifier: string;
  headline: string;
  observations: AnalyticsObservation[];
  requested_by: User;
  created_at: string;
};

export type DiscussionKind = "note" | "question" | "concern" | "update";

export type DiscussionEntry = {
  id: string;
  decision_id: string;
  author: User;
  kind: DiscussionKind;
  kind_label: string;
  body: string;
  reply_to_id: string | null;
  reply_to_summary: {
    id: string;
    author_email: string;
    kind: DiscussionKind;
    body_excerpt: string;
  } | null;
  mentioned_users: User[];
  is_resolved: boolean;
  resolved_at: string | null;
  resolved_by: User | null;
  resolution_note: string;
  can_resolve: boolean;
  created_at: string;
};

export type DiscussionResponse = {
  can_contribute: boolean;
  entries: DiscussionEntry[];
};

export type DecisionActivityItem = {
  id: string;
  source: "audit" | "discussion";
  action: string;
  title: string;
  actor: User | null;
  created_at: string;
  url: string;
  metadata: Record<string, unknown>;
};

export type PortfolioDecision = DecisionSummary & {
  organisation_id: string;
  organisation_name: string;
  workspace: { id: string; name: string };
  participant_role: ParticipantRole | null;
  unresolved_discussion_count: number;
  next_action: string;
  due_date: string | null;
  is_overdue: boolean;
};

export type PersonalWork = {
  unread_notifications: number;
  overdue_count: number;
  decision_count: number;
  decisions: PortfolioDecision[];
};

export type PortfolioWatchlist = {
  stalled_decisions: Array<{
    id: string;
    title: string;
    status: DecisionStatus;
    status_label: string;
    days_stalled: number;
  }>;
  open_high_risks: Array<{
    id: string;
    title: string;
    decision_id: string;
    decision_title: string;
    likelihood: number;
    impact: number;
  }>;
  assumptions_at_risk: Array<{
    id: string;
    statement: string;
    decision_id: string;
    decision_title: string;
    verification_status: string;
    verification_status_label: string;
  }>;
  triggered_signposts: Array<{
    id: string;
    signpost_id: string;
    signpost_title: string;
    scenario_set_id: string;
    canvas_id: string;
    assessment: string;
    assessment_label: string;
    observed_on: string;
  }>;
  benefits_realization: {
    exceeded: number;
    met: number;
    partially_met: number;
    not_met: number;
    inconclusive: number;
    total_reviewed: number;
  };
  risk_heatmap: {
    cells: Array<{
      likelihood: number;
      impact: number;
      count: number;
      risks: Array<{
        id: string;
        title: string;
        decision_id: string;
        decision_title: string;
      }>;
    }>;
    total_open_risks: number;
  };
};

export type OrganisationPortfolio = {
  organisation: Organisation;
  summary: {
    total: number;
    active: number;
    overdue: number;
    unresolved_discussion: number;
    status_counts: Partial<Record<DecisionStatus, number>>;
  };
  decisions: PortfolioDecision[];
  watchlist: PortfolioWatchlist;
};

export type DecisionTemplate = {
  key: string;
  name: string;
  summary: string;
  best_for: string;
  question_prompt: string;
  purpose_prompt: string;
  context_prompt: string;
  scope_prompt: string;
  contribution_prompt: string;
  suggested_urgency: DecisionUrgency;
  checklist: string[];
  version: number;
};

export type DecisionMethodVersion = {
  id: string;
  method_id: string;
  organisation_id: string;
  version: number;
  status: "draft" | "approved" | "retired";
  question_prompt: string;
  purpose_prompt: string;
  context_prompt: string;
  scope_prompt: string;
  contribution_prompt: string;
  suggested_urgency: DecisionUrgency;
  required_fields: string[];
  checklist: string[];
  evidence_prompts: string[];
  assumption_prompts: string[];
  risk_prompts: string[];
  stakeholder_prompts: string[];
  lifecycle_expectations: string[];
  approved_by_email: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DecisionMethod = {
  id: string;
  organisation_id: string;
  key: string;
  name: string;
  summary: string;
  best_for: string;
  status: "draft" | "approved" | "retired";
  current_version: DecisionMethodVersion | null;
  versions: DecisionMethodVersion[];
  retired_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DecisionMethodUsage = {
  id: string;
  method_name: string;
  method_version_number: number;
  decision_id: string;
  decision_title: string;
  applied_by_email: string;
  created_at: string;
};

export type MembershipEvent = {
  id: string;
  user: User;
  actor: User;
  kind: "created" | "role_changed" | "removed" | "ownership_transferred" | "status_changed";
  kind_label: string;
  previous_role: string;
  new_role: string;
  previous_status: string;
  new_status: string;
  note: string;
  created_at: string;
};

export type OrganisationDeletionRequest = {
  id: string;
  status: "pending" | "cancelled" | "completed";
  reason: string;
  earliest_deletion_at: string;
  requested_by: User;
  cancelled_by: User | null;
  cancelled_at: string | null;
  created_at: string;
};

export type DecisionOverview = {
  progress: { stage_index: number; stage_count: number; percent: number };
  next_action: { label: string; description: string; route: string };
  framing: { completed: number; total: number; missing: string[] };
  participants: {
    total: number;
    role_counts: Record<string, number>;
    people: Array<{
      id: string;
      name: string;
      email: string;
      role: ParticipantRole;
      role_label: string;
    }>;
  };
  discussion: { unresolved: number };
  options: Array<{
    id: string;
    title: string;
    is_status_quo: boolean;
    evidence_count: number;
    risk_count: number;
  }>;
  linked_signals: Array<{
    id: string;
    title: string;
    steep_category: string;
    time_horizon: string;
    maturity: string;
    priority_score: number;
    relevance: string;
  }>;
  foresight_implications: Array<{
    id: string;
    canvas_id: string;
    canvas_title: string;
    title: string;
    description: string;
    implication_type: string;
    priority: number;
    status: string;
    owner: string;
  }>;
  material_risks: Array<{
    id: string;
    title: string;
    score: number;
    status: string;
    owner: string;
  }>;
  reasoning: ReasoningSummary;
  target: { date: string | null; is_overdue: boolean };
};



export type ForesightFeed = {
  id: string;
  organisation_id: string;
  name: string;
  feed_url: string;
  owner: User;
  created_by: User;
  is_active: boolean;
  last_checked_at: string | null;
  last_success_at: string | null;
  last_error: string;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightSource = {
  id: string;
  organisation_id: string;
  feed_id: string | null;
  feed_name: string | null;
  external_id: string;
  title: string;
  source_type: "research" | "news" | "government" | "internal" | "expert" | "stakeholder" | "dataset" | "other";
  source_type_label: string;
  author: string;
  publisher: string;
  published_on: string | null;
  source_url: string;
  reference: string;
  credibility: "unassessed" | "low" | "moderate" | "high";
  credibility_label: string;
  credibility_rationale: string;
  notes: string;
  status: "active" | "superseded" | "withdrawn";
  status_label: string;
  supersedes_id: string | null;
  created_by: User;
  attachments: Array<{
    id: string;
    original_name: string;
    content_type: string;
    size_bytes: number;
    sha256: string;
    uploaded_by: User;
    created_at: string;
    download_url: string;
  }>;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightSignal = {
  id: string;
  organisation_id: string;
  source_id: string | null;
  source_title: string | null;
  title: string;
  summary: string;
  future_implication: string;
  steep_category: "social" | "technological" | "economic" | "environmental" | "political" | "legal" | "ethical";
  steep_label: string;
  time_horizon: "near" | "medium" | "long";
  horizon_label: string;
  maturity: "weak" | "emerging" | "established";
  maturity_label: string;
  polarity: "opportunity" | "threat" | "both" | "unclear";
  polarity_label: string;
  geography: string;
  domain: string;
  impact: number;
  uncertainty: number;
  priority_score: number;
  status: "draft" | "reviewed" | "monitoring" | "retired";
  status_label: string;
  owner: User;
  created_by: User;
  last_reviewed_at: string | null;
  linked_decisions: Array<{ id: string; title: string; relevance: string }>;
  watchlists: Array<{ id: string; name: string }>;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightWatchlist = {
  id: string;
  organisation_id: string;
  name: string;
  description: string;
  owner: User;
  created_by: User;
  is_active: boolean;
  signal_count: number;
  signals: Array<{
    id: string;
    title: string;
    steep_category: string;
    time_horizon: string;
    priority_score: number;
  }>;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightOverview = {
  signal_count: number;
  source_count: number;
  watchlist_count: number;
  canvas_count: number;
  high_attention_count: number;
  by_steep: Partial<Record<ForesightSignal["steep_category"], number>>;
  by_horizon: Partial<Record<ForesightSignal["time_horizon"], number>>;
  can_contribute: boolean;
};

export type ForesightCanvas = {
  id: string;
  organisation_id: string;
  title: string;
  focal_question: string;
  scope: string;
  horizon_year: number;
  owner: User;
  created_by: User;
  status: "draft" | "active" | "complete" | "archived";
  status_label: string;
  driver_count: number;
  implication_count: number;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightDriver = {
  id: string;
  canvas_id: string;
  title: string;
  description: string;
  driver_type: "trend" | "driver" | "critical_uncertainty" | "predetermined" | "wild_card";
  driver_type_label: string;
  steep_category: ForesightSignal["steep_category"];
  steep_label: string;
  direction: "increasing" | "decreasing" | "stable" | "volatile" | "unclear";
  direction_label: string;
  impact: number;
  uncertainty: number;
  attention_score: number;
  owner: User;
  created_by: User;
  is_active: boolean;
  linked_signals: Array<{ id: string; title: string; rationale: string }>;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightStakeholder = {
  id: string;
  canvas_id: string;
  name: string;
  stakeholder_type: "internal" | "customer" | "partner" | "regulator" | "community" | "competitor" | "other";
  stakeholder_type_label: string;
  role: string;
  interests: string;
  influence: number;
  exposure: number;
  stance: "supportive" | "neutral" | "resistant" | "mixed" | "unclear";
  stance_label: string;
  created_by: User;
  created_at: string;
  updated_at: string;
};

export type ForesightRelationship = {
  id: string;
  canvas_id: string;
  source_driver_id: string;
  source_title: string;
  target_driver_id: string;
  target_title: string;
  polarity: "reinforcing" | "balancing" | "uncertain";
  polarity_label: string;
  strength: number;
  delay: "immediate" | "short" | "medium" | "long" | "unknown";
  delay_label: string;
  rationale: string;
  created_by: User;
  created_at: string;
  updated_at: string;
};

export type ForesightFeedbackLoop = {
  id: string;
  canvas_id: string;
  name: string;
  description: string;
  loop_type: "reinforcing" | "balancing" | "mixed" | "uncertain";
  loop_type_label: string;
  drivers: Array<{ id: string; title: string }>;
  rationale: string;
  created_by: User;
  created_at: string;
  updated_at: string;
};

export type ForesightConsequence = {
  id: string;
  canvas_id: string;
  originating_driver_id: string | null;
  originating_driver_title: string | null;
  parent_id: string | null;
  parent_title: string | null;
  title: string;
  description: string;
  order: 1 | 2 | 3;
  consequence_type: "opportunity" | "threat" | "mixed" | "unclear";
  consequence_type_label: string;
  likelihood: number;
  impact: number;
  created_by: User;
  created_at: string;
  updated_at: string;
};

export type ThreeHorizonItem = {
  id: string;
  canvas_id: string;
  horizon: "h1" | "h2" | "h3";
  horizon_label: string;
  title: string;
  description: string;
  evidence: string;
  created_by: User;
  created_at: string;
  updated_at: string;
};

export type StrategicImplication = {
  id: string;
  canvas_id: string;
  title: string;
  description: string;
  implication_type: "opportunity" | "threat" | "capability" | "decision_requirement" | "policy";
  implication_type_label: string;
  priority: number;
  owner: User;
  linked_decision_id: string | null;
  linked_decision_title: string | null;
  drivers: Array<{ id: string; title: string }>;
  status: "open" | "addressed" | "dismissed";
  status_label: string;
  created_by: User;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightCanvasWorkspace = ForesightCanvas & {
  drivers: ForesightDriver[];
  stakeholders: ForesightStakeholder[];
  relationships: ForesightRelationship[];
  feedback_loops: ForesightFeedbackLoop[];
  consequences: ForesightConsequence[];
  horizon_items: ThreeHorizonItem[];
  implications: StrategicImplication[];
  scenario_sets: ForesightScenarioSet[];
  summary: {
    driver_count: number;
    critical_uncertainty_count: number;
    high_attention_count: number;
    stakeholder_count: number;
    relationship_count: number;
    feedback_loop_count: number;
    scenario_set_count: number;
    open_implication_count: number;
  };
};

export type ForesightScenarioSet = {
  id: string;
  canvas_id: string;
  title: string;
  purpose: string;
  axis_x_driver_id: string;
  axis_x_driver_title: string;
  axis_x_low_label: string;
  axis_x_high_label: string;
  axis_y_driver_id: string;
  axis_y_driver_title: string;
  axis_y_low_label: string;
  axis_y_high_label: string;
  linked_decision_id: string | null;
  linked_decision_title: string | null;
  owner: User;
  created_by: User;
  status: "draft" | "active" | "complete" | "archived";
  status_label: string;
  scenario_count: number;
  signpost_count: number;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightScenarioDriverState = {
  id: string;
  scenario_id: string;
  driver_id: string;
  driver_title: string;
  state: "strengthening" | "weakening" | "stable" | "volatile" | "transformed" | "uncertain";
  state_label: string;
  salience: number;
  description: string;
  created_by: User;
  created_at: string;
  updated_at: string;
};

export type ForesightScenarioReview = {
  id: string;
  scenario_id: string;
  reviewer: User;
  plausibility: number;
  internal_consistency: number;
  distinctiveness: number;
  usefulness: number;
  confidence: number;
  comment: string;
  created_at: string;
  updated_at: string;
};

export type ForesightWindTunnelAssessment = {
  id: string;
  scenario_id: string;
  option_id: string;
  option_title: string;
  decision_id: string;
  decision_title: string;
  verdict: "robust" | "adaptable" | "vulnerable" | "infeasible" | "uncertain";
  verdict_label: string;
  desirability: number;
  feasibility: number;
  resilience: number;
  robustness_score: number;
  rationale: string;
  conditions_for_success: string;
  vulnerabilities: string;
  mitigations: string;
  assessed_by: User;
  created_at: string;
  updated_at: string;
};

export type ForesightScenarioImplicationLink = {
  id: string;
  scenario_id: string;
  implication_id: string;
  implication_title: string;
  implication_type: string;
  effect: "amplifies" | "reduces" | "changes" | "triggers";
  effect_label: string;
  rationale: string;
  linked_by: User;
  created_at: string;
  updated_at: string;
};

export type ForesightScenario = {
  id: string;
  scenario_set_id: string;
  title: string;
  code: string;
  axis_x_position: "low" | "high";
  axis_x_position_label: string;
  axis_y_position: "low" | "high";
  axis_y_position_label: string;
  headline: string;
  narrative: string;
  key_assumptions: string;
  opportunities: string;
  threats: string;
  status: "draft" | "reviewed";
  status_label: string;
  created_by: User;
  driver_states: ForesightScenarioDriverState[];
  reviews: ForesightScenarioReview[];
  review_summary: {
    review_count: number;
    plausibility: number | null;
    internal_consistency: number | null;
    distinctiveness: number | null;
    usefulness: number | null;
    confidence: number | null;
    confidence_range: number | null;
  };
  wind_tunnel_assessments: ForesightWindTunnelAssessment[];
  implication_links: ForesightScenarioImplicationLink[];
  signpost_links: Array<{
    id: string;
    signpost_id: string;
    signpost_title: string;
    relationship: string;
    relationship_label: string;
    rationale: string;
  }>;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ForesightSignpostObservation = {
  id: string;
  signpost_id: string;
  observed_on: string;
  value: string;
  assessment: "no_change" | "weak" | "moderate" | "strong" | "contradictory";
  assessment_label: string;
  evidence: string;
  source_id: string | null;
  source_title: string | null;
  created_by: User;
  created_at: string;
  updated_at: string;
};

export type ForesightSignpost = {
  id: string;
  scenario_set_id: string;
  title: string;
  description: string;
  indicator: string;
  threshold: string;
  direction: "above" | "below" | "rising" | "falling" | "change" | "qualitative";
  direction_label: string;
  review_cadence: "monthly" | "quarterly" | "semiannual" | "annual" | "event_driven";
  review_cadence_label: string;
  source_notes: string;
  owner: User;
  created_by: User;
  status: "active" | "paused" | "retired";
  status_label: string;
  scenario_links: Array<{
    id: string;
    scenario_id: string;
    scenario_title: string;
    relationship: "supports" | "contradicts" | "contextual";
    relationship_label: string;
    rationale: string;
  }>;
  observations: ForesightSignpostObservation[];
  latest_observation: {
    id: string;
    observed_on: string;
    value: string;
    assessment: string;
    assessment_label: string;
  } | null;
  assumption_links: Array<{
    id: string;
    assumption_id: string;
    assumption_statement: string;
    rationale: string;
  }>;
  risk_links: Array<{
    id: string;
    risk_id: string;
    risk_title: string;
    rationale: string;
  }>;
  created_at: string;
  updated_at: string;
};

export type ForesightScenarioSetWorkspace = ForesightScenarioSet & {
  scenarios: ForesightScenario[];
  signposts: ForesightSignpost[];
  decision_options: Array<{
    id: string;
    title: string;
    description: string;
    status: string;
    is_status_quo: boolean;
  }>;
  summary: {
    scenario_count: number;
    review_count: number;
    assessment_count: number;
    robust_assessment_count: number;
    active_signpost_count: number;
    observation_count: number;
  };
};

export type EvaluationMethod = "scorecard" | "approval" | "consent" | "delphi";
export type EvaluationAnonymity = "attributed" | "peer_anonymous";

export type EvaluationCriterion = {
  id: string;
  exercise_id: string;
  title: string;
  description: string;
  weight: string;
  scale_min: number;
  scale_max: number;
  higher_is_better: boolean;
  order: number;
  created_at: string;
  updated_at: string;
};

export type EvaluationResponseRecord = {
  id: string;
  option_id: string;
  option_title: string;
  criterion_id: string | null;
  criterion_title: string | null;
  score: string | null;
  vote: "approve" | "consent" | "concern" | "object" | "abstain" | "";
  rationale: string;
  created_at: string;
};

export type EvaluationSubmission = {
  id: string;
  round_id: string;
  respondent: { anonymous: true; label: string } | { anonymous: false; user: User };
  status: "draft" | "submitted";
  confidence: number;
  overall_rationale: string;
  submitted_at: string | null;
  responses: EvaluationResponseRecord[];
  created_at: string;
  updated_at: string;
};

export type EvaluationOptionResult = {
  option_id: string;
  title: string;
  weighted_score?: number | null;
  confidence?: number | null;
  score_stdev?: number | null;
  score_min?: number | null;
  score_max?: number | null;
  disagreement?: "low" | "moderate" | "high" | "insufficient_data";
  criteria?: Array<{
    criterion_id: string;
    title: string;
    mean_score: number | null;
    normalised_score: number | null;
    response_count: number;
  }>;
  vote_count?: number;
  approval_rate?: number;
  objection_rate?: number;
  dissent_rate?: number;
  passes_threshold?: boolean;
  breakdown?: Record<string, number>;
};

export type EvaluationResults = {
  hidden: boolean;
  round_id: string;
  submission_count: number;
  eligible_count: number;
  quorum_count: number;
  quorum_met: boolean;
  method: EvaluationMethod;
  options: EvaluationOptionResult[];
  criterion_sensitivity: Array<{
    option_id: string;
    base_rank: number;
    best_rank: number;
    worst_rank: number;
    stable: boolean;
  }>;
  tornado: {
    option_id: string;
    option_title: string;
    base_score: number | null;
    criteria: Array<{
      criterion_id: string;
      title: string;
      score_low: number | null;
      score_high: number | null;
      impact: number | null;
    }>;
  } | null;
  uncertainty_narrative: string;
};

export type EvaluationRound = {
  id: string;
  exercise_id: string;
  number: number;
  title: string;
  status: "draft" | "open" | "closed";
  feedback_summary: string;
  opens_at: string | null;
  closes_at: string | null;
  submissions: EvaluationSubmission[];
  result_summary: EvaluationResults;
  created_at: string;
  updated_at: string;
};

export type MinorityReport = {
  id: string;
  exercise_id: string;
  round_id: string | null;
  author: User;
  title: string;
  analysis: string;
  recommendation: string;
  status: "draft" | "published";
  published_at: string;
  created_at: string;
  updated_at: string;
};

export type EvaluationExercise = {
  id: string;
  organisation_id: string;
  decision_id: string;
  title: string;
  purpose: string;
  method: EvaluationMethod;
  method_label: string;
  status: "draft" | "open" | "closed" | "archived";
  status_label: string;
  anonymity: EvaluationAnonymity;
  blind_results_until_close: boolean;
  quorum_count: number;
  approval_threshold: string;
  objection_threshold: string;
  owner: User;
  created_by: User;
  criteria: EvaluationCriterion[];
  rounds: EvaluationRound[];
  minority_reports: MinorityReport[];
  can_manage: boolean;
  can_submit: boolean;
  created_at: string;
  updated_at: string;
};

export type PortfolioCriterion = {
  id: string;
  portfolio_id: string;
  title: string;
  description: string;
  weight: string;
  higher_is_better: boolean;
  order: number;
  created_at: string;
  updated_at: string;
};

export type PortfolioAssessment = {
  id: string;
  candidate_id: string;
  criterion_id: string;
  criterion_title: string;
  respondent: { anonymous: true; label: string } | { anonymous: false; user: User };
  score: string;
  confidence: number;
  rationale: string;
  created_at: string;
  updated_at: string;
};

export type PortfolioSelection = {
  id: string;
  candidate_id: string;
  selected: boolean;
  priority_order: number | null;
  approved_budget: string | null;
  approved_capacity: string | null;
  rationale: string;
  selected_by: User;
  selected_at: string;
  created_at: string;
  updated_at: string;
};

export type PortfolioCandidate = {
  id: string;
  portfolio_id: string;
  decision_id: string;
  decision_title: string;
  decision_status: DecisionStatus;
  budget_required: string;
  capacity_required: string;
  mandatory: boolean;
  rationale: string;
  status: "active" | "withdrawn";
  assessments: PortfolioAssessment[];
  selection?: PortfolioSelection;
  created_at: string;
  updated_at: string;
};

export type PrioritisationRecommendation = {
  hidden: boolean;
  portfolio_id: string;
  budget_limit: number | null;
  capacity_limit: number | null;
  recommended_budget: number;
  recommended_capacity: number;
  candidates: Array<{
    candidate_id: string;
    decision_id: string;
    title: string;
    score: number;
    assessor_count: number;
    confidence: number | null;
    budget_required: number;
    capacity_required: number;
    mandatory: boolean;
    recommended: boolean;
    constraint_reason: string;
  }>;
  warning: string;
};

export type PrioritisationPortfolio = {
  id: string;
  organisation_id: string;
  title: string;
  purpose: string;
  budget_limit: string | null;
  capacity_limit: string | null;
  status: "draft" | "open" | "closed" | "archived";
  anonymity: "attributed" | "peer_anonymous";
  blind_results_until_close: boolean;
  owner: User;
  created_by: User;
  criteria: PortfolioCriterion[];
  candidates: PortfolioCandidate[];
  recommendation: PrioritisationRecommendation;
  can_manage: boolean;
  can_assess: boolean;
  created_at: string;
  updated_at: string;
};

export type DecisionAnalysisWorkspace = {
  decision: { id: string; title: string; question: string; status: DecisionStatus; status_label: string };
  options: Array<{
    id: string;
    title: string;
    description: string;
    expected_benefits: string;
    tradeoffs: string;
    is_status_quo: boolean;
    evidence: { supporting: number; challenging: number; mixed: number; context: number; high_strength: number; structured_sources: number; high_credibility_sources: number; unassessed_sources: number; superseded_sources: number; withdrawn_sources: number; dated_sources: number };
    assumptions: { total: number; unverified: number; invalidated: number; low_confidence: number; overdue_review: number };
    risks: { total: number; exposure: number; highest_score: number; without_mitigation: number; overdue_review: number };
    stakeholders: { support: number; conditional: number; high_confidence: number };
    scenarios: { assessment_count: number; average_robustness: number | null; minimum_robustness: number | null; vulnerability_count: number; mitigation_count: number };
    evaluations: Array<{ exercise_id: string; exercise_title: string; method: EvaluationMethod; weighted_score?: number | null; approval_rate?: number | null; objection_rate?: number | null; passes_threshold?: boolean | null; confidence?: number | null }>;
    issues: { open: number; critical: number };
  }>;
  cross_cutting: { evidence: number; assumptions: number; risks: number; open_issues: number; do_not_support_any: number; abstentions: number };
  foresight: {
    linked_signals: Array<{ id: string; title: string; relevance: string; priority_score: number; time_horizon: string }>;
    implications: Array<{ id: string; canvas_id: string; canvas_title: string; title: string; type: string; priority: number; status: string }>;
  };
  quality_review: null | { id: string; version: number; status: string; judgement: string; blockers: string; conditions: string; published_at: string | null };
  executive_summary: null | { id: string; version: number; status: string; proposed_judgement: string; approved_at: string | null };
  minority_reports: Array<{ id: string; exercise_id: string; exercise_title: string; title: string; analysis: string; recommendation: string; published_at: string }>;
  issue_summary: { total: number; open: number; critical: number };
  capabilities: { can_manage: boolean; can_contribute: boolean };
  principle: string;
};

export type DecisionAnalysisIssue = {
  id: string;
  decision_id: string;
  option_id: string | null;
  evidence_id: string | null;
  assumption_id: string | null;
  risk_id: string | null;
  evaluation_exercise_id: string | null;
  scenario_set_id: string | null;
  issue_type: string;
  issue_type_label: string;
  title: string;
  description: string;
  severity: "low" | "moderate" | "high" | "critical";
  severity_label: string;
  status: "open" | "in_progress" | "resolved" | "dismissed";
  status_label: string;
  owner: User;
  due_date: string | null;
  resolution: string;
  resolved_at: string | null;
  resolved_by: User | null;
  created_by: User;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type DecisionQualityReview = {
  id: string;
  decision_id: string;
  version: number;
  status: "draft" | "published" | "superseded";
  status_label: string;
  judgement: "not_ready" | "ready_with_conditions" | "ready";
  judgement_label: string;
  answers: Record<string, "yes" | "partly" | "no" | "not_applicable">;
  strengths: string;
  blockers: string;
  conditions: string;
  author: User;
  published_at: string | null;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ExecutiveDecisionSummary = {
  id: string;
  decision_id: string;
  version: number;
  status: "draft" | "approved" | "superseded";
  status_label: string;
  context_summary: string;
  options_summary: string;
  evidence_summary: string;
  uncertainty_summary: string;
  stakeholder_summary: string;
  scenario_summary: string;
  evaluation_summary: string;
  risk_summary: string;
  unresolved_issues: string;
  proposed_judgement: string;
  conditions: string;
  implementation_implications: string;
  created_by: User;
  approved_by: User | null;
  approved_at: string | null;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ContributionRequestStatus =
  | "draft"
  | "open"
  | "in_progress"
  | "submitted"
  | "under_review"
  | "accepted"
  | "returned"
  | "cancelled";

export type ContributionSubmission = {
  id: string;
  request_id: string;
  author: User;
  sequence: number;
  body: string;
  references: string;
  status: "draft" | "submitted";
  status_label: string;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ContributionReview = {
  id: string;
  request_id: string;
  submission_id: string;
  reviewer: User;
  outcome: "accepted" | "returned" | "comment";
  outcome_label: string;
  note: string;
  created_at: string;
};

export type ContributionRequest = {
  id: string;
  organisation_id: string;
  organisation_name: string;
  decision_id: string;
  decision_title: string;
  option_id: string | null;
  session_id: string | null;
  session_title: string | null;
  requested_by: User;
  assignee: User;
  reviewer: User | null;
  kind: string;
  kind_label: string;
  title: string;
  instructions: string;
  priority: "low" | "normal" | "high" | "critical";
  priority_label: string;
  status: ContributionRequestStatus;
  status_label: string;
  due_at: string | null;
  opened_at: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  submissions: ContributionSubmission[];
  reviews: ContributionReview[];
  can_work: boolean;
  can_review: boolean;
  can_manage: boolean;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
};

export type ContributionParticipationSummary = {
  participant_count: number;
  assigned_count: number;
  submitted_count: number;
  coverage_percent: number;
  unassigned_participants: { id: string; email: string; role: string }[];
  role_counts: Record<string, number>;
};

export type DecisionContributionWorkspace = {
  can_manage: boolean;
  participation: ContributionParticipationSummary;
  requests: ContributionRequest[];
};

export type FacilitationSessionParticipant = {
  id: string;
  user: User;
  role: "participant" | "observer";
  role_label: string;
  attendance: "invited" | "attended" | "absent";
  attendance_label: string;
  created_at: string;
  updated_at: string;
};

export type FacilitationSession = {
  id: string;
  decision_id: string;
  title: string;
  objective: string;
  agenda: string;
  participation_guidance: string;
  facilitator: User;
  starts_at: string | null;
  ends_at: string | null;
  status: "planned" | "open" | "closed" | "cancelled";
  status_label: string;
  participants: FacilitationSessionParticipant[];
  can_manage: boolean;
  closed_at: string | null;
  created_by: User;
  created_at: string;
  updated_at: string;
};

export type PersonalContributionWork = {
  summary: { total: number; overdue: number; returned: number; submitted: number; awaiting_review: number };
  requests: ContributionRequest[];
};

export type ContributionPreference = {
  id: string;
  organisation_id: string;
  digest_cadence: "immediate" | "daily" | "weekly" | "none";
  email_enabled: boolean;
  due_reminders_enabled: boolean;
  reminder_days_before: number;
  last_digest_at: string | null;
  created_at: string;
  updated_at: string;
};

export type IdeaStatus = "submitted" | "shortlisted" | "promoted" | "archived";
export type OpenSessionStatus = "draft" | "open" | "closed" | "archived";

export type Idea = {
  id: string;
  title: string;
  description: string;
  status: IdeaStatus;
  status_label: string;
  submitted_by_participant: { name: string } | null;
  submitted_by_user: User | null;
  vote_count: number;
  voted_by_me: boolean;
  created_at: string;
};

export type OpenSessionPublic = {
  id: string;
  organisation_name: string;
  title: string;
  prompt: string;
  description: string;
  status: OpenSessionStatus;
  status_label: string;
  voting_enabled: boolean;
  submission_deadline: string | null;
  ideas: Idea[];
};

export type OpenSessionSummary = {
  id: string;
  title: string;
  prompt: string;
  status: OpenSessionStatus;
  status_label: string;
  public_slug: string;
  decision_id: string | null;
  decision_title: string | null;
  voting_enabled: boolean;
  idea_count: number;
  created_by: User;
  created_at: string;
};

export type OpenSessionOrganiser = OpenSessionSummary & {
  description: string;
  ideas: Idea[];
};
