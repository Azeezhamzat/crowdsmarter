import type { ReactNode } from "react";

type StatusMessageProps = {
  kind: "error" | "success" | "info" | "warning";
  children: ReactNode;
};

export function StatusMessage({ kind, children }: StatusMessageProps) {
  return (
    <div className={`status-message status-message--${kind}`} role={kind === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}
