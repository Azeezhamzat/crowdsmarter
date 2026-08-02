import { apiRequest } from "../../lib/api";
import type {
  DecisionFinalisation,
  DecisionStatus,
  PositionRecommendation,
  StakeholderPosition,
} from "../../lib/types";

export type PositionInput = {
  preferred_option_id?: string | null;
  recommendation: PositionRecommendation;
  rationale: string;
  conditions?: string;
  confidence: "low" | "medium" | "high";
};

export function listCurrentPositions(
  decisionId: string,
): Promise<StakeholderPosition[]> {
  return apiRequest<StakeholderPosition[]>(`/decisions/${decisionId}/positions/`);
}

export function listPositionHistory(
  decisionId: string,
): Promise<StakeholderPosition[]> {
  return apiRequest<StakeholderPosition[]>(
    `/decisions/${decisionId}/positions/history/`,
  );
}

export function submitPosition(
  decisionId: string,
  input: PositionInput,
): Promise<StakeholderPosition> {
  return apiRequest<StakeholderPosition>(`/decisions/${decisionId}/positions/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getFinalisation(
  decisionId: string,
): Promise<{ finalisation: DecisionFinalisation | null }> {
  return apiRequest<{ finalisation: DecisionFinalisation | null }>(
    `/decisions/${decisionId}/finalisation/`,
  );
}

export function finaliseDecision(
  decisionId: string,
  input: {
    expected_status: DecisionStatus;
    selected_option_id: string;
    rationale: string;
    conditions?: string;
    dissent_summary?: string;
    positions_reviewed: boolean;
  },
): Promise<DecisionFinalisation> {
  return apiRequest<DecisionFinalisation>(`/decisions/${decisionId}/finalisation/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
