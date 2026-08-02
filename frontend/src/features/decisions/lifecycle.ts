import type { DecisionStatus } from "../../lib/types";

export const decisionLifecycle: Array<{ status: DecisionStatus; label: string }> = [
  { status: "draft", label: "Draft" },
  { status: "framing", label: "Framing" },
  { status: "open_for_contribution", label: "Open for Contribution" },
  { status: "under_review", label: "Under Review" },
  { status: "ready_for_decision", label: "Ready for Decision" },
  { status: "decision_finalised", label: "Decision Finalised" },
  { status: "commitment", label: "Commitment" },
  { status: "implementation", label: "Implementation" },
  { status: "outcome_review", label: "Outcome Review" },
  { status: "lessons_learned", label: "Lessons Learned" },
  { status: "archived", label: "Archived" },
];

export function statusLabel(status: DecisionStatus): string {
  return decisionLifecycle.find((item) => item.status === status)?.label ?? status;
}
