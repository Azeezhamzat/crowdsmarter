import type { Dispatch, FormEvent, SetStateAction } from "react";
import { Link } from "react-router-dom";

import { Icon } from "../../components/Icon";
import type { ForesightCanvasWorkspace, Membership } from "../../lib/types";
import type { DriverForm, SignalLinkForm } from "./canvasTypes";
import { personName, scoreLabel, STEEP_CATEGORIES } from "./canvasTypes";

export function ForesightDriversSection({
  canvas,
  form,
  isSaving,
  memberships,
  organisationId,
  setForm,
  setSignalLink,
  signalLink,
  signals,
  submit,
  submitSignal,
}: {
  canvas: ForesightCanvasWorkspace;
  form: DriverForm;
  isSaving: boolean;
  memberships: Membership[];
  organisationId: string;
  setForm: Dispatch<SetStateAction<DriverForm>>;
  setSignalLink: Dispatch<SetStateAction<SignalLinkForm>>;
  signalLink: SignalLinkForm;
  signals: Array<{ id: string; title: string }>;
  submit: () => void;
  submitSignal: (driverId: string, signalId: string, rationale: string) => void;
}) {
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit();
  };

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Forces of change</p>
            <h2>Drivers and uncertainties</h2>
          </div>
          <span className="role-badge">Impact × uncertainty</span>
        </div>
        <div className="driver-grid">
          {canvas.drivers.map((driver) => {
            const currentLink = signalLink[driver.id] ?? {
              signalId: "",
              rationale: "",
            };
            return (
              <article
                className={`driver-card driver-card--${driver.driver_type}`}
                key={driver.id}
              >
                <div className="driver-card__top">
                  <div className="inline-badges">
                    <span className="status-badge">{driver.driver_type_label}</span>
                    <span className="role-badge">{driver.steep_label}</span>
                  </div>
                  <strong>
                    {driver.attention_score}
                    <small>{scoreLabel(driver.attention_score)}</small>
                  </strong>
                </div>
                <h3>{driver.title}</h3>
                <p>{driver.description}</p>
                <div className="driver-card__metrics">
                  <span>Impact {driver.impact}/5</span>
                  <span>Uncertainty {driver.uncertainty}/5</span>
                  <span>{driver.direction_label}</span>
                </div>
                {driver.linked_signals.length ? (
                  <div className="driver-signals">
                    <strong>Signal evidence</strong>
                    {driver.linked_signals.map((signal) => (
                      <Link
                        key={signal.id}
                        to={`/organisations/${organisationId}/foresight?signal=${signal.id}`}
                      >
                        {signal.title}
                      </Link>
                    ))}
                  </div>
                ) : null}
                <details className="driver-linker">
                  <summary>Connect signal evidence</summary>
                  <select
                    aria-label={`Signal for ${driver.title}`}
                    value={currentLink.signalId}
                    onChange={(event) =>
                      setSignalLink((current) => ({
                        ...current,
                        [driver.id]: {
                          signalId: event.target.value,
                          rationale: currentLink.rationale,
                        },
                      }))
                    }
                  >
                    <option value="">Choose signal</option>
                    {signals
                      .filter(
                        (signal) =>
                          !driver.linked_signals.some(
                            (linked) => linked.id === signal.id,
                          ),
                      )
                      .map((signal) => (
                        <option key={signal.id} value={signal.id}>
                          {signal.title}
                        </option>
                      ))}
                  </select>
                  <textarea
                    aria-label={`Link rationale for ${driver.title}`}
                    placeholder="How does this signal support or challenge the driver?"
                    rows={2}
                    value={currentLink.rationale}
                    onChange={(event) =>
                      setSignalLink((current) => ({
                        ...current,
                        [driver.id]: {
                          signalId: currentLink.signalId,
                          rationale: event.target.value,
                        },
                      }))
                    }
                  />
                  <button
                    className="button button--quiet"
                    disabled={!currentLink.signalId || !currentLink.rationale.trim()}
                    onClick={() =>
                      submitSignal(
                        driver.id,
                        currentLink.signalId,
                        currentLink.rationale,
                      )
                    }
                    type="button"
                  >
                    Link signal
                  </button>
                </details>
              </article>
            );
          })}
          {!canvas.drivers.length ? (
            <div className="empty-state">
              <Icon name="activity" />
              <h3>No drivers yet</h3>
              <p>
                Synthesise signals into the forces and uncertainties shaping the
                focal system.
              </p>
            </div>
          ) : null}
        </div>
      </section>

      <aside className="side-panel foresight-create-panel">
        <p className="eyebrow">Interpret change</p>
        <h2>Add driver</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="driver-title">Title</label>
          <input
            id="driver-title"
            required
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
          <label htmlFor="driver-description">Description and mechanism</label>
          <textarea
            id="driver-description"
            required
            rows={5}
            value={form.description}
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
          />
          <div className="form-row">
            <div>
              <label htmlFor="driver-type">Type</label>
              <select
                id="driver-type"
                value={form.driver_type}
                onChange={(event) =>
                  setForm({ ...form, driver_type: event.target.value })
                }
              >
                <option value="trend">Trend</option>
                <option value="driver">Driver of change</option>
                <option value="critical_uncertainty">Critical uncertainty</option>
                <option value="predetermined">Predetermined element</option>
                <option value="wild_card">Wild card</option>
              </select>
            </div>
            <div>
              <label htmlFor="driver-steep">STEEP</label>
              <select
                id="driver-steep"
                value={form.steep_category}
                onChange={(event) =>
                  setForm({ ...form, steep_category: event.target.value })
                }
              >
                {STEEP_CATEGORIES.map((item) => (
                  <option key={item} value={item}>
                    {item.charAt(0).toUpperCase() + item.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <label htmlFor="driver-direction">Direction</label>
          <select
            id="driver-direction"
            value={form.direction}
            onChange={(event) =>
              setForm({ ...form, direction: event.target.value })
            }
          >
            <option value="increasing">Increasing</option>
            <option value="decreasing">Decreasing</option>
            <option value="stable">Stable</option>
            <option value="volatile">Volatile</option>
            <option value="unclear">Unclear</option>
          </select>
          <div className="form-row">
            <div>
              <label htmlFor="driver-impact">Impact (1–5)</label>
              <input
                id="driver-impact"
                max="5"
                min="1"
                type="number"
                value={form.impact}
                onChange={(event) =>
                  setForm({ ...form, impact: Number(event.target.value) })
                }
              />
            </div>
            <div>
              <label htmlFor="driver-uncertainty">Uncertainty (1–5)</label>
              <input
                id="driver-uncertainty"
                max="5"
                min="1"
                type="number"
                value={form.uncertainty}
                onChange={(event) =>
                  setForm({ ...form, uncertainty: Number(event.target.value) })
                }
              />
            </div>
          </div>
          <label htmlFor="driver-owner">Owner</label>
          <select
            id="driver-owner"
            value={form.owner_id}
            onChange={(event) =>
              setForm({ ...form, owner_id: event.target.value })
            }
          >
            <option value="">Me</option>
            {memberships
              .filter((item) => item.status === "active")
              .map((item) => (
                <option key={item.user.id} value={item.user.id}>
                  {personName(item.user)}
                </option>
              ))}
          </select>
          <button
            className="button button--primary button--full"
            disabled={isSaving}
            type="submit"
          >
            {isSaving ? "Adding…" : "Add driver"}
          </button>
        </form>
      </aside>
    </div>
  );
}
