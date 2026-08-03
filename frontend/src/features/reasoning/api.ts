import { apiRequest } from "../../lib/api";
import type {
  Assumption,
  Criterion,
  DecisionOption,
  EvidenceItem,
  EvidenceSourceType,
  Risk,
} from "../../lib/types";

export type DecisionOptionInput = {
  title: string;
  description: string;
  expected_benefits?: string;
  tradeoffs?: string;
  is_status_quo?: boolean;
};

export function listOptions(decisionId: string): Promise<DecisionOption[]> {
  return apiRequest<DecisionOption[]>(`/decisions/${decisionId}/options/`);
}

export function createOption(
  decisionId: string,
  input: DecisionOptionInput,
): Promise<DecisionOption> {
  return apiRequest<DecisionOption>(`/decisions/${decisionId}/options/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateOption(
  optionId: string,
  input: Partial<DecisionOptionInput> & { status?: "active" | "withdrawn" },
): Promise<DecisionOption> {
  return apiRequest<DecisionOption>(`/decision-options/${optionId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export type EvidenceInput = {
  source_id?: string | null;
  option_id?: string | null;
  title: string;
  summary: string;
  source_type: EvidenceSourceType;
  source_reference?: string;
  source_url?: string;
  stance: "supports" | "challenges" | "mixed" | "context";
  strength: "low" | "moderate" | "high";
};

export function listEvidence(decisionId: string): Promise<EvidenceItem[]> {
  return apiRequest<EvidenceItem[]>(`/decisions/${decisionId}/evidence/`);
}

export function createEvidence(
  decisionId: string,
  input: EvidenceInput,
): Promise<EvidenceItem> {
  return apiRequest<EvidenceItem>(`/decisions/${decisionId}/evidence/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateEvidence(
  evidenceId: string,
  input: Partial<EvidenceInput> & { status?: "active" | "withdrawn" },
): Promise<EvidenceItem> {
  return apiRequest<EvidenceItem>(`/evidence/${evidenceId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export type AssumptionInput = {
  option_id?: string | null;
  statement: string;
  rationale?: string;
  impact_if_false: string;
  confidence: "low" | "medium" | "high";
  verification_status?:
    | "unverified"
    | "partially_verified"
    | "verified"
    | "invalidated";
  verification_notes?: string;
  owner_id?: string;
  review_date?: string | null;
};

export function listAssumptions(decisionId: string): Promise<Assumption[]> {
  return apiRequest<Assumption[]>(`/decisions/${decisionId}/assumptions/`);
}

export function createAssumption(
  decisionId: string,
  input: AssumptionInput,
): Promise<Assumption> {
  return apiRequest<Assumption>(`/decisions/${decisionId}/assumptions/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateAssumption(
  assumptionId: string,
  input: Partial<AssumptionInput> & { status?: "active" | "retired" },
): Promise<Assumption> {
  return apiRequest<Assumption>(`/assumptions/${assumptionId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export type RiskInput = {
  option_id?: string | null;
  title: string;
  description: string;
  likelihood: number;
  impact: number;
  response_strategy: "accept" | "avoid" | "mitigate" | "transfer" | "monitor";
  mitigation_plan?: string;
  owner_id?: string;
  review_date?: string | null;
};

export function listRisks(decisionId: string): Promise<Risk[]> {
  return apiRequest<Risk[]>(`/decisions/${decisionId}/risks/`);
}

export function createRisk(decisionId: string, input: RiskInput): Promise<Risk> {
  return apiRequest<Risk>(`/decisions/${decisionId}/risks/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateRisk(
  riskId: string,
  input: Partial<RiskInput> & {
    status?: "open" | "monitoring" | "mitigated" | "accepted" | "closed";
  },
): Promise<Risk> {
  return apiRequest<Risk>(`/risks/${riskId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export type CriterionInput = {
  title: string;
  description: string;
  measurement_note?: string;
  direction: "maximize" | "minimize";
  weight: number;
  weight_rationale?: string;
  is_must_have?: boolean;
  threshold_note?: string;
  owner_id?: string;
  order?: number;
};

export function listCriteria(decisionId: string): Promise<Criterion[]> {
  return apiRequest<Criterion[]>(`/decisions/${decisionId}/criteria/`);
}

export function createCriterion(
  decisionId: string,
  input: CriterionInput,
): Promise<Criterion> {
  return apiRequest<Criterion>(`/decisions/${decisionId}/criteria/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateCriterion(
  criterionId: string,
  input: Partial<CriterionInput> & { status?: "active" | "retired" },
): Promise<Criterion> {
  return apiRequest<Criterion>(`/criteria/${criterionId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}
