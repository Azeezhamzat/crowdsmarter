import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createSignal,
  createResearchClaim,
  getForesightOverview,
  linkSignalToDecision,
  linkSourceToResearchClaim,
  syncFeed,
  uploadSourceAttachment,
  updateResearchClaim,
  createForesightCanvas,
  createScenarioSet,
  assessScenarioOption,
  createSignpostObservation,
} from "./api";

afterEach(() => {
  vi.restoreAllMocks();
});

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

function parseRequestBody(body: BodyInit | null | undefined): unknown {
  expect(typeof body).toBe("string");
  return JSON.parse(typeof body === "string" ? body : "{}");
}

describe("foresight API contracts", () => {
  it("reads the organisation overview from the tenant-scoped route", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ signal_count: 0 }),
    );

    await getForesightOverview("organisation-1");

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/api/v1/organisations/organisation-1/foresight/overview/",
    );
  });

  it("uploads private files with FormData rather than JSON", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ id: "attachment-1" }),
    );
    const file = new File(["source"], "source.txt", { type: "text/plain" });

    await uploadSourceAttachment("source-1", file);

    const [, init] = fetchMock.mock.calls[0] ?? [];
    expect(init?.method).toBe("POST");
    expect(init?.body).toBeInstanceOf(FormData);
    expect(new Headers(init?.headers).has("Content-Type")).toBe(false);
  });

  it("keeps signal interpretation and decision relevance explicit", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ id: "signal-1" }))
      .mockResolvedValueOnce(jsonResponse({ id: "signal-1" }));

    await createSignal("organisation-1", {
      title: "Emerging change",
      summary: "What is happening now",
      future_implication: "Why it may matter later",
    });
    await linkSignalToDecision(
      "signal-1",
      "decision-1",
      "This may change the option assumptions.",
    );

    expect(parseRequestBody(fetchMock.mock.calls[0]?.[1]?.body)).toMatchObject({
      summary: "What is happening now",
      future_implication: "Why it may matter later",
    });
    expect(parseRequestBody(fetchMock.mock.calls[1]?.[1]?.body)).toEqual({
      decision_id: "decision-1",
      relevance: "This may change the option assumptions.",
    });
  });

  it("keeps research claims, scoring, and contrary evidence explicit", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ id: "claim-1" }))
      .mockResolvedValueOnce(jsonResponse({ id: "claim-1" }))
      .mockResolvedValueOnce(jsonResponse({ id: "claim-1" }));

    await createResearchClaim("organisation-1", {
      statement: "Hybrid participation reduces access barriers.",
      state: "plausible",
      authority_score: 3,
      directness_score: 2,
      recency_score: 2,
      triangulation_score: 1,
      reversal_conditions: "A pilot shows no improvement in participation diversity.",
    });
    await linkSourceToResearchClaim("claim-1", {
      source_id: "source-1",
      relationship: "contradicts",
      note: "Documents barriers that remain after hybrid delivery.",
    });
    await updateResearchClaim("claim-1", { recommendation: "monitor" });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/api/v1/organisations/organisation-1/foresight/research-claims/",
    );
    expect(parseRequestBody(fetchMock.mock.calls[0]?.[1]?.body)).toMatchObject({
      statement: "Hybrid participation reduces access barriers.",
      authority_score: 3,
      reversal_conditions: "A pilot shows no improvement in participation diversity.",
    });
    expect(parseRequestBody(fetchMock.mock.calls[1]?.[1]?.body)).toEqual({
      source_id: "source-1",
      relationship: "contradicts",
      note: "Documents barriers that remain after hybrid delivery.",
    });
    expect(fetchMock.mock.calls[2]?.[0]).toBe(
      "/api/v1/foresight/research-claims/claim-1/",
    );
  });

  it("creates systems canvases through a tenant-scoped command", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ id: "canvas-1" }),
    );

    await createForesightCanvas("organisation-1", {
      title: "Future system",
      focal_question: "What may reshape the system?",
      scope: "A bounded inquiry",
      horizon_year: 2035,
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/api/v1/organisations/organisation-1/foresight/canvases/",
    );
  });

  it("uses a separate manual command to synchronise a feed", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ feed: {}, result: { created_sources: 0 } }),
    );

    await syncFeed("feed-1");

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/api/v1/foresight/feeds/feed-1/sync/",
    );
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe("POST");
  });
  it("keeps scenario construction, wind-tunnelling, and observations explicit", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ id: "scenario-set-1" }))
      .mockResolvedValueOnce(jsonResponse({ id: "assessment-1" }))
      .mockResolvedValueOnce(jsonResponse({ id: "observation-1" }));

    await createScenarioSet("canvas-1", {
      title: "Resilience pathways",
      purpose: "Stress-test the live strategy.",
      axis_x_driver_id: "driver-x",
      axis_x_low_label: "Restricted finance",
      axis_x_high_label: "Inclusive finance",
      axis_y_driver_id: "driver-y",
      axis_y_low_label: "Concentrated automation",
      axis_y_high_label: "Accessible automation",
    });
    await assessScenarioOption("scenario-1", {
      option_id: "option-1",
      verdict: "adaptable",
      desirability: 4,
      feasibility: 3,
      resilience: 4,
      rationale: "The option remains useful if governance conditions hold.",
    });
    await createSignpostObservation("signpost-1", {
      observed_on: "2026-08-01",
      value: "29%",
      assessment: "moderate",
      evidence: "Two lenders widened eligibility.",
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/api/v1/foresight/canvases/canvas-1/scenario-sets/",
    );
    expect(fetchMock.mock.calls[1]?.[0]).toBe(
      "/api/v1/foresight/scenarios/scenario-1/wind-tunnel/",
    );
    expect(fetchMock.mock.calls[2]?.[0]).toBe(
      "/api/v1/foresight/signposts/signpost-1/observations/",
    );
  });

});
