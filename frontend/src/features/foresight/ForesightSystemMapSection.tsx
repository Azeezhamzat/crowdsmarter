import type { CSSProperties, Dispatch, SetStateAction } from "react";

import { Icon } from "../../components/Icon";
import type { ForesightCanvasWorkspace } from "../../lib/types";
import type { FeedbackLoopForm, RelationshipForm, StakeholderForm } from "./canvasTypes";

export function ForesightSystemMapSection({
  canvas,
  stakeholderForm,
  setStakeholderForm,
  feedbackLoopForm,
  setFeedbackLoopForm,
  relationshipForm,
  setRelationshipForm,
  createStakeholder,
  createRelationship,
  createFeedbackLoop,
}: {
  canvas: ForesightCanvasWorkspace;
  stakeholderForm: StakeholderForm;
  setStakeholderForm: Dispatch<SetStateAction<StakeholderForm>>;
  feedbackLoopForm: FeedbackLoopForm;
  setFeedbackLoopForm: Dispatch<SetStateAction<FeedbackLoopForm>>;
  relationshipForm: RelationshipForm;
  setRelationshipForm: Dispatch<SetStateAction<RelationshipForm>>;
  createStakeholder: () => void;
  createRelationship: () => void;
  createFeedbackLoop: () => void;
}) {
  return (
    <div className="system-map-layout">
      <section className="page-primary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Causal structure</p>
            <h2>Driver relationships</h2>
          </div>
          <span className="role-badge">Structured, not predictive</span>
        </div>
        <div className="causal-map" aria-label="Causal relationships">
          {canvas.relationships.map((item, index) => (
            <article
              className={`causal-link causal-link--${item.polarity}`}
              key={item.id}
              style={{ "--link-order": index } as CSSProperties}
            >
              <div className="causal-node">
                <small>Source driver</small>
                <strong>{item.source_title}</strong>
              </div>
              <div className="causal-arrow">
                <span aria-hidden="true">
                  {item.polarity === "reinforcing"
                    ? "+"
                    : item.polarity === "balancing"
                      ? "−"
                      : "?"}
                </span>
                <small>
                  {item.polarity === "reinforcing"
                    ? "amplifies"
                    : item.polarity === "balancing"
                      ? "constrains"
                      : "uncertain"}
                </small>
              </div>
              <div className="causal-node">
                <small>Target driver</small>
                <strong>{item.target_title}</strong>
              </div>
              <footer>
                Strength {item.strength}/5 · {item.delay_label}
              </footer>
              <p>{item.rationale}</p>
            </article>
          ))}
          {!canvas.relationships.length ? (
            <div className="empty-state">
              <Icon name="layers" />
              <h3>No causal relationships</h3>
              <p>
                Record an explicit mechanism between two drivers rather than drawing
                an unexplained arrow.
              </p>
            </div>
          ) : null}
        </div>

        <div className="section-heading system-stakeholder-heading">
          <div>
            <p className="eyebrow">Feedback structures</p>
            <h2>Interpreted loops</h2>
          </div>
          <span className="role-badge">{canvas.feedback_loops.length} recorded</span>
        </div>
        <div className="feedback-loop-grid">
          {canvas.feedback_loops.map((loop) => (
            <article
              className={`feedback-loop-card feedback-loop-card--${loop.loop_type}`}
              key={loop.id}
            >
              <div>
                <span className="status-badge">{loop.loop_type_label}</span>
                <strong>{loop.name}</strong>
              </div>
              <p>{loop.description}</p>
              <div className="feedback-loop-path" aria-label="Drivers in this loop">
                {loop.drivers.map((driver, index) => (
                  <span key={driver.id}>
                    {driver.title}
                    {index < loop.drivers.length - 1 ? " →" : " ↺"}
                  </span>
                ))}
              </div>
              <small>{loop.rationale}</small>
            </article>
          ))}
          {!canvas.feedback_loops.length ? (
            <p className="muted">
              No feedback loops have been interpreted yet. Record loops only when
              the causal mechanism and participating drivers can be explained.
            </p>
          ) : null}
        </div>

        <div className="section-heading system-stakeholder-heading">
          <div>
            <p className="eyebrow">Actors in the system</p>
            <h2>Influence and exposure</h2>
          </div>
        </div>
        <div className="stakeholder-matrix">
          {canvas.stakeholders.map((item) => (
            <article
              className={`stakeholder-node stakeholder-node--${item.stance}`}
              key={item.id}
              style={
                {
                  "--stakeholder-x": `${8 + (item.influence - 1) * 21}%`,
                  "--stakeholder-y": `${92 - (item.exposure - 1) * 21}%`,
                } as CSSProperties
              }
            >
              <strong>{item.name}</strong>
              <small>{item.stakeholder_type_label}</small>
              <span>
                Influence {item.influence} · Exposure {item.exposure}
              </span>
            </article>
          ))}
          <span className="matrix-axis matrix-axis--x">Influence →</span>
          <span className="matrix-axis matrix-axis--y">Exposure →</span>
        </div>
      </section>

      <aside className="side-panel foresight-create-panel systems-map-forms">
        <details open>
          <summary>Add stakeholder</summary>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              createStakeholder();
            }}
          >
            <label htmlFor="stakeholder-name">Name or actor group</label>
            <input
              id="stakeholder-name"
              required
              value={stakeholderForm.name}
              onChange={(event) =>
                setStakeholderForm({
                  ...stakeholderForm,
                  name: event.target.value,
                })
              }
            />
            <label htmlFor="stakeholder-type">Type</label>
            <select
              id="stakeholder-type"
              value={stakeholderForm.stakeholder_type}
              onChange={(event) =>
                setStakeholderForm({
                  ...stakeholderForm,
                  stakeholder_type: event.target.value,
                })
              }
            >
              <option value="internal">Internal</option>
              <option value="customer">Customer or beneficiary</option>
              <option value="partner">Partner</option>
              <option value="regulator">Regulator or government</option>
              <option value="community">Community</option>
              <option value="competitor">Competitor</option>
              <option value="other">Other</option>
            </select>
            <label htmlFor="stakeholder-role">Role in the system</label>
            <textarea
              id="stakeholder-role"
              required
              rows={3}
              value={stakeholderForm.role}
              onChange={(event) =>
                setStakeholderForm({
                  ...stakeholderForm,
                  role: event.target.value,
                })
              }
            />
            <label htmlFor="stakeholder-interests">Interests and incentives</label>
            <textarea
              id="stakeholder-interests"
              required
              rows={3}
              value={stakeholderForm.interests}
              onChange={(event) =>
                setStakeholderForm({
                  ...stakeholderForm,
                  interests: event.target.value,
                })
              }
            />
            <div className="form-row">
              <div>
                <label htmlFor="stakeholder-influence">Influence</label>
                <input
                  id="stakeholder-influence"
                  max="5"
                  min="1"
                  type="number"
                  value={stakeholderForm.influence}
                  onChange={(event) =>
                    setStakeholderForm({
                      ...stakeholderForm,
                      influence: Number(event.target.value),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="stakeholder-exposure">Exposure</label>
                <input
                  id="stakeholder-exposure"
                  max="5"
                  min="1"
                  type="number"
                  value={stakeholderForm.exposure}
                  onChange={(event) =>
                    setStakeholderForm({
                      ...stakeholderForm,
                      exposure: Number(event.target.value),
                    })
                  }
                />
              </div>
            </div>
            <label htmlFor="stakeholder-stance">Current stance</label>
            <select
              id="stakeholder-stance"
              value={stakeholderForm.stance}
              onChange={(event) =>
                setStakeholderForm({
                  ...stakeholderForm,
                  stance: event.target.value,
                })
              }
            >
              <option value="supportive">Supportive</option>
              <option value="neutral">Neutral</option>
              <option value="resistant">Resistant</option>
              <option value="mixed">Mixed</option>
              <option value="unclear">Unclear</option>
            </select>
            <button className="button button--secondary button--full" type="submit">
              Add stakeholder
            </button>
          </form>
        </details>

        <details open>
          <summary>Connect drivers</summary>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              createRelationship();
            }}
          >
            <label htmlFor="relationship-source">Source driver</label>
            <select
              id="relationship-source"
              required
              value={relationshipForm.source_driver_id}
              onChange={(event) =>
                setRelationshipForm({
                  ...relationshipForm,
                  source_driver_id: event.target.value,
                })
              }
            >
              <option value="">Choose driver</option>
              {canvas.drivers.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title}
                </option>
              ))}
            </select>
            <label htmlFor="relationship-target">Target driver</label>
            <select
              id="relationship-target"
              required
              value={relationshipForm.target_driver_id}
              onChange={(event) =>
                setRelationshipForm({
                  ...relationshipForm,
                  target_driver_id: event.target.value,
                })
              }
            >
              <option value="">Choose driver</option>
              {canvas.drivers.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title}
                </option>
              ))}
            </select>
            <label htmlFor="relationship-polarity">Relationship</label>
            <select
              id="relationship-polarity"
              value={relationshipForm.polarity}
              onChange={(event) =>
                setRelationshipForm({
                  ...relationshipForm,
                  polarity: event.target.value,
                })
              }
            >
              <option value="reinforcing">Reinforcing</option>
              <option value="balancing">Balancing</option>
              <option value="uncertain">Uncertain</option>
            </select>
            <div className="form-row">
              <div>
                <label htmlFor="relationship-strength">Strength</label>
                <input
                  id="relationship-strength"
                  max="5"
                  min="1"
                  type="number"
                  value={relationshipForm.strength}
                  onChange={(event) =>
                    setRelationshipForm({
                      ...relationshipForm,
                      strength: Number(event.target.value),
                    })
                  }
                />
              </div>
              <div>
                <label htmlFor="relationship-delay">Delay</label>
                <select
                  id="relationship-delay"
                  value={relationshipForm.delay}
                  onChange={(event) =>
                    setRelationshipForm({
                      ...relationshipForm,
                      delay: event.target.value,
                    })
                  }
                >
                  <option value="immediate">Immediate</option>
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="long">Long</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
            </div>
            <label htmlFor="relationship-rationale">Causal rationale</label>
            <textarea
              id="relationship-rationale"
              required
              rows={4}
              value={relationshipForm.rationale}
              onChange={(event) =>
                setRelationshipForm({
                  ...relationshipForm,
                  rationale: event.target.value,
                })
              }
            />
            <button className="button button--primary button--full" type="submit">
              Connect drivers
            </button>
          </form>
        </details>

        <details>
          <summary>Record feedback loop</summary>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              createFeedbackLoop();
            }}
          >
            <label htmlFor="feedback-loop-name">Loop name</label>
            <input
              id="feedback-loop-name"
              required
              value={feedbackLoopForm.name}
              onChange={(event) =>
                setFeedbackLoopForm({
                  ...feedbackLoopForm,
                  name: event.target.value,
                })
              }
            />
            <label htmlFor="feedback-loop-description">Behaviour over time</label>
            <textarea
              id="feedback-loop-description"
              required
              rows={4}
              value={feedbackLoopForm.description}
              onChange={(event) =>
                setFeedbackLoopForm({
                  ...feedbackLoopForm,
                  description: event.target.value,
                })
              }
            />
            <label htmlFor="feedback-loop-type">Loop type</label>
            <select
              id="feedback-loop-type"
              value={feedbackLoopForm.loop_type}
              onChange={(event) =>
                setFeedbackLoopForm({
                  ...feedbackLoopForm,
                  loop_type: event.target.value,
                })
              }
            >
              <option value="reinforcing">Reinforcing</option>
              <option value="balancing">Balancing</option>
              <option value="mixed">Mixed</option>
              <option value="uncertain">Uncertain</option>
            </select>
            <label htmlFor="feedback-loop-drivers">Drivers in sequence</label>
            <select
              id="feedback-loop-drivers"
              multiple
              required
              value={feedbackLoopForm.driver_ids}
              onChange={(event) =>
                setFeedbackLoopForm({
                  ...feedbackLoopForm,
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
            <small>Select at least two drivers. Order follows the selection list.</small>
            <label htmlFor="feedback-loop-rationale">Evidence and rationale</label>
            <textarea
              id="feedback-loop-rationale"
              required
              rows={4}
              value={feedbackLoopForm.rationale}
              onChange={(event) =>
                setFeedbackLoopForm({
                  ...feedbackLoopForm,
                  rationale: event.target.value,
                })
              }
            />
            <button className="button button--secondary button--full" type="submit">
              Record feedback loop
            </button>
          </form>
        </details>
      </aside>
    </div>
  );
}
