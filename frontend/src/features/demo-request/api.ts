import { apiRequest, ensureCsrfCookie } from "../../lib/api";

export type DemoRequestInput = {
  full_name: string;
  work_email: string;
  organisation_name: string;
  job_title: string;
  organisation_size: "1-10" | "11-50" | "51-200" | "201-1000" | "1000+" | "not_sure";
  primary_need:
    | "strategic_foresight"
    | "decision_governance"
    | "collective_intelligence"
    | "portfolio_prioritisation"
    | "organisational_learning"
    | "other";
  message: string;
  consent_to_contact: boolean;
  website: string;
};

export type DemoRequestResponse = {
  detail: string;
  reference: string;
};

export async function submitDemoRequest(input: DemoRequestInput): Promise<DemoRequestResponse> {
  await ensureCsrfCookie();
  return apiRequest<DemoRequestResponse>("/public/demo-requests/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
