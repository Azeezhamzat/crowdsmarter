import type { Dispatch, SetStateAction } from "react";
import { Link } from "react-router";

import { Icon } from "../../components/Icon";
import type { ForesightCanvasWorkspace, Membership, PortfolioDecision } from "../../lib/types";
import type { ImplicationForm } from "./canvasTypes";
import { personName } from "./canvasTypes";

export function ForesightImplicationsSection({
  canvas,
  form,
  setForm,
  memberships,
  decisions,
  submit,
  updateStatus,
}: {
  canvas: ForesightCanvasWorkspace;
  form: ImplicationForm;
  setForm: Dispatch<SetStateAction<ImplicationForm>>;
  memberships: Membership[];
  decisions: PortfolioDecision[];
  submit: () => void;
  updateStatus: (id: string, status: string) => void;
}) {
  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">From insight to choice</p>
            <h2>Strategic implications</h2>
          </div>
          <span className="role-badge">Human interpretation</span>
        </div>
        <div className="implication-grid">
          {canvas.implications.map((item) => (
            <article
              className={`implication-card implication-card--${item.implication_type}`}
              key={item.id}
            >
              <div className="implication-card__top">
                <div className="inline-badges">
                  <span className="status-badge">
                    {item.implication_type_label}
                  </span>
                  <span className="role-badge">Priority {item.priority}/5</span>
                </div>
                <select
                  aria-label={`Status for ${item.title}`}
                  disabled={!item.can_edit}
                  value={item.status}
                  onChange={(event) => updateStatus(item.id, event.target.value)}
                >
                  <option value="open">Open</option>
                  <option value="addressed">Addressed</option>
                  <option value="dismissed">Dismissed</option>
                </select>
              </div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              {item.drivers.length ? (
                <div className="implication-drivers">
                  <strong>Grounded in</strong>
                  {item.drivers.map((driver) => (
                    <span key={driver.id}>{driver.title}</span>
                  ))}
                </div>
              ) : null}
              <footer>
                <span>Owner: {personName(item.owner)}</span>
                {item.linked_decision_id ? (
                  <Link to={`/decisions/${item.linked_decision_id}`}>
                    {item.linked_decision_title}
                  </Link>
                ) : (
                  <span>No decision linked</span>
                )}
              </footer>
            </article>
          ))}
          {!canvas.implications.length ? (
            <div className="empty-state">
              <Icon name="decision" />
              <h3>No strategic implications</h3>
              <p>
                Translate the foresight analysis into opportunities, threats,
                capability needs, policies, or new decisions.
              </p>
            </div>
          ) : null}
        </div>
      </section>

      <aside className="side-panel foresight-create-panel">
        <p className="eyebrow">Strategic interpretation</p>
        <h2>Add implication</h2>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <label htmlFor="implication-title">Title</label>
          <input
            id="implication-title"
            required
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
          <label htmlFor="implication-description">Description</label>
          <textarea
            id="implication-description"
            required
            rows={5}
            value={form.description}
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
          />
          <label htmlFor="implication-type">Type</label>
          <select
            id="implication-type"
            value={form.implication_type}
            onChange={(event) =>
              setForm({ ...form, implication_type: event.target.value })
            }
          >
            <option value="opportunity">Opportunity</option>
            <option value="threat">Threat</option>
            <option value="capability">Capability requirement</option>
            <option value="decision_requirement">Decision requirement</option>
            <option value="policy">Policy implication</option>
          </select>
          <label htmlFor="implication-priority">Priority (1–5)</label>
          <input
            id="implication-priority"
            max="5"
            min="1"
            type="number"
            value={form.priority}
            onChange={(event) =>
              setForm({ ...form, priority: Number(event.target.value) })
            }
          />
          <label htmlFor="implication-drivers">Grounded in drivers</label>
          <select
            id="implication-drivers"
            multiple
            value={form.driver_ids}
            onChange={(event) =>
              setForm({
                ...form,
                driver_ids: Array.from(
                  event.currentTarget.selectedOptions,
                  (option) => option.value,
                ),
              })
            }
          >
            {canvas.drivers.map((driver) => (
              <option key={driver.id} value={driver.id}>
                {driver.title}
              </option>
            ))}
          </select>
          <small>Hold Ctrl or Command to select more than one.</small>
          <label htmlFor="implication-owner">Owner</label>
          <select
            id="implication-owner"
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
          <label htmlFor="implication-decision">Connect to decision</label>
          <select
            id="implication-decision"
            value={form.linked_decision_id}
            onChange={(event) =>
              setForm({ ...form, linked_decision_id: event.target.value })
            }
          >
            <option value="">No decision yet</option>
            {decisions.map((decision) => (
              <option key={decision.id} value={decision.id}>
                {decision.title}
              </option>
            ))}
          </select>
          <button className="button button--primary button--full" type="submit">
            Add implication
          </button>
        </form>
      </aside>
    </div>
  );
}
