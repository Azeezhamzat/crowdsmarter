import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { listMemberships } from "../organisations/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import {
  createCausalRelationship,
  createFeedbackLoop,
  createForesightDriver,
  createFuturesConsequence,
  createStrategicImplication,
  createSystemStakeholder,
  createThreeHorizonItem,
  getForesightCanvas,
  linkDriverSignal,
  listSignals,
  updateForesightCanvas,
  updateStrategicImplication,
} from "./api";
import {
  EMPTY_CONSEQUENCE,
  EMPTY_DRIVER,
  EMPTY_FEEDBACK_LOOP,
  EMPTY_HORIZON,
  EMPTY_IMPLICATION,
  EMPTY_RELATIONSHIP,
  EMPTY_STAKEHOLDER,
  type CanvasTab,
  type ConsequenceForm,
  type DriverForm,
  type FeedbackLoopForm,
  type HorizonForm,
  type ImplicationForm,
  personName,
  type RelationshipForm,
  type SignalLinkForm,
  type StakeholderForm,
} from "./canvasTypes";
import { ForesightCanvasOverview as CanvasOverview } from "./ForesightCanvasOverview";
import { ForesightDriversSection as DriversSection } from "./ForesightDriversSection";
import {
  ForesightFuturesWheelSection as FuturesWheelSection,
  ForesightThreeHorizonsSection as ThreeHorizonsSection,
} from "./ForesightFuturesSections";
import { ForesightImplicationsSection as ImplicationsSection } from "./ForesightImplicationsSection";
import { ForesightSystemMapSection as SystemMapSection } from "./ForesightSystemMapSection";
import { ForesightScenarioSetsSection as ScenarioSetsSection } from "./ForesightScenarioSetsSection";

function mutationErrorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "The foresight action could not be completed.";
}

