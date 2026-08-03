import { useQuery } from "@tanstack/react-query";
import { Link, Navigate, useParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { getDecision } from "../decisions/api";
import { listMemberships } from "../organisations/api";
import { AssumptionsSection } from "./AssumptionsSection";
import { EvidenceSection } from "./EvidenceSection";
import { OptionsSection } from "./OptionsSection";
import { RisksSection } from "./RisksSection";

const sections = ["options", "evidence", "assumptions", "risks"] as const;
type Section = (typeof sections)[number];

function isSection(value: string | undefined): value is Section {
  return sections.includes(value as Section);
}

export function DecisionReasoningPage() {
  const { decisionId = "", section } = useParams();
  const decision = useQuery({
    queryKey: ["decisions", decisionId],
    queryFn: () => getDecision(decisionId),
    enabled: Boolean(decisionId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", decision.data?.organisation_id, "memberships"],
    queryFn: () => listMemberships(decision.data?.organisation_id ?? ""),
    enabled: Boolean(decision.data?.organisation_id),
  });

  if (!isSection(section)) {
    return (
      <Navigate
        to={`/decisions/${decisionId}/reasoning/options`}
        replace
      />
    );
  }
  if (decision.isPending) {
    return <p>Loading structured review…</p>;
  }
  if (decision.isError || !decision.data) {
    return (
      <StatusMessage kind="error">
        The decision could not be loaded.
      </StatusMessage>
    );
  }

  const current = decision.data;
  return (
    <div>
      <Link className="back-link" to={`/decisions/${decisionId}`}>
        ← Decision workspace
      </Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Structured review</p>
          <h1>{current.title}</h1>
          <p className="decision-question">{current.decision_question}</p>
        </div>
        <span className="status-badge">{current.status_label}</span>
      </div>

      <section className="readiness-panel" aria-labelledby="readiness-title">
        <div>
          <p className="eyebrow">Readiness gate</p>
          <h2 id="readiness-title">Ready for decision</h2>
        </div>
        <div className="readiness-metrics">
          <span>
            <strong>{current.reasoning_summary.active_options}</strong> options
          </span>
          <span>
            <strong>{current.reasoning_summary.active_evidence}</strong> evidence
          </span>
          <span>
            <strong>{current.reasoning_summary.active_assumptions}</strong>{" "}
            assumptions
          </span>
          <span>
            <strong>{current.reasoning_summary.current_risks}</strong> risks
          </span>
        </div>
        {current.reasoning_summary.ready_for_decision ? (
          <StatusMessage kind="success">
            The minimum structured reasoning gate is satisfied. Human reviewers
            must still judge quality and relevance.
          </StatusMessage>
        ) : (
          <ul className="blocker-list">
            {current.reasoning_summary.blockers.map((blocker) => (
              <li key={blocker}>{blocker}</li>
            ))}
          </ul>
        )}
      </section>

      <nav className="section-tabs" aria-label="Structured review sections">
        {sections.map((item) => (
          <Link
            className={
              item === section
                ? "section-tab section-tab--active"
                : "section-tab"
            }
            key={item}
            to={`/decisions/${decisionId}/reasoning/${item}`}
          >
            {item}
          </Link>
        ))}
      </nav>

      {memberships.isError && (section === "assumptions" || section === "risks") ? (
        <StatusMessage kind="error">
          Organisation members could not be loaded. Existing records remain
          visible, but accountable ownership cannot be reassigned right now.
        </StatusMessage>
      ) : null}

      {section === "options" ? (
        <OptionsSection
          decisionId={decisionId}
          canContribute={current.can_contribute_reasoning}
        />
      ) : null}
      {section === "evidence" ? (
        <EvidenceSection
          decisionId={decisionId}
          canContribute={current.can_contribute_reasoning}
        />
      ) : null}
      {section === "assumptions" ? (
        <AssumptionsSection
          decisionId={decisionId}
          canContribute={current.can_contribute_reasoning}
          memberships={memberships.data ?? []}
        />
      ) : null}
      {section === "risks" ? (
        <RisksSection
          decisionId={decisionId}
          canContribute={current.can_contribute_reasoning}
          memberships={memberships.data ?? []}
        />
      ) : null}
    </div>
  );
}
