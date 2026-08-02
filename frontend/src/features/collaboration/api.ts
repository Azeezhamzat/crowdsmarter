import { apiRequest } from "../../lib/api";
import type {
  DecisionActivityItem,
  DiscussionEntry,
  DiscussionKind,
  DiscussionResponse,
} from "../../lib/types";

export function listDiscussion(decisionId: string): Promise<DiscussionResponse> {
  return apiRequest<DiscussionResponse>(`/decisions/${decisionId}/discussion/`);
}

export function createDiscussionEntry(
  decisionId: string,
  input: {
    kind: DiscussionKind;
    body: string;
    mentioned_user_ids: string[];
    reply_to_id?: string | null;
  },
): Promise<DiscussionEntry> {
  return apiRequest<DiscussionEntry>(`/decisions/${decisionId}/discussion/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function resolveDiscussionEntry(
  entryId: string,
  resolutionNote: string,
): Promise<DiscussionEntry> {
  return apiRequest<DiscussionEntry>(`/discussion-entries/${entryId}/resolve/`, {
    method: "POST",
    body: JSON.stringify({ resolution_note: resolutionNote }),
  });
}

export function listDecisionActivity(decisionId: string): Promise<DecisionActivityItem[]> {
  return apiRequest<DecisionActivityItem[]>(`/decisions/${decisionId}/activity/`);
}
