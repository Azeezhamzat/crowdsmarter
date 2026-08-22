import { apiRequest, ensureCsrfCookie } from "../../lib/api";
import type { MyApplicationsResponse } from "../../lib/types";

const APPLICANT_TOKEN_HEADER = "X-Applicant-Token";
const STORAGE_KEY = "crowdsmarter:applicant-portal-token";

export function getStoredApplicantToken(): string | null {
  return window.localStorage.getItem(STORAGE_KEY);
}

export function storeApplicantToken(token: string): void {
  window.localStorage.setItem(STORAGE_KEY, token);
}

export function clearApplicantToken(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}

function applicantHeaders(): HeadersInit | undefined {
  const token = getStoredApplicantToken();
  return token ? { [APPLICANT_TOKEN_HEADER]: token } : undefined;
}

export async function requestMagicLink(input: { email: string; name?: string }): Promise<void> {
  await ensureCsrfCookie();
  await apiRequest<{ status: string }>("/applicants/magic-link/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function consumeMagicLink(
  token: string,
): Promise<{ applicant_token: string; email: string; name: string }> {
  await ensureCsrfCookie();
  const result = await apiRequest<{ applicant_token: string; email: string; name: string }>(
    "/applicants/magic-link/consume/",
    { method: "POST", body: JSON.stringify({ token }) },
  );
  storeApplicantToken(result.applicant_token);
  return result;
}

export function getMyApplications(): Promise<MyApplicationsResponse> {
  return apiRequest<MyApplicationsResponse>("/applicants/me/applications/", {
    headers: applicantHeaders(),
  });
}

export async function submitProgressReport(
  ideaId: string,
  body: string,
): Promise<MyApplicationsResponse> {
  await ensureCsrfCookie();
  return apiRequest<MyApplicationsResponse>(`/applicants/me/applications/${ideaId}/progress-reports/`, {
    method: "POST",
    body: JSON.stringify({ body }),
    headers: applicantHeaders(),
  });
}
