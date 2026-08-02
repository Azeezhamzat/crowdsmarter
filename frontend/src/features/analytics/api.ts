import { apiRequest } from "../../lib/api";
import type { OrganisationAnalytics } from "../../lib/types";

export function getOrganisationAnalytics(organisationId: string): Promise<OrganisationAnalytics> {
  return apiRequest<OrganisationAnalytics>(`/organisations/${organisationId}/analytics/`);
}
