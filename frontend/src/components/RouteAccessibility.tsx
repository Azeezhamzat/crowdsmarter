import { useEffect, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";
import { Outlet, useLocation } from "react-router-dom";

const PRODUCT_NAME = "The CrowdSmarter";

const routeTitles: Array<[RegExp, string]> = [
  [/^\/$/, "Foresight-to-decision intelligence"],
  [/^\/request-demo\/?$/, "Request a tailored demo"],
  [/^\/login\/?$/, "Sign in"],
  [/^\/forgot-password\/?$/, "Reset your password"],
  [/^\/reset-password\/?$/, "Choose a new password"],
  [/^\/accept-invitation\/?$/, "Accept organisation invitation"],
  [/^\/app\/?$/, "My work"],
  [/^\/notifications\/?$/, "Notifications"],
  [/^\/contributions\/?$/, "Contribution inbox"],
  [/^\/account\/?$/, "Account settings"],
  [/^\/platform-admin\/?$/, "Platform administration"],
  [/^\/platform-admin\/organisations\/[^/]+\/?$/, "Tenant support workspace"],
  [/^\/organisations\/[^/]+\/administration\/?$/, "Organisation administration"],
  [/^\/organisations\/[^/]+\/methods\/?$/, "Decision methods"],
  [/^\/organisations\/[^/]+\/workspaces\/?$/, "Workspaces"],
  [/^\/organisations\/[^/]+\/search\/?$/, "Organisation search"],
  [/^\/organisations\/[^/]+\/analytics\/?$/, "Organisation analytics"],
  [/^\/organisations\/[^/]+\/portfolio\/?$/, "Decision portfolio"],
  [/^\/organisations\/[^/]+\/prioritisation\/?$/, "Collective prioritisation"],
  [/^\/organisations\/[^/]+\/export\/?$/, "Organisation export"],
  [/^\/organisations\/[^/]+\/foresight\/canvases\/[^/]+\/scenarios\/[^/]+\/?$/, "Scenario set"],
  [/^\/organisations\/[^/]+\/foresight\/canvases\/[^/]+\/?$/, "Foresight canvas"],
  [/^\/organisations\/[^/]+\/foresight\/canvases\/?$/, "Systems canvases"],
  [/^\/organisations\/[^/]+\/foresight\/?$/, "Strategic foresight"],
  [/^\/organisations\/[^/]+\/audit\/?$/, "Audit history"],
  [/^\/organisations\/[^/]+\/?$/, "Organisation workspace"],
  [/^\/workspaces\/[^/]+\/decisions\/new\/?$/, "Create a decision"],
  [/^\/workspaces\/[^/]+\/?$/, "Workspace"],
  [/^\/decisions\/[^/]+\/governance\/?$/, "Decision governance"],
  [/^\/decisions\/[^/]+\/evaluations\/?$/, "Collective evaluation"],
  [/^\/decisions\/[^/]+\/analysis\/?$/, "Decision analysis"],
  [/^\/decisions\/[^/]+\/outcomes\/?$/, "Implementation and outcomes"],
  [/^\/decisions\/[^/]+\/ai-review\/?$/, "AI review"],
  [/^\/decisions\/[^/]+\/collaboration\/?$/, "Decision collaboration"],
  [/^\/decisions\/[^/]+\/contributions\/?$/, "Decision contributions"],
  [/^\/decisions\/[^/]+\/reasoning\/[^/]+\/?$/, "Decision reasoning"],
  [/^\/decisions\/[^/]+\/?$/, "Decision workspace"],
];

function titleForPath(pathname: string): string {
  return routeTitles.find(([pattern]) => pattern.test(pathname))?.[1] ?? "Page not found";
}

export function RouteAccessibility() {
  const location = useLocation();
  const previousPath = useRef(location.pathname);
  const [announcement, setAnnouncement] = useState("");

  useEffect(() => {
    const title = titleForPath(location.pathname);
    document.title = `${title} — ${PRODUCT_NAME}`;
    setAnnouncement(title);

    const pathChanged = previousPath.current !== location.pathname;
    previousPath.current = location.pathname;
    if (!pathChanged) return;

    const focusTimer = window.setTimeout(() => {
      const main = document.querySelector<HTMLElement>("main#main-content, main[role='main'], main");
      if (!main) return;
      const focusTarget = main.querySelector<HTMLElement>("h1") ?? main;
      if (!focusTarget.hasAttribute("tabindex")) focusTarget.setAttribute("tabindex", "-1");
      focusTarget.classList.add("route-focus-target");
      focusTarget.focus({ preventScroll: true });
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    });

    return () => window.clearTimeout(focusTimer);
  }, [location.pathname]);

  function handleSkipLink(event: ReactMouseEvent<HTMLAnchorElement>) {
    const main = document.getElementById("main-content");
    if (!main) return;
    event.preventDefault();
    if (!main.hasAttribute("tabindex")) main.setAttribute("tabindex", "-1");
    main.focus({ preventScroll: true });
    main.scrollIntoView({ block: "start", behavior: "auto" });
  }

  return (
    <>
      <a className="skip-link" href="#main-content" onClick={handleSkipLink}>Skip to main content</a>
      <div className="route-announcer visually-hidden" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>
      <Outlet />
    </>
  );
}
