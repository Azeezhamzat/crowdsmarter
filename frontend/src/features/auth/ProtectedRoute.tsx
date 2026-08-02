import { useQuery } from "@tanstack/react-query";
import { Navigate, useLocation } from "react-router-dom";

import { AppShell } from "../../components/AppShell";
import { ApiError } from "../../lib/api";
import { fetchCurrentUser } from "./api";

export function ProtectedRoute() {
  const location = useLocation();
  const currentUser = useQuery({
    queryKey: ["current-user"],
    queryFn: fetchCurrentUser,
    retry: false,
    staleTime: 60_000,
  });

  if (currentUser.isPending) {
    return <main id="main-content" className="centred-state" tabIndex={-1} aria-busy="true">Loading your workspace…</main>;
  }

  if (currentUser.error instanceof ApiError && currentUser.error.status === 403) {
    const next = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }

  if (currentUser.isError) {
    return <main id="main-content" className="centred-state" tabIndex={-1} role="alert">The application could not verify your session.</main>;
  }

  return <AppShell />;
}
