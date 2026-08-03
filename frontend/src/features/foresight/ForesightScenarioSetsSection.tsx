import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type {
  ForesightCanvasWorkspace,
  Membership,
  PortfolioDecision,
} from "../../lib/types";
import { createScenarioSet } from "./api";
import { personName } from "./canvasTypes";

const EMPTY_FORM = {
  title: "",
  purpose: "",
  axis_x_driver_id: "",
  axis_x_low_label: "",
  axis_x_high_label: "",
  axis_y_driver_id: "",
  axis_y_low_label: "",
  axis_y_high_label: "",
  linked_decision_id: "",
  owner_id: "",
  status: "draft",
};

export function ForesightScenarioSetsSection({
  canvas,
  organisationId,
  memberships,
  decisions,
}: {
  canvas: ForesightCanvasWorkspace;
  organisationId: string;
  memberships: Membership[];
  decisions: PortfolioDecision[];
}) {
  const [form, setForm] = useState(EMPTY_FORM);
  const queryClient = useQueryClient();
  const uncertainties = useMemo(
    () =>
      canvas.drivers.filter(
        (driver) => driver.driver_type === "critical_uncertainty" && driver.is_active,
      ),
    [canvas.drivers],
  );

  const mutation = useMutation({
    mutationFn: () =>
      createScenarioSet(canvas.id, {
        ...form,
        owner_id: form.owner_id || undefined,
        linked_decision_id: form.linked_decision_id || null,
      }),
    onSuccess: async () => {
      setForm(EMPTY_FORM);
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["foresight", "canvases", canvas.id],
        }),
        queryClient.invalidateQueries({
          queryKey: ["organisations", organisationId, "search"],
        }),
      ]);
    },
  });

  const errorMessage =
    mutation.error instanceof ApiError
      ? mutation.error.message
      : mutation.error
        ? "The scenario set could not be created."
        : null;

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Alternative futures</p>
            <h2>Scenario sets</h2>
          </div>
          <span className="role-badge">Human-authored worlds</span>
        </div>

        <div className="scenario-set-list">
          {canvas.scenario_sets.map((item) => (
            <Link
              className="scenario-set-card"
              key={item.id}
              to={`/organisations/${organisationId}/foresight/canvases/${canvas.id}/scenarios/${item.id}`}
            >
              <div className="scenario-set-card__top">
                <div className="inline-badges">
                  <span className={`status-badge status-badge--${item.status}`}>
                    {item.status_label}
                  </span>
                  <span className="role-badge">
                    {item.scenario_count}/4 worlds
                  </span>
                </div>
                <Icon name="arrow-right" size={18} />
              </div>
              <h3>{item.title}</h3>
              <p>{item.purpose}</p>
              <div className="scenario-axis-summary">
                <span>
                  <strong>X</strong> {item.axis_x_low_label} ↔ {item.axis_x_high_label}
                </span>
                <span>
                  <strong>Y</strong> {item.axis_y_low_label} ↔ {item.axis_y_high_label}
                </span>
              </div>
              <footer>
                <span>Owner: {personName(item.owner)}</span>
                <span>{item.signpost_count} signposts</span>
                <span>{item.linked_decision_title ?? "Exploratory"}</span>
              </footer>
            </Link>
          ))}
          {!canvas.scenario_sets.length ? (
            <div className="empty-state">
              <Icon name="decision" />
              <h3>No scenario set yet</h3>
              <p>
                Choose two high-impact critical uncertainties and define four
                plausible worlds before testing strategies against them.
              </p>
            </div>
          ) : null}
        </div>
      </section>

      <aside className="side-panel foresight-create-panel">
        <p className="eyebrow">Scenario architecture</p>
        <h2>Create a 2×2 set</h2>
        {uncertainties.length < 2 ? (
          <StatusMessage kind="warning">
            Add at least two active critical uncertainties in the Drivers tab.
          </StatusMessage>
        ) : null}
        {errorMessage ? <StatusMessage kind="error">{errorMessage}</StatusMessage> : null}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate();
          }}
        >
          <label htmlFor="scenario-set-title">Title</label>
          <input
            id="scenario-set-title"
            required
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
          <label htmlFor="scenario-set-purpose">Purpose</label>
          <textarea
            id="scenario-set-purpose"
            required
            rows={4}
            value={form.purpose}
            onChange={(event) => setForm({ ...form, purpose: event.target.value })}
          />

          <fieldset className="scenario-axis-fieldset">
            <legend>X axis</legend>
            <label htmlFor="scenario-axis-x-driver">Critical uncertainty</label>
            <select
              id="scenario-axis-x-driver"
              required
              value={form.axis_x_driver_id}
              onChange={(event) =>
                setForm({ ...form, axis_x_driver_id: event.target.value })
              }
            >
              <option value="">Choose uncertainty</option>
              {uncertainties.map((driver) => (
                <option key={driver.id} value={driver.id}>
                  {driver.title}
                </option>
              ))}
            </select>
            <div className="form-row">
              <div>
                <label htmlFor="scenario-axis-x-low">Low endpoint</label>
                <input
                  id="scenario-axis-x-low"
                  required
                  value={form.axis_x_low_label}
                  onChange={(event) =>
                    setForm({ ...form, axis_x_low_label: event.target.value })
                  }
                />
              </div>
              <div>
                <label htmlFor="scenario-axis-x-high">High endpoint</label>
                <input
                  id="scenario-axis-x-high"
                  required
                  value={form.axis_x_high_label}
                  onChange={(event) =>
                    setForm({ ...form, axis_x_high_label: event.target.value })
                  }
                />
              </div>
            </div>
          </fieldset>

          <fieldset className="scenario-axis-fieldset">
            <legend>Y axis</legend>
            <label htmlFor="scenario-axis-y-driver">Critical uncertainty</label>
            <select
              id="scenario-axis-y-driver"
              required
              value={form.axis_y_driver_id}
              onChange={(event) =>
                setForm({ ...form, axis_y_driver_id: event.target.value })
              }
            >
              <option value="">Choose uncertainty</option>
              {uncertainties.map((driver) => (
                <option key={driver.id} value={driver.id}>
                  {driver.title}
                </option>
              ))}
            </select>
            <div className="form-row">
              <div>
                <label htmlFor="scenario-axis-y-low">Low endpoint</label>
                <input
                  id="scenario-axis-y-low"
                  required
                  value={form.axis_y_low_label}
                  onChange={(event) =>
                    setForm({ ...form, axis_y_low_label: event.target.value })
                  }
                />
              </div>
              <div>
                <label htmlFor="scenario-axis-y-high">High endpoint</label>
                <input
                  id="scenario-axis-y-high"
                  required
                  value={form.axis_y_high_label}
                  onChange={(event) =>
                    setForm({ ...form, axis_y_high_label: event.target.value })
                  }
                />
              </div>
            </div>
          </fieldset>

          <label htmlFor="scenario-set-decision">Decision to wind-tunnel</label>
          <select
            id="scenario-set-decision"
            value={form.linked_decision_id}
            onChange={(event) =>
              setForm({ ...form, linked_decision_id: event.target.value })
            }
          >
            <option value="">Exploratory — no decision yet</option>
            {decisions.map((decision) => (
              <option key={decision.id} value={decision.id}>
                {decision.title}
              </option>
            ))}
          </select>

          <label htmlFor="scenario-set-owner">Accountable owner</label>
          <select
            id="scenario-set-owner"
            value={form.owner_id}
            onChange={(event) => setForm({ ...form, owner_id: event.target.value })}
          >
            <option value="">Use me</option>
            {memberships
              .filter((membership) => membership.status === "active")
              .map((membership) => (
                <option key={membership.id} value={membership.user.id}>
                  {personName(membership.user)}
                </option>
              ))}
          </select>

          <button
            className="primary-button"
            disabled={mutation.isPending || uncertainties.length < 2}
            type="submit"
          >
            {mutation.isPending ? "Creating…" : "Create scenario set"}
          </button>
        </form>
      </aside>
    </div>
  );
}
