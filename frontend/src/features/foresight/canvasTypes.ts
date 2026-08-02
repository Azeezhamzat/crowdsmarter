export const STEEP_CATEGORIES = [
  "social",
  "technological",
  "economic",
  "environmental",
  "political",
  "legal",
  "ethical",
] as const;

export type CanvasTab =
  | "overview"
  | "drivers"
  | "system"
  | "wheel"
  | "horizons"
  | "scenarios"
  | "implications";

export type DriverForm = {
  title: string;
  description: string;
  driver_type: string;
  steep_category: string;
  direction: string;
  impact: number;
  uncertainty: number;
  owner_id: string;
};

export type StakeholderForm = {
  name: string;
  stakeholder_type: string;
  role: string;
  interests: string;
  influence: number;
  exposure: number;
  stance: string;
};

export type RelationshipForm = {
  source_driver_id: string;
  target_driver_id: string;
  polarity: string;
  strength: number;
  delay: string;
  rationale: string;
};

export type FeedbackLoopForm = {
  name: string;
  description: string;
  loop_type: string;
  driver_ids: string[];
  rationale: string;
};

export type ConsequenceForm = {
  originating_driver_id: string;
  parent_id: string;
  title: string;
  description: string;
  consequence_type: string;
  likelihood: number;
  impact: number;
};

export type HorizonForm = {
  horizon: string;
  title: string;
  description: string;
  evidence: string;
};

export type ImplicationForm = {
  title: string;
  description: string;
  implication_type: string;
  priority: number;
  owner_id: string;
  linked_decision_id: string;
  driver_ids: string[];
};

export type SignalLinkForm = Record<
  string,
  { signalId: string; rationale: string }
>;

export type CanvasSettingsForm = {
  title: string;
  focal_question: string;
  scope: string;
  horizon_year: number;
  owner_id: string;
  status: string;
};

export const EMPTY_DRIVER: DriverForm = {
  title: "",
  description: "",
  driver_type: "driver",
  steep_category: "technological",
  direction: "unclear",
  impact: 3,
  uncertainty: 3,
  owner_id: "",
};

export const EMPTY_STAKEHOLDER: StakeholderForm = {
  name: "",
  stakeholder_type: "internal",
  role: "",
  interests: "",
  influence: 3,
  exposure: 3,
  stance: "unclear",
};

export const EMPTY_RELATIONSHIP: RelationshipForm = {
  source_driver_id: "",
  target_driver_id: "",
  polarity: "reinforcing",
  strength: 3,
  delay: "unknown",
  rationale: "",
};

export const EMPTY_FEEDBACK_LOOP: FeedbackLoopForm = {
  name: "",
  description: "",
  loop_type: "reinforcing",
  driver_ids: [],
  rationale: "",
};

export const EMPTY_CONSEQUENCE: ConsequenceForm = {
  originating_driver_id: "",
  parent_id: "",
  title: "",
  description: "",
  consequence_type: "unclear",
  likelihood: 3,
  impact: 3,
};

export const EMPTY_HORIZON: HorizonForm = {
  horizon: "h1",
  title: "",
  description: "",
  evidence: "",
};

export const EMPTY_IMPLICATION: ImplicationForm = {
  title: "",
  description: "",
  implication_type: "opportunity",
  priority: 3,
  owner_id: "",
  linked_decision_id: "",
  driver_ids: [],
};

export function personName(user: {
  first_name: string;
  last_name: string;
  email: string;
}): string {
  return [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email;
}

export function scoreLabel(score: number): string {
  if (score >= 20) return "Very high";
  if (score >= 16) return "High";
  if (score >= 9) return "Moderate";
  return "Lower";
}
