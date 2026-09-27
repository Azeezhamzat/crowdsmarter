import { apiRequest } from "../../lib/api";
import type {
  ForesightCanvas,
  ForesightCanvasWorkspace,
  ForesightConsequence,
  ForesightDriver,
  ForesightFeed,
  ForesightFeedbackLoop,
  ForesightOverview,
  ResearchClaim,
  ForesightRelationship,
  ForesightScenario,
  ForesightScenarioDriverState,
  ForesightScenarioImplicationLink,
  ForesightScenarioReview,
  ForesightScenarioSet,
  ForesightScenarioSetWorkspace,
  ForesightSignal,
  ForesightSignpost,
  ForesightSignpostObservation,
  ForesightSource,
  ForesightStakeholder,
  ForesightWatchlist,
  ForesightWindTunnelAssessment,
  StrategicImplication,
  ThreeHorizonItem,
} from "../../lib/types";

export function getForesightOverview(organisationId: string): Promise<ForesightOverview> {
  return apiRequest<ForesightOverview>(`/organisations/${organisationId}/foresight/overview/`);
}

export function listSources(organisationId: string): Promise<ForesightSource[]> {
  return apiRequest<ForesightSource[]>(`/organisations/${organisationId}/foresight/sources/`);
}

export function createSource(
  organisationId: string,
  input: Record<string, unknown>,
): Promise<ForesightSource> {
  return apiRequest<ForesightSource>(`/organisations/${organisationId}/foresight/sources/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function uploadSourceAttachment(sourceId: string, file: File): Promise<ForesightSource["attachments"][number]> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<ForesightSource["attachments"][number]>(`/foresight/sources/${sourceId}/attachments/`, {
    method: "POST",
    body,
  });
}

export function listResearchClaims(organisationId: string): Promise<ResearchClaim[]> {
  return apiRequest<ResearchClaim[]>(
    `/organisations/${organisationId}/foresight/research-claims/`,
  );
}

export function createResearchClaim(
  organisationId: string,
  input: Record<string, unknown>,
): Promise<ResearchClaim> {
  return apiRequest<ResearchClaim>(
    `/organisations/${organisationId}/foresight/research-claims/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function updateResearchClaim(
  claimId: string,
  input: Record<string, unknown>,
): Promise<ResearchClaim> {
  return apiRequest<ResearchClaim>(`/foresight/research-claims/${claimId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function linkSourceToResearchClaim(
  claimId: string,
  input: { source_id: string; relationship: string; note?: string },
): Promise<ResearchClaim> {
  return apiRequest<ResearchClaim>(`/foresight/research-claims/${claimId}/sources/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function unlinkSourceFromResearchClaim(
  claimId: string,
  sourceId: string,
): Promise<void> {
  return apiRequest<void>(
    `/foresight/research-claims/${claimId}/sources/${sourceId}/`,
    { method: "DELETE" },
  );
}

export function listSignals(organisationId: string): Promise<ForesightSignal[]> {
  return apiRequest<ForesightSignal[]>(`/organisations/${organisationId}/foresight/signals/`);
}

export function createSignal(
  organisationId: string,
  input: Record<string, unknown>,
): Promise<ForesightSignal> {
  return apiRequest<ForesightSignal>(`/organisations/${organisationId}/foresight/signals/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateSignal(signalId: string, input: Record<string, unknown>): Promise<ForesightSignal> {
  return apiRequest<ForesightSignal>(`/foresight/signals/${signalId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function linkSignalToDecision(
  signalId: string,
  decisionId: string,
  relevance: string,
): Promise<ForesightSignal> {
  return apiRequest<ForesightSignal>(`/foresight/signals/${signalId}/decisions/`, {
    method: "POST",
    body: JSON.stringify({ decision_id: decisionId, relevance }),
  });
}

export function listWatchlists(organisationId: string): Promise<ForesightWatchlist[]> {
  return apiRequest<ForesightWatchlist[]>(`/organisations/${organisationId}/foresight/watchlists/`);
}

export function createWatchlist(
  organisationId: string,
  input: Record<string, unknown>,
): Promise<ForesightWatchlist> {
  return apiRequest<ForesightWatchlist>(`/organisations/${organisationId}/foresight/watchlists/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function addSignalToWatchlist(
  watchlistId: string,
  signalId: string,
): Promise<ForesightWatchlist> {
  return apiRequest<ForesightWatchlist>(`/foresight/watchlists/${watchlistId}/signals/`, {
    method: "POST",
    body: JSON.stringify({ signal_id: signalId, note: "" }),
  });
}


export function listFeeds(organisationId: string): Promise<ForesightFeed[]> {
  return apiRequest<ForesightFeed[]>(`/organisations/${organisationId}/foresight/feeds/`);
}

export function createFeed(
  organisationId: string,
  input: { name: string; feed_url: string; owner_id?: string },
): Promise<ForesightFeed> {
  return apiRequest<ForesightFeed>(`/organisations/${organisationId}/foresight/feeds/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function syncFeed(feedId: string): Promise<{
  feed: ForesightFeed;
  result: { created_sources: number; entries_seen: number; not_modified: boolean };
}> {
  return apiRequest(`/foresight/feeds/${feedId}/sync/`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function listForesightCanvases(organisationId: string) {
  return apiRequest<ForesightCanvas[]>(
    `/organisations/${organisationId}/foresight/canvases/`,
  );
}

export function createForesightCanvas(organisationId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightCanvas>(
    `/organisations/${organisationId}/foresight/canvases/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function getForesightCanvas(canvasId: string) {
  return apiRequest<ForesightCanvasWorkspace>(
    `/foresight/canvases/${canvasId}/`,
  );
}

export function updateForesightCanvas(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightCanvas>(`/foresight/canvases/${canvasId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function createForesightDriver(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightDriver>(`/foresight/canvases/${canvasId}/drivers/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function linkDriverSignal(driverId: string, signalId: string, rationale: string) {
  return apiRequest<ForesightDriver>(`/foresight/drivers/${driverId}/signals/`, {
    method: "POST",
    body: JSON.stringify({ signal_id: signalId, rationale }),
  });
}

export function createSystemStakeholder(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightStakeholder>(
    `/foresight/canvases/${canvasId}/stakeholders/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function createCausalRelationship(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightRelationship>(
    `/foresight/canvases/${canvasId}/relationships/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function createFeedbackLoop(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightFeedbackLoop>(
    `/foresight/canvases/${canvasId}/feedback-loops/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function createFuturesConsequence(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightConsequence>(
    `/foresight/canvases/${canvasId}/consequences/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function createThreeHorizonItem(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<ThreeHorizonItem>(
    `/foresight/canvases/${canvasId}/horizons/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function createStrategicImplication(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<StrategicImplication>(
    `/foresight/canvases/${canvasId}/implications/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function updateStrategicImplication(implicationId: string, input: Record<string, unknown>) {
  return apiRequest<StrategicImplication>(
    `/foresight/implications/${implicationId}/`,
    { method: "PATCH", body: JSON.stringify(input) },
  );
}

export function listScenarioSets(canvasId: string) {
  return apiRequest<ForesightScenarioSet[]>(
    `/foresight/canvases/${canvasId}/scenario-sets/`,
  );
}

export function createScenarioSet(canvasId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightScenarioSet>(
    `/foresight/canvases/${canvasId}/scenario-sets/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function getScenarioSet(scenarioSetId: string) {
  return apiRequest<ForesightScenarioSetWorkspace>(
    `/foresight/scenario-sets/${scenarioSetId}/`,
  );
}

export function updateScenarioSet(scenarioSetId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightScenarioSet>(
    `/foresight/scenario-sets/${scenarioSetId}/`,
    { method: "PATCH", body: JSON.stringify(input) },
  );
}

export function createScenario(scenarioSetId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightScenario>(
    `/foresight/scenario-sets/${scenarioSetId}/scenarios/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function updateScenario(scenarioId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightScenario>(
    `/foresight/scenarios/${scenarioId}/`,
    { method: "PATCH", body: JSON.stringify(input) },
  );
}

export function setScenarioDriverState(scenarioId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightScenarioDriverState>(
    `/foresight/scenarios/${scenarioId}/driver-states/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function submitScenarioReview(scenarioId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightScenarioReview>(
    `/foresight/scenarios/${scenarioId}/reviews/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function assessScenarioOption(scenarioId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightWindTunnelAssessment>(
    `/foresight/scenarios/${scenarioId}/wind-tunnel/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function createScenarioSignpost(scenarioSetId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightSignpost>(
    `/foresight/scenario-sets/${scenarioSetId}/signposts/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function createSignpostObservation(signpostId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightSignpostObservation>(
    `/foresight/signposts/${signpostId}/observations/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function linkScenarioImplication(scenarioId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightScenarioImplicationLink>(
    `/foresight/scenarios/${scenarioId}/implications/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function linkSignpostToAssumption(signpostId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightSignpost>(
    `/foresight/signposts/${signpostId}/assumption-links/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function linkSignpostToRisk(signpostId: string, input: Record<string, unknown>) {
  return apiRequest<ForesightSignpost>(
    `/foresight/signposts/${signpostId}/risk-links/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}
