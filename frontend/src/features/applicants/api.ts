import { apiRequest, ensureCsrfCookie } from "../../lib/api";
import type { MyApplicationsResponse } from "../../lib/types";

export async function requestMagicLink(input: { email: string; name?: string }): Promise<void> {
  await ensureCsrfCookie();
  await apiRequest<{ status: string }>("/applicants/magic-link/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function consumeMagicLink(
  token: string,
): Promise<{ email: string; name: string }> {
  await ensureCsrfCookie();
  return apiRequest<{ email: string; name: string }>(
    "/applicants/magic-link/consume/",
    { method: "POST", body: JSON.stringify({ token }) },
  );
}

export function getMyApplications(): Promise<MyApplicationsResponse> {
  return apiRequest<MyApplicationsResponse>("/applicants/me/applications/");
}

export async function logoutApplicantSession(): Promise<void> {
  await ensureCsrfCookie();
  return apiRequest<void>("/applicants/session/", { method: "DELETE" });
}

export async function submitProgressReport(
  ideaId: string,
  body: string,
): Promise<MyApplicationsResponse> {
  await ensureCsrfCookie();
  return apiRequest<MyApplicationsResponse>(`/applicants/me/applications/${ideaId}/progress-reports/`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}
