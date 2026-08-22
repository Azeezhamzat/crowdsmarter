import { apiRequest } from "../../lib/api";
import type { OrganisationBudgetRollup, OrganisationPortfolio, PersonalWork } from "../../lib/types";

export function getPersonalWork(): Promise<PersonalWork> {
  return apiRequest<PersonalWork>("/me/work/");
}

export function getOrganisationPortfolio(
  organisationId: string,
  filters: Record<string, string | boolean>,
): Promise<OrganisationPortfolio> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== "" && value !== false) params.set(key, String(value));
  }
  const suffix = params.size ? `?${params.toString()}` : "";
  return apiRequest<OrganisationPortfolio>(
    `/organisations/${organisationId}/portfolio/${suffix}`,
  );
}

export function getOrganisationBudgetRollup(organisationId: string): Promise<OrganisationBudgetRollup> {
  return apiRequest<OrganisationBudgetRollup>(`/organisations/${organisationId}/budget-rollup/`);
}