export function ForesightCanvasPage() {
  const { organisationId = "", canvasId = "" } = useParams<{
    organisationId: string;
    canvasId: string;
  }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const tab: CanvasTab = [
    "overview",
    "drivers",
    "system",
    "wheel",
    "horizons",
    "scenarios",
    "implications",
  ].includes(requestedTab ?? "")
    ? (requestedTab as CanvasTab)
    : "overview";
  const queryClient = useQueryClient();

  const [driverForm, setDriverForm] = useState<DriverForm>(EMPTY_DRIVER);
  const [stakeholderForm, setStakeholderForm] =
    useState<StakeholderForm>(EMPTY_STAKEHOLDER);
  const [relationshipForm, setRelationshipForm] =
    useState<RelationshipForm>(EMPTY_RELATIONSHIP);
  const [feedbackLoopForm, setFeedbackLoopForm] =
    useState<FeedbackLoopForm>(EMPTY_FEEDBACK_LOOP);
  const [consequenceForm, setConsequenceForm] =
    useState<ConsequenceForm>(EMPTY_CONSEQUENCE);
  const [horizonForm, setHorizonForm] = useState<HorizonForm>(EMPTY_HORIZON);
  const [implicationForm, setImplicationForm] =
    useState<ImplicationForm>(EMPTY_IMPLICATION);
  const [signalLink, setSignalLink] = useState<SignalLinkForm>({});

  const canvas = useQuery({
    queryKey: ["foresight", "canvases", canvasId],
    queryFn: () => getForesightCanvas(canvasId),
    enabled: Boolean(canvasId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", organisationId, "memberships"],
    queryFn: () => listMemberships(organisationId),
    enabled: Boolean(organisationId),
  });
  const signals = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "signals"],
    queryFn: () => listSignals(organisationId),
    enabled: Boolean(organisationId),
  });
  const portfolio = useQuery({
    queryKey: ["organisations", organisationId, "portfolio", "foresight-canvas"],
    queryFn: () => getOrganisationPortfolio(organisationId, {}),
    enabled: Boolean(organisationId),
  });

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["foresight", "canvases", canvasId],
      }),
      queryClient.invalidateQueries({
        queryKey: ["organisations", organisationId, "foresight", "canvases"],
      }),
      queryClient.invalidateQueries({
        queryKey: ["organisations", organisationId, "search"],
      }),
    ]);
  };

  const createDriver = useMutation({
    mutationFn: () =>
      createForesightDriver(canvasId, {
        ...driverForm,
        owner_id: driverForm.owner_id || undefined,
      }),
    onSuccess: async () => {
      setDriverForm(EMPTY_DRIVER);
      await refresh();
    },
  });
  const createStakeholder = useMutation({
    mutationFn: () => createSystemStakeholder(canvasId, stakeholderForm),
    onSuccess: async () => {
      setStakeholderForm(EMPTY_STAKEHOLDER);
      await refresh();
    },
  });
  const createRelationship = useMutation({
    mutationFn: () => createCausalRelationship(canvasId, relationshipForm),
    onSuccess: async () => {
      setRelationshipForm(EMPTY_RELATIONSHIP);
      await refresh();
    },
  });
  const createLoop = useMutation({
    mutationFn: () => createFeedbackLoop(canvasId, feedbackLoopForm),
    onSuccess: async () => {
      setFeedbackLoopForm(EMPTY_FEEDBACK_LOOP);
      await refresh();
    },
  });
  const createConsequence = useMutation({
    mutationFn: () =>
      createFuturesConsequence(canvasId, {
        ...consequenceForm,
        originating_driver_id: consequenceForm.originating_driver_id || null,
        parent_id: consequenceForm.parent_id || null,
      }),
    onSuccess: async () => {
      setConsequenceForm(EMPTY_CONSEQUENCE);
      await refresh();
    },
  });
  const createHorizon = useMutation({
    mutationFn: () => createThreeHorizonItem(canvasId, horizonForm),
    onSuccess: async () => {
      setHorizonForm(EMPTY_HORIZON);
      await refresh();
    },
  });
  const createImplication = useMutation({
    mutationFn: () =>
      createStrategicImplication(canvasId, {
        ...implicationForm,
        owner_id: implicationForm.owner_id || undefined,
        linked_decision_id: implicationForm.linked_decision_id || null,
      }),
    onSuccess: async () => {
      setImplicationForm(EMPTY_IMPLICATION);
      await refresh();
    },
  });
  const updateCanvas = useMutation({
    mutationFn: (input: Record<string, unknown>) =>
      updateForesightCanvas(canvasId, input),
    onSuccess: refresh,
  });
  const updateImplication = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateStrategicImplication(id, { status }),
    onSuccess: refresh,
  });
  const linkSignal = useMutation({
    mutationFn: ({
      driverId,
      signalId,
      rationale,
    }: {
      driverId: string;
      signalId: string;
      rationale: string;
    }) => linkDriverSignal(driverId, signalId, rationale),
    onSuccess: async (_, variables) => {
      setSignalLink((current) => ({
        ...current,
        [variables.driverId]: { signalId: "", rationale: "" },
      }));
      await refresh();
    },
  });

  const errors = [
    createDriver.error,
    createStakeholder.error,
    createRelationship.error,
    createLoop.error,
    createConsequence.error,
    createHorizon.error,
    createImplication.error,
    linkSignal.error,
    updateCanvas.error,
    updateImplication.error,
  ].filter(Boolean);

  const data = canvas.data;
  const groupedConsequences = useMemo(
    () => ({
      1: data?.consequences.filter((item) => item.order === 1) ?? [],
      2: data?.consequences.filter((item) => item.order === 2) ?? [],
      3: data?.consequences.filter((item) => item.order === 3) ?? [],
    }),
    [data?.consequences],
  );

  if (canvas.isPending) return <p>Loading foresight canvas…</p>;
  if (canvas.isError || !data) {
    return (
      <StatusMessage kind="error">
        The foresight canvas could not be loaded.
      </StatusMessage>
    );
  }

  const tabs: Array<{ key: CanvasTab; label: string }> = [
    { key: "overview", label: "Overview" },
    { key: "drivers", label: "Drivers" },
    { key: "system", label: "System map" },
    { key: "wheel", label: "Futures wheel" },
    { key: "horizons", label: "Three Horizons" },
    { key: "scenarios", label: "Scenarios" },
    { key: "implications", label: "Implications" },
  ];

  const setTab = (value: CanvasTab) => {
    setSearchParams(value === "overview" ? {} : { tab: value });
  };

  return (
    <div className="foresight-canvas-page">
      <Link
        className="back-link"
        to={`/organisations/${organisationId}/foresight/canvases`}
      >
        ← Foresight canvases
      </Link>

      <header className="foresight-canvas-hero">
        <div>
          <div className="inline-badges">
            <span className={`status-badge status-badge--${data.status}`}>
              {data.status_label}
            </span>
            <span className="role-badge">Horizon {data.horizon_year}</span>
          </div>
          <p className="eyebrow">Systems foresight canvas</p>
          <h1>{data.title}</h1>
          <p className="foresight-canvas-question">{data.focal_question}</p>
        </div>
        <div className="foresight-canvas-owner">
          <span>Accountable owner</span>
          <strong>{personName(data.owner)}</strong>
          <small>{data.scope}</small>
        </div>
      </header>

      {errors.length ? (
        <StatusMessage kind="error">
          {mutationErrorMessage(errors[0])}
        </StatusMessage>
      ) : null}

      <section className="foresight-canvas-metrics" aria-label="Canvas summary">
        <article>
          <strong>{data.summary.driver_count}</strong>
          <span>active drivers</span>
        </article>
        <article>
          <strong>{data.summary.critical_uncertainty_count}</strong>
          <span>critical uncertainties</span>
        </article>
        <article>
          <strong>{data.summary.high_attention_count}</strong>
          <span>high-attention drivers</span>
        </article>
        <article>
          <strong>{data.summary.relationship_count}</strong>
          <span>causal links</span>
        </article>
        <article>
          <strong>{data.summary.feedback_loop_count}</strong>
          <span>feedback loops</span>
        </article>
        <article>
          <strong>{data.summary.scenario_set_count}</strong>
          <span>scenario sets</span>
        </article>
        <article>
          <strong>{data.summary.open_implication_count}</strong>
          <span>open implications</span>
        </article>
      </section>

      <nav className="foresight-canvas-tabs" aria-label="Canvas sections">
        {tabs.map((item) => (
          <button
            className={tab === item.key ? "is-active" : ""}
            key={item.key}
            onClick={() => setTab(item.key)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>

      {tab === "overview" ? (
        <CanvasOverview
          canvas={data}
          isSaving={updateCanvas.isPending}
          memberships={memberships.data ?? []}
          save={(input) => updateCanvas.mutate(input)}
          setTab={setTab}
        />
      ) : null}
      {tab === "drivers" ? (
        <DriversSection
          canvas={data}
          form={driverForm}
          isSaving={createDriver.isPending}
          memberships={memberships.data ?? []}
          organisationId={organisationId}
          setForm={setDriverForm}
          setSignalLink={setSignalLink}
          signalLink={signalLink}
          signals={signals.data ?? []}
          submit={() => createDriver.mutate()}
          submitSignal={(driverId, signalId, rationale) =>
            linkSignal.mutate({ driverId, signalId, rationale })
          }
        />
      ) : null}
      {tab === "system" ? (
        <SystemMapSection
          canvas={data}
          createFeedbackLoop={() => createLoop.mutate()}
          createRelationship={() => createRelationship.mutate()}
          createStakeholder={() => createStakeholder.mutate()}
          feedbackLoopForm={feedbackLoopForm}
          relationshipForm={relationshipForm}
          setFeedbackLoopForm={setFeedbackLoopForm}
          setRelationshipForm={setRelationshipForm}
          setStakeholderForm={setStakeholderForm}
          stakeholderForm={stakeholderForm}
        />
      ) : null}
      {tab === "wheel" ? (
        <FuturesWheelSection
          canvas={data}
          form={consequenceForm}
          grouped={groupedConsequences}
          setForm={setConsequenceForm}
          submit={() => createConsequence.mutate()}
        />
      ) : null}
      {tab === "horizons" ? (
        <ThreeHorizonsSection
          canvas={data}
          form={horizonForm}
          setForm={setHorizonForm}
          submit={() => createHorizon.mutate()}
        />
      ) : null}
      {tab === "scenarios" ? (
        <ScenarioSetsSection
          canvas={data}
          decisions={portfolio.data?.decisions ?? []}
          memberships={memberships.data ?? []}
          organisationId={organisationId}
        />
      ) : null}
      {tab === "implications" ? (
        <ImplicationsSection
          canvas={data}
          decisions={portfolio.data?.decisions ?? []}
          form={implicationForm}
          memberships={memberships.data ?? []}
          setForm={setImplicationForm}
          submit={() => createImplication.mutate()}
          updateStatus={(id, status) =>
            updateImplication.mutate({ id, status })
          }
        />
      ) : null}
    </div>
  );
}
