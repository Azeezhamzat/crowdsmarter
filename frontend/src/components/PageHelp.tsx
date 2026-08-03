import type { ReactNode } from "react";

export function PageHelp({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="page-help">
      <summary>{title}</summary>
      <div className="page-help__body">{children}</div>
    </details>
  );
}
