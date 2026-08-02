import { useEffect, useState } from "react";

import { Icon, type IconName } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import type { ForesightCanvasWorkspace, Membership } from "../../lib/types";
import type { CanvasSettingsForm, CanvasTab } from "./canvasTypes";
import { personName } from "./canvasTypes";

export function ForesightCanvasOverview({
  canvas,
  isSaving,
  memberships,
  save,
  setTab,
}: {
  canvas: ForesightCanvasWorkspace;
  isSaving: boolean;
  memberships: Membership[];
  save: (input: Record<string, unknown>) => void;
  setTab: (tab: CanvasTab) => void;
}) {
  const priorities = [...canvas.drivers]
    .sort((a, b) => b.attention_score - a.attention_score)
    .slice(0, 4);
  const [settings, setSettings] = useState<CanvasSettingsForm>({
    title: canvas.title,
    focal_question: canvas.focal_question,
    scope: canvas.scope,
    horizon_year: canvas.horizon_year,
    owner_id: canvas.owner.id,
    status: canvas.status,
  });

  useEffect(() => {
    setSettings({
      title: canvas.title,
      focal_question: canvas.focal_question,
      scope: canvas.scope,
      horizon_year: canvas.horizon_year,
      owner_id: canvas.owner.id,
      status: canvas.status,
    });
  }, [canvas]);

  return (
    <div className="foresight-overview-grid">
      <section className="page-primary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Strategic interpretation</p>
            <h2>What deserves attention</h2>
          </div>
        </div>
        <div className="foresight-attention-list">
          {priorities.map((driver) => (
            <button key={driver.id} onClick={() => setTab("drivers")} type="button">
              <span
                className={`attention-ring attention-ring--${
                  driver.attention_score >= 16 ? "high" : "normal"
                }`}
              >
                {driver.attention_score}
              </span>
              <span>
                <strong>{driver.title}</strong>
                <small>
                  {driver.driver_type_label} · {driver.steep_label} ·{" "}
                  {driver.direction_label}
                </small>
              </span>
              <Icon name="arrow-right" size={17} />
            </button>
          ))}
          {!priorities.length ? (
            <div className="empty-state">
              <Icon name="activity" />
              <h3>Interpret your first driver</h3>
              <p>Move from isolated signals to the forces shaping the system.</p>
            </div>
          ) : null}
        </div>
      </section>

      <aside className="side-panel">
        <p className="eyebrow">Canvas readiness</p>
        <h2>Next useful work</h2>
        <div className="canvas-next-actions">
          <CanvasAction
            icon="activity"
            label="Drivers"
            detail={
              canvas.drivers.length
                ? `${canvas.drivers.length} recorded`
                : "Synthesize signals"
            }
            onClick={() => setTab("drivers")}
          />
          <CanvasAction
            icon="layers"
            label="System relationships"
            detail={
              canvas.relationships.length
                ? `${canvas.relationships.length} causal links`
                : "Map feedback and actors"
            }
            onClick={() => setTab("system")}
          />
          <CanvasAction
            icon="spark"
            label="Consequences"
            detail={
              canvas.consequences.length
                ? `${canvas.consequences.length} explored`
                : "Explore second-order effects"
            }
            onClick={() => setTab("wheel")}
          />
          <CanvasAction
            icon="decision"
            label="Strategic implications"
            detail={
              canvas.summary.open_implication_count
                ? `${canvas.summary.open_implication_count} open`
                : "Translate insight into choice"
            }
            onClick={() => setTab("implications")}
          />
        </div>

        <details className="canvas-governance" open={canvas.status === "draft"}>
          <summary>Canvas governance</summary>
          {canvas.can_edit ? (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                save(settings);
              }}
            >
              <label htmlFor="canvas-settings-title">Title</label>
              <input
                id="canvas-settings-title"
                required
                value={settings.title}
                onChange={(event) =>
                  setSettings({ ...settings, title: event.target.value })
                }
              />
              <label htmlFor="canvas-settings-question">Focal question</label>
              <textarea
                id="canvas-settings-question"
                required
                rows={4}
                value={settings.focal_question}
                onChange={(event) =>
                  setSettings({
                    ...settings,
                    focal_question: event.target.value,
                  })
                }
              />
              <label htmlFor="canvas-settings-scope">Scope and boundary</label>
              <textarea
                id="canvas-settings-scope"
                required
                rows={4}
                value={settings.scope}
                onChange={(event) =>
                  setSettings({ ...settings, scope: event.target.value })
                }
              />
              <div className="form-row">
                <div>
                  <label htmlFor="canvas-settings-horizon">Horizon year</label>
                  <input
                    id="canvas-settings-horizon"
                    max="2200"
                    min="2000"
                    type="number"
                    value={settings.horizon_year}
                    onChange={(event) =>
                      setSettings({
                        ...settings,
                        horizon_year: Number(event.target.value),
                      })
                    }
                  />
                </div>
                <div>
                  <label htmlFor="canvas-settings-status">Status</label>
                  <select
                    id="canvas-settings-status"
                    value={settings.status}
                    onChange={(event) =>
                      setSettings({ ...settings, status: event.target.value })
                    }
                  >
                    <option value="draft">Draft</option>
                    <option value="active">Active</option>
                    <option value="complete">Complete</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>
              <label htmlFor="canvas-settings-owner">Accountable owner</label>
              <select
                id="canvas-settings-owner"
                value={settings.owner_id}
                onChange={(event) =>
                  setSettings({ ...settings, owner_id: event.target.value })
                }
              >
                {memberships
                  .filter((item) => item.status === "active")
                  .map((item) => (
                    <option key={item.user.id} value={item.user.id}>
                      {personName(item.user)}
                    </option>
                  ))}
              </select>
              {settings.status === "archived" ? (
                <StatusMessage kind="warning">
                  Archiving makes the canvas and all its mapping records read-only.
                </StatusMessage>
              ) : null}
              <button
                className="button button--secondary button--full"
                disabled={isSaving}
                type="submit"
              >
                {isSaving ? "Saving…" : "Save canvas settings"}
              </button>
            </form>
          ) : (
            <p className="muted">This canvas is read-only or managed by another owner.</p>
          )}
        </details>
      </aside>
    </div>
  );
}

function CanvasAction({
  icon,
  label,
  detail,
  onClick,
}: {
  icon: IconName;
  label: string;
  detail: string;
  onClick: () => void;
}) {
  return (
    <button onClick={onClick} type="button">
      <Icon name={icon} />
      <span>
        <strong>{label}</strong>
        <small>{detail}</small>
      </span>
    </button>
  );
}
