import { apiRequest } from "../../lib/api";
import type { AuditEvent } from "../../lib/types";

export function listAuditEvents(organisationId: string): Promise<AuditEvent[]> {
  return apiRequest<AuditEvent[]>(`/organisations/${organisationId}/audit-events/`);
}
