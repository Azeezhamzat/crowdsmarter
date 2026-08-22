import { apiRequest } from "../../lib/api";
import type { LookupConfiguration, OrganisationLookupResult } from "../../lib/types";

export function getLookupConfiguration(organisationId: string): Promise<LookupConfiguration> {
  return apiRequest(`/organisations/${organisationId}/lookup-configuration/`);
}

export function setLookupProvider(
  organisationId: string,
  input: { provider_key: "manual" | "candid" },
): Promise<LookupConfiguration> {
  return apiRequest(`/organisations/${organisationId}/lookup-configuration/`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function setLookupApiKey(organisationId: string, apiKey: string): Promise<LookupConfiguration> {
  return apiRequest(`/organisations/${organisationId}/lookup-configuration/api-key/`, {
    method: "PUT",
    body: JSON.stringify({ api_key: apiKey }),
  });
}

export function clearLookupApiKey(organisationId: string): Promise<LookupConfiguration> {
  return apiRequest(`/organisations/${organisationId}/lookup-configuration/api-key/`, {
    method: "DELETE",
  });
}

export function testLookupConnection(
  organisationId: string,
): Promise<{ ok: boolean; detail: string; provider_key: string; provider_label: string }> {
  return apiRequest(`/organisations/${organisationId}/lookup-configuration/test-connection/`, {
    method: "POST",
  });
}

export function lookupOrganisation(organisationId: string, query: string): Promise<OrganisationLookupResult> {
  return apiRequest(`/organisations/${organisationId}/lookup-organisation/`, {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}
