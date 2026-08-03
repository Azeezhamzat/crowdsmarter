import type { DecisionStatus, DecisionTransitionAvailability } from "../../lib/types";
import { decisionLifecycle } from "./lifecycle";

export function DecisionLifecycle({
  currentStatus,
  nextTransition,
}: {
  currentStatus: DecisionStatus;
  nextTransition: DecisionTransitionAvailability | null;
}) {
  const currentIndex = decisionLifecycle.findIndex((item) => item.status === currentStatus);

  return (
    <section className="lifecycle-panel" aria-labelledby="lifecycle-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Governed progression</p>
          <h2 id="lifecycle-title">Decision lifecycle</h2>
        </div>
        {nextTransition && !nextTransition.enabled ? (
          <span className="status-badge status-badge--blocked">Future phase required</span>
        ) : null}
      </div>
      <ol className="lifecycle-list" tabIndex={0} aria-label="Decision lifecycle stages, scrollable">
        {decisionLifecycle.map((item, index) => {
          const state = index < currentIndex ? "complete" : index === currentIndex ? "current" : "future";
          return (
            <li className={`lifecycle-step lifecycle-step--${state}`} key={item.status}>
              <span className="lifecycle-marker" aria-hidden="true">
                {index < currentIndex ? "✓" : index + 1}
              </span>
              <span>{item.label}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
