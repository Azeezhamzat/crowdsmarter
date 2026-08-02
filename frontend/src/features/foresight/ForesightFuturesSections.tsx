import type { Dispatch, SetStateAction } from "react";

import type { ForesightCanvasWorkspace, ForesightConsequence } from "../../lib/types";
import type { ConsequenceForm, HorizonForm } from "./canvasTypes";

export function ForesightFuturesWheelSection({
  canvas,
  grouped,
  form,
  setForm,
  submit,
}: {
  canvas: ForesightCanvasWorkspace;
  grouped: Record<1 | 2 | 3, ForesightConsequence[]>;
  form: ConsequenceForm;
  setForm: Dispatch<SetStateAction<ConsequenceForm>>;
  submit: () => void;
}) {
  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Second- and third-order effects</p>
            <h2>Futures wheel</h2>
          </div>
          <span className="role-badge">Three orders</span>
        </div>
        <div className="futures-wheel">
          <div className="futures-wheel__centre">
            <span>Focal system</span>
            <strong>{canvas.title}</strong>
          </div>
          {([1, 2, 3] as const).map((order) => (
            <section
              className={`futures-wheel__ring futures-wheel__ring--${order}`}
              key={order}
            >
              <header>
                <strong>
                  {order === 1
                    ? "First-order"
                    : order === 2
                      ? "Second-order"
                      : "Third-order"}
                </strong>
                <span>{grouped[order].length}</span>
              </header>
              <div>
                {grouped[order].map((item) => (
                  <article
                    className={`consequence-card consequence-card--${item.consequence_type}`}
                    key={item.id}
                  >
                    <div>
                      <span>{item.consequence_type_label}</span>
                      <small>
                        Likelihood {item.likelihood}/5 · Impact {item.impact}/5
                      </small>
                    </div>
                    <h3>{item.title}</h3>
                    <p>{item.description}</p>
                    {item.parent_title ? (
                      <small>Flows from: {item.parent_title}</small>
                    ) : item.originating_driver_title ? (
                      <small>Origin: {item.originating_driver_title}</small>
                    ) : null}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>

      <aside className="side-panel foresight-create-panel">
        <p className="eyebrow">Explore consequences</p>
        <h2>Add consequence</h2>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <label htmlFor="consequence-driver">Originating driver</label>
          <select
            id="consequence-driver"
            value={form.originating_driver_id}
            onChange={(event) =>
              setForm({ ...form, originating_driver_id: event.target.value })
            }
          >
            <option value="">Focal system</option>
            {canvas.drivers.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
          <label htmlFor="consequence-parent">Parent consequence</label>
          <select
            id="consequence-parent"
            value={form.parent_id}
            onChange={(event) =>
              setForm({ ...form, parent_id: event.target.value })
            }
          >
            <option value="">First-order consequence</option>
            {canvas.consequences
              .filter((item) => item.order < 3)
              .map((item) => (
                <option key={item.id} value={item.id}>
                  {"—".repeat(item.order)} {item.title}
                </option>
              ))}
          </select>
          <label htmlFor="consequence-title">Consequence</label>
          <input
            id="consequence-title"
            required
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
          <label htmlFor="consequence-description">Why might it occur?</label>
          <textarea
            id="consequence-description"
            required
            rows={5}
            value={form.description}
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
          />
          <label htmlFor="consequence-type">Interpretation</label>
          <select
            id="consequence-type"
            value={form.consequence_type}
            onChange={(event) =>
              setForm({ ...form, consequence_type: event.target.value })
            }
          >
            <option value="opportunity">Opportunity</option>
            <option value="threat">Threat</option>
            <option value="mixed">Mixed</option>
            <option value="unclear">Unclear</option>
          </select>
          <div className="form-row">
            <div>
              <label htmlFor="consequence-likelihood">Likelihood</label>
              <input
                id="consequence-likelihood"
                max="5"
                min="1"
                type="number"
                value={form.likelihood}
                onChange={(event) =>
                  setForm({ ...form, likelihood: Number(event.target.value) })
                }
              />
            </div>
            <div>
              <label htmlFor="consequence-impact">Impact</label>
              <input
                id="consequence-impact"
                max="5"
                min="1"
                type="number"
                value={form.impact}
                onChange={(event) =>
                  setForm({ ...form, impact: Number(event.target.value) })
                }
              />
            </div>
          </div>
          <button className="button button--primary button--full" type="submit">
            Add consequence
          </button>
        </form>
      </aside>
    </div>
  );
}

export function ForesightThreeHorizonsSection({
  canvas,
  form,
  setForm,
  submit,
}: {
  canvas: ForesightCanvasWorkspace;
  form: HorizonForm;
  setForm: Dispatch<SetStateAction<HorizonForm>>;
  submit: () => void;
}) {
  const horizons = [
    { key: "h1", title: "Horizon 1", subtitle: "Current system under pressure" },
    { key: "h2", title: "Horizon 2", subtitle: "Transition and innovation" },
    { key: "h3", title: "Horizon 3", subtitle: "Emerging viable future" },
  ] as const;

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Transition thinking</p>
            <h2>Three Horizons</h2>
          </div>
        </div>
        <div className="three-horizons-board">
          {horizons.map((horizon) => {
            const items = canvas.horizon_items.filter(
              (item) => item.horizon === horizon.key,
            );
            return (
              <section
                className={`horizon-column horizon-column--${horizon.key}`}
                key={horizon.key}
              >
                <header>
                  <span>{horizon.title}</span>
                  <strong>{horizon.subtitle}</strong>
                </header>
                <div>
                  {items.map((item) => (
                    <article key={item.id}>
                      <h3>{item.title}</h3>
                      <p>{item.description}</p>
                      {item.evidence ? <small>{item.evidence}</small> : null}
                    </article>
                  ))}
                  {!items.length ? <p className="muted">No items recorded.</p> : null}
                </div>
              </section>
            );
          })}
        </div>
      </section>

      <aside className="side-panel foresight-create-panel">
        <p className="eyebrow">Place change in time</p>
        <h2>Add horizon item</h2>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <label htmlFor="horizon-value">Horizon</label>
          <select
            id="horizon-value"
            value={form.horizon}
            onChange={(event) =>
              setForm({ ...form, horizon: event.target.value })
            }
          >
            <option value="h1">H1 — current system</option>
            <option value="h2">H2 — transition</option>
            <option value="h3">H3 — emerging future</option>
          </select>
          <label htmlFor="horizon-title">Title</label>
          <input
            id="horizon-title"
            required
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
          <label htmlFor="horizon-description">Description</label>
          <textarea
            id="horizon-description"
            required
            rows={5}
            value={form.description}
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
          />
          <label htmlFor="horizon-evidence">Evidence or signals</label>
          <textarea
            id="horizon-evidence"
            rows={3}
            value={form.evidence}
            onChange={(event) =>
              setForm({ ...form, evidence: event.target.value })
            }
          />
          <button className="button button--primary button--full" type="submit">
            Add horizon item
          </button>
        </form>
      </aside>
    </div>
  );
}
