import { apiRequest } from "../../lib/api";
import type { Disbursement, DisbursementConfiguration } from "../../lib/types";

export function getDisbursementConfiguration(organisationId: string): Promise<DisbursementConfiguration> {
  return apiRequest(`/organisations/${organisationId}/disbursement-configuration/`);
}

export function setDisbursementProvider(
  organisationId: string,
  input: { provider_key: "manual" | "stripe"; stripe_account_id?: string; currency: string },
): Promise<DisbursementConfiguration> {
  return apiRequest(`/organisations/${organisationId}/disbursement-configuration/`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function setDisbursementApiKey(organisationId: string, apiKey: string): Promise<DisbursementConfiguration> {
  return apiRequest(`/organisations/${organisationId}/disbursement-configuration/api-key/`, {
    method: "PUT",
    body: JSON.stringify({ api_key: apiKey }),
  });
}

export function clearDisbursementApiKey(organisationId: string): Promise<DisbursementConfiguration> {
  return apiRequest(`/organisations/${organisationId}/disbursement-configuration/api-key/`, {
    method: "DELETE",
  });
}

export function testDisbursementConnection(
  organisationId: string,
): Promise<{ ok: boolean; detail: string; provider_key: string; provider_label: string }> {
  return apiRequest(`/organisations/${organisationId}/disbursement-configuration/test-connection/`, {
    method: "POST",
  });
}

export function listDisbursements(optionId: string): Promise<Disbursement[]> {
  return apiRequest(`/decision-options/${optionId}/disbursements/`);
}

export function issueDisbursement(
  optionId: string,
  input: { amount: number; note?: string },
): Promise<Disbursement> {
  return apiRequest(`/decision-options/${optionId}/disbursements/`, {
    method: "POST",
    body: JSON.stringify({ ...input, idempotency_key: crypto.randomUUID() }),
  });
}
