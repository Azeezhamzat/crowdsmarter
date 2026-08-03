import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { listDecisionTemplates } from "../decisions/api";
import { getOrganisation } from "./api";
import {
  listDecisionMethods,
  listDecisionMethodUsage,
} from "./methodology-api";
import { OrganisationMethodsPage } from "./OrganisationMethodsPage";

vi.mock("../decisions/api", () => ({ listDecisionTemplates: vi.fn() }));
vi.mock("./api", () => ({ getOrganisation: vi.fn() }));
vi.mock("./methodology-api", () => ({
  listDecisionMethods: vi.fn(),
  listDecisionMethodUsage: vi.fn(),
  cloneBuiltInMethod: vi.fn(),
  createDecisionMethod: vi.fn(),
  createMethodVersion: vi.fn(),
  updateMethodVersion: vi.fn(),
  approveMethodVersion: vi.fn(),
  retireDecisionMethod: vi.fn(),
}));

const organisation = {
  id: "o1", name: "AgriNova", slug: "agrinova", description: "", website_url: "",
  brand_name: "", primary_colour: "#315c54", invitation_policy: "owners_and_admins" as const,
  default_invitation_role: "contributor" as const, retention_days: null, status: "active" as const,
  deactivated_at: null, current_user_role: "owner" as const,
  created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
};

describe("OrganisationMethodsPage", () => {
  it("shows governed methods and their immutable usage history", async () => {
    vi.mocked(getOrganisation).mockResolvedValue(organisation);
    vi.mocked(listDecisionTemplates).mockResolvedValue([]);
    vi.mocked(listDecisionMethodUsage).mockResolvedValue([{
      id: "usage-1", method_name: "Strategic investment", method_version_number: 2,
      decision_id: "decision-1", decision_title: "Choose the pilot portfolio",
      applied_by_email: "owner@example.com", created_at: "2026-08-01T11:00:00Z",
    }]);
    vi.mocked(listDecisionMethods).mockResolvedValue([{
      id: "method-1", organisation_id: "o1", key: "strategic-investment",
      name: "Strategic investment", summary: "A governed investment method.",
      best_for: "Material cross-functional choices.", status: "approved", retired_at: null,
      created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
      versions: [], current_version: {
        id: "version-2", method_id: "method-1", organisation_id: "o1", version: 2,
        status: "approved", question_prompt: "State the choice.", purpose_prompt: "State the value.",
        context_prompt: "Describe context.", scope_prompt: "Set boundaries.", contribution_prompt: "Request evidence.",
        suggested_urgency: "normal", required_fields: ["decision_question"], checklist: ["Status quo considered"],
        evidence_prompts: [], assumption_prompts: [], risk_prompts: [], stakeholder_prompts: [], lifecycle_expectations: [],
        approved_by_email: "owner@example.com", approved_at: "2026-08-01T10:30:00Z",
        created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:30:00Z",
      },
    }]);

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/organisations/o1/methods"]}>
          <Routes><Route path="/organisations/:organisationId/methods" element={<OrganisationMethodsPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: /govern how important decisions are framed/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Strategic investment" })).toBeInTheDocument();
    expect(screen.getByText(/Choose the pilot portfolio/i)).toBeInTheDocument();
    expect(screen.getByText(/without pre-deciding the outcome/i)).toBeInTheDocument();
  });
});
