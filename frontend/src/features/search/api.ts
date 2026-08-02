import { apiRequest } from "../../lib/api";
import type { SearchResponse } from "../../lib/types";

export function searchOrganisation(organisationId: string, query: string): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  return apiRequest<SearchResponse>(`/organisations/${organisationId}/search/?${params.toString()}`);
}
