import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { listMemberships } from "../organisations/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import {
  createResearchClaim,
  listResearchClaims,
  listSources,
} from "./api";
import { ResearchClaimsPanel } from "./ResearchClaimsPanel";

vi.mock("../organisations/api", () => ({ listMemberships: vi.fn() }));
vi.mock("../portfolio/api", () => ({ getOrganisationPortfolio: vi.fn() }));
vi.mock("./api", () => ({
  createResearchClaim: vi.fn(),
  linkSourceToResearchClaim: vi.fn(),
  listResearchClaims: vi.fn(),
  listSources: vi.fn(),
  unlinkSourceFromResearchClaim: vi.fn(),
  updateResearchClaim: vi.fn(),
}));

describe("ResearchClaimsPanel", () => {
  it("shows an inspectable evidence gate and records bounded claims", async () => {
    const owner = {
      id: "user-1",
      email: "owner@example.com",
      first_name: "Azeez",
      last_name: "Hamzat",
    };
    vi.mocked(listResearchClaims).mockResolvedValue([
      {
        id: "claim-1",
        organisation_id: "organisation-1",
        statement: "Hybrid participation can preserve input from non-digital channels.",
        state: "supported",
        state_label: "Supported",
        recommendation: "build",
        recommendation_label: "Build",
        relevance: "facilitation",
        relevance_label: "Facilitation",
        evidence_summary: "Independent guidance supports combined digital and in-person methods.",
        limitations: "CrowdSmarter has not yet measured its own outcomes.",
        assumptions: "Facilitators preserve source provenance.",
        reversal_conditions: "Pilots show that assisted capture excludes or distorts input.",
        expected_outcome: "More channel-diverse contributions reach the decision record.",
        authority_score: 3,
        directness_score: 3,
        recency_score: 2,
        triangulation_score: 1,
        evidence_score: 9,
        linked_decision: { id: "decision-1", title: "Participation delivery model" },
        owner,
        created_by: owner,
        review_due_on: "2026-12-01",
        last_reviewed_at: "2026-09-03T10:00:00Z",
        review_status: "scheduled",
        lifecycle_status: "active",
        lifecycle_status_label: "Active",
        source_links: [
          {
            id: "link-1",
            source_id: "source-1",
            source_title: "Independent participation guidance",
            source_type: "research",
            source_type_label: "Research publication",
            credibility: "high",
            source_url: "https://example.org/guidance",
            publisher: "Public institution",
            published_on: "2026-05-01",
            relationship: "supports",
            relationship_label: "Supports",
            note: "Directly recommends a hybrid method.",
            linked_by: owner,
            created_at: "2026-09-03T10:00:00Z",
            updated_at: "2026-09-03T10:00:00Z",
          },
          {
            id: "link-2",
            source_id: "source-2",
            source_title: "Delivery constraints report",
            source_type: "government",
            source_type_label: "Government or regulation",
            credibility: "high",
            source_url: "https://example.gov/constraints",
            publisher: "Public authority",
            published_on: "2026-06-01",
            relationship: "contradicts",
            relationship_label: "Contradicts",
            note: "Documents unresolved access barriers.",
            linked_by: owner,
            created_at: "2026-09-03T10:00:00Z",
            updated_at: "2026-09-03T10:00:00Z",
          },
        ],
        support_count: 1,
        contrary_count: 1,
        can_edit: true,
        created_at: "2026-09-03T10:00:00Z",
        updated_at: "2026-09-03T10:00:00Z",
      },
    ]);
    vi.mocked(listSources).mockResolvedValue([]);
    vi.mocked(listMemberships).mockResolvedValue([]);
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({ decisions: [] } as never);
    vi.mocked(createResearchClaim).mockResolvedValue({ id: "claim-2" } as never);

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <ResearchClaimsPanel organisationId="organisation-1" canContribute />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText("9")).toBeInTheDocument();
    expect(screen.getByText("Roadmap eligible")).toBeInTheDocument();
    expect(screen.getByText("1 supporting")).toBeInTheDocument();
    expect(screen.getByText("1 contrary")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Participation delivery model" })).toBeInTheDocument();
    expect(screen.getByText("CrowdSmarter has not yet measured its own outcomes.")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Neutral claim"), {
      target: { value: "A smaller reversible product test is justified." },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Save research claim" }).closest("form")!);

    await waitFor(() => expect(createResearchClaim).toHaveBeenCalledWith(
      "organisation-1",
      expect.objectContaining({
        statement: "A smaller reversible product test is justified.",
        state: "unknown",
        recommendation: "defer",
      }),
    ));
  });
});
