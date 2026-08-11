import { apiRequest } from "../../lib/api";
import type { AnalyticsInsight, OrganisationAnalytics } from "../../lib/types";

export function getOrganisationAnalytics(organisationId: string): Promise<OrganisationAnalytics> {
  return apiRequest<OrganisationAnalytics>(`/organisations/${organisationId}/analytics/`);
}

export function generateOrganisationAnalyticsInsight(organisationId: string): Promise<AnalyticsInsight> {
  return apiRequest<AnalyticsInsight>(`/organisations/${organisationId}/analytics/insight/`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}
