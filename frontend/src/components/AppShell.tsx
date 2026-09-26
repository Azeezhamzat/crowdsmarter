import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";

import { fetchCurrentUser, logoutSession } from "../features/auth/api";
import { listNotifications } from "../features/notifications/api";
import { listOrganisations } from "../features/organisations/api";
import { Icon, type IconName } from "./Icon";
import { LogoMark } from "./Logo";

type CommandItem = {
  label: string;
  description: string;
  href: string;
  icon: IconName;
  group: string;
};

function initials(firstName: string, lastName: string, email: string): string {
  const value = `${firstName.slice(0, 1)}${lastName.slice(0, 1)}`.trim();
  return (value || email.slice(0, 2)).toUpperCase();
}

export function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const searchInputRef = useRef<HTMLInputElement>(null);
  const mobileMenuButtonRef = useRef<HTMLButtonElement>(null);
  const sidebarCloseButtonRef = useRef<HTMLButtonElement>(null);
  const restoreSidebarFocusRef = useRef(false);
  const commandTriggerRef = useRef<HTMLButtonElement>(null);
  const commandDialogRef = useRef<HTMLDivElement>(null);
  const restoreCommandFocusRef = useRef(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState("");
  const [commandIndex, setCommandIndex] = useState(0);

  function closeSidebar(restoreFocus = true) {
    restoreSidebarFocusRef.current = restoreFocus;
    setSidebarOpen(false);
  }

  function openSidebar() {
    restoreSidebarFocusRef.current = false;
    setSidebarOpen(true);
  }

  function closeCommand(restoreFocus = true) {
    restoreCommandFocusRef.current = restoreFocus;
    setCommandOpen(false);
  }

  function openCommand() {
    restoreCommandFocusRef.current = false;
    setCommandOpen(true);
  }

  const currentUser = useQuery({
    queryKey: ["current-user"],
    queryFn: fetchCurrentUser,
    staleTime: 60_000,
  });
  const organisations = useQuery({
    queryKey: ["organisations"],
    queryFn: listOrganisations,
    staleTime: 60_000,
  });
  const inbox = useQuery({
    queryKey: ["notifications"],
    queryFn: () => listNotifications(false),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
  const logout = useMutation({
    mutationFn: logoutSession,
    onSuccess: async () => {
      queryClient.clear();
      await navigate("/login", { replace: true });
    },
  });

  useEffect(() => {
    restoreSidebarFocusRef.current = false;
    setSidebarOpen(false);
    restoreCommandFocusRef.current = false;
    setCommandOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (sidebarOpen) {
      const focusTimer = window.setTimeout(() => sidebarCloseButtonRef.current?.focus());
      return () => window.clearTimeout(focusTimer);
    }
    if (restoreSidebarFocusRef.current) {
      const focusTimer = window.setTimeout(() => mobileMenuButtonRef.current?.focus());
      restoreSidebarFocusRef.current = false;
      return () => window.clearTimeout(focusTimer);
    }
    return undefined;
  }, [sidebarOpen]);

  useEffect(() => {
    const focusTimer = window.setTimeout(() => {
      const main = document.getElementById("main-content");
      const focusTarget = main?.querySelector<HTMLElement>("h1") ?? main;
      if (!focusTarget) return;
      if (!focusTarget.hasAttribute("tabindex")) focusTarget.setAttribute("tabindex", "-1");
      focusTarget.classList.add("route-focus-target");
      focusTarget.focus({ preventScroll: true });
    });
    return () => window.clearTimeout(focusTimer);
  }, []);

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((open) => {
          restoreCommandFocusRef.current = open;
          return !open;
        });
      }
      if (event.key === "Escape") {
        restoreCommandFocusRef.current = commandOpen;
        setCommandOpen(false);
        restoreSidebarFocusRef.current = sidebarOpen;
        setSidebarOpen(false);
      }
    }
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, [commandOpen, sidebarOpen]);

  useEffect(() => {
    if (commandOpen) {
      window.setTimeout(() => searchInputRef.current?.focus(), 30);
    } else {
      setCommandQuery("");
      setCommandIndex(0);
      if (restoreCommandFocusRef.current) {
        window.setTimeout(() => commandTriggerRef.current?.focus(), 0);
        restoreCommandFocusRef.current = false;
      }
    }
  }, [commandOpen]);

  const commandItems = useMemo<CommandItem[]>(() => {
    const basics: CommandItem[] = [
      { label: "My work", description: "Your active decisions and next actions", href: "/app", icon: "home", group: "Navigate" },
      ...(currentUser.data?.is_platform_administrator ? [{ label: "Platform administration", description: "Users, tenants, support access, decision enquiries, and service settings", href: "/platform-admin", icon: "shield" as const, group: "Administration" }] : []),
      { label: "Notifications", description: "Assignments, mentions, and workflow updates", href: "/notifications", icon: "bell", group: "Navigate" },
      { label: "Contribution inbox", description: "Assigned contributions, drafts, reviews, and due work", href: "/contributions", icon: "check", group: "Navigate" },
      { label: "Account settings", description: "Profile and password security", href: "/account", icon: "shield", group: "Navigate" },
      { label: "Public website", description: "Open the CrowdSmarter public site", href: "/", icon: "external", group: "Navigate" },
    ];
    const organisationItems = (organisations.data ?? []).flatMap((organisation) => ([
      {
        label: organisation.name,
        description: `${organisation.current_user_role} · organisation workspace`,
        href: `/organisations/${organisation.id}`,
        icon: "building" as const,
        group: "Organisations",
      },
      {
        label: `${organisation.name} prioritisation`,
        description: "Collective scoring, thresholds, and constrained portfolio choices",
        href: `/organisations/${organisation.id}/prioritisation`,
        icon: "analytics" as const,
        group: "Collective intelligence",
      },
      {
        label: `${organisation.name} foresight`,
        description: "Signals, sources, systems canvases, and strategic watchlists",
        href: `/organisations/${organisation.id}/foresight`,
        icon: "spark" as const,
        group: "Foresight",
      },
      {
        label: `${organisation.name} systems canvases`,
        description: "Drivers, causal maps, futures wheels, and implications",
        href: `/organisations/${organisation.id}/foresight/canvases`,
        icon: "layers" as const,
        group: "Foresight",
      },
      ...( ["owner", "admin"].includes(organisation.current_user_role) ? [{
        label: `${organisation.name} decision methods`,
        description: "Govern organisation-owned methods and approved versions",
        href: `/organisations/${organisation.id}/methods`,
        icon: "layers" as const,
        group: "Administration",
      }, {
        label: `${organisation.name} administration`,
        description: "Branding, invitation policy, ownership, retention, and account safeguards",
        href: `/organisations/${organisation.id}/administration`,
        icon: "shield" as const,
        group: "Administration",
      }] : []),
    ]));
    return [...basics, ...organisationItems];
  }, [organisations.data, currentUser.data?.is_platform_administrator]);

  const filteredCommands = commandItems.filter((item) => {
    const needle = commandQuery.trim().toLowerCase();
    return !needle || `${item.label} ${item.description}`.toLowerCase().includes(needle);
  });

  function handleCommandKeyDown(event: ReactKeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setCommandIndex((index) => Math.min(index + 1, Math.max(filteredCommands.length - 1, 0)));
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setCommandIndex((index) => Math.max(index - 1, 0));
    }
    const selectedCommand = filteredCommands[commandIndex];
    if (event.key === "Enter" && selectedCommand) {
      event.preventDefault();
      closeCommand(false);
      void navigate(selectedCommand.href);
    }
  }

  function handleCommandDialogKeyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (event.key !== "Tab" || !commandDialogRef.current) return;
    const focusable = Array.from(
      commandDialogRef.current.querySelectorAll<HTMLElement>(
        'input:not([disabled]), button:not([disabled]):not([tabindex="-1"]), [href]:not([tabindex="-1"])',
      ),
    );
    if (!focusable.length) return;
    const first = focusable[0]!;
    const last = focusable[focusable.length - 1]!;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  const user = currentUser.data;
  const displayName = user
    ? [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email
    : "Account";

  return (
    <div className={`app-shell app-shell--professional${sidebarOpen ? " app-shell--nav-open" : ""}`}>
      <button
        className="app-nav-backdrop"
        type="button"
        aria-label="Close navigation"
        onClick={() => closeSidebar()}
      />

      <aside id="application-sidebar" className="app-sidebar" aria-label="Primary application navigation">
        <div className="app-sidebar__brand-row">
          <Link to="/app" className="brand brand--sidebar" aria-label="CrowdSmarter application home">
            <LogoMark variant="inverse" size={34} />
            <span className="brand-copy"><strong>CrowdSmarter</strong><small>Facilitation. Systems. Collective intelligence.</small></span>
          </Link>
          <button ref={sidebarCloseButtonRef} className="icon-button app-sidebar__close" type="button" onClick={() => closeSidebar()} aria-label="Close navigation">
            <Icon name="close" />
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Workspace navigation">
          <p className="sidebar-nav__label">Workspace</p>
          <NavLink to="/app" end className={({ isActive }) => `sidebar-nav__link${isActive ? " is-active" : ""}`}>
            <Icon name="home" /><span>My work</span>
          </NavLink>
          <NavLink to="/notifications" className={({ isActive }) => `sidebar-nav__link${isActive ? " is-active" : ""}`}>
            <Icon name="bell" /><span>Notifications</span>
            {inbox.data?.unread_count ? <span className="nav-count">{inbox.data.unread_count > 99 ? "99+" : inbox.data.unread_count}</span> : null}
          </NavLink>
          <NavLink to="/contributions" className={({ isActive }) => `sidebar-nav__link${isActive ? " is-active" : ""}`}>
            <Icon name="check" /><span>Contribution inbox</span>
          </NavLink>
          {currentUser.data?.is_platform_administrator ? <NavLink to="/platform-admin" className={({ isActive }) => `sidebar-nav__link sidebar-nav__link--platform${isActive ? " is-active" : ""}`}>
            <Icon name="shield" /><span>Platform administration</span>
          </NavLink> : null}

          <p className="sidebar-nav__label sidebar-nav__label--spaced">Organisations</p>
          {organisations.isPending ? <div className="sidebar-skeleton" aria-label="Loading organisations"><span /><span /></div> : null}
          {organisations.data?.slice(0, 5).map((organisation) => (
            <NavLink
              to={`/organisations/${organisation.id}`}
              key={organisation.id}
              className={({ isActive }) => `sidebar-nav__link sidebar-nav__link--organisation${isActive ? " is-active" : ""}`}
            >
              <span className="organisation-avatar" aria-hidden="true">{organisation.name.slice(0, 1).toUpperCase()}</span>
              <span className="sidebar-nav__organisation-copy"><strong>{organisation.name}</strong><small>{organisation.current_user_role}</small></span>
            </NavLink>
          ))}
        </nav>

        <div className="app-sidebar__footer">
          <Link className="sidebar-nav__link" to="/account">
            <Icon name="shield" /><span>Account settings</span>
          </Link>
          <Link className="sidebar-nav__link" to="/" target="_blank" rel="noreferrer">
            <Icon name="external" /><span>Public website</span>
          </Link>
          <div className="sidebar-profile">
            <span className="user-avatar" aria-hidden="true">{user ? initials(user.first_name, user.last_name, user.email) : "CS"}</span>
            <span className="sidebar-profile__copy"><strong>{displayName}</strong><small>{user?.email ?? "Signed in"}</small></span>
            <button className="icon-button" type="button" onClick={() => logout.mutate()} disabled={logout.isPending} aria-label="Sign out">
              <Icon name="logout" />
            </button>
          </div>
        </div>
      </aside>

      <div className="app-frame">
        <header className="app-topbar">
          <div className="app-topbar__left">
            <button ref={mobileMenuButtonRef} className="icon-button mobile-menu-button" type="button" onClick={openSidebar} aria-label="Open navigation" aria-expanded={sidebarOpen} aria-controls="application-sidebar">
              <Icon name="menu" />
            </button>
            <button
              ref={commandTriggerRef}
              className="command-trigger"
              type="button"
              onClick={openCommand}
              aria-haspopup="dialog"
              aria-expanded={commandOpen}
              aria-controls="quick-navigation-dialog"
              aria-keyshortcuts="Control+K Meta+K"
            >
              <Icon name="search" />
              <span>Search or go to…</span>
              <kbd>⌘ K</kbd>
            </button>
          </div>
          <div className="app-topbar__right">
            <Link className="topbar-notification" to="/notifications" aria-label={`${inbox.data?.unread_count ?? 0} unread notifications`}>
              <Icon name="bell" />
              {inbox.data?.unread_count ? <span>{inbox.data.unread_count > 99 ? "99+" : inbox.data.unread_count}</span> : null}
            </Link>
            <Link className="topbar-user topbar-user--link" to="/account">
              <span className="user-avatar user-avatar--small" aria-hidden="true">{user ? initials(user.first_name, user.last_name, user.email) : "CS"}</span>
              <span><strong>{displayName}</strong><small>{user?.email ?? ""}</small></span>
            </Link>
          </div>
        </header>

        <main id="main-content" className="main-content main-content--app" tabIndex={-1}>
          <Outlet />
        </main>
      </div>

      {commandOpen ? (
        <div
          id="quick-navigation-dialog"
          ref={commandDialogRef}
          className="command-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="command-title"
          aria-describedby="command-instructions"
          onKeyDown={handleCommandDialogKeyDown}
          onMouseDown={(event) => {
            if (event.currentTarget === event.target) closeCommand();
          }}
        >
          <section className="command-palette">
            <h2 className="visually-hidden" id="command-title">Quick navigation</h2>
            <p className="visually-hidden" id="command-instructions">Type to filter destinations. Use the up and down arrow keys to choose a result, then press Enter to open it. Press Escape to close.</p>
            <div className="command-search">
              <Icon name="search" />
              <input
                ref={searchInputRef}
                role="combobox"
                aria-autocomplete="list"
                aria-expanded="true"
                aria-controls="command-results"
                aria-activedescendant={filteredCommands[commandIndex] ? `command-option-${commandIndex}` : undefined}
                value={commandQuery}
                onChange={(event) => { setCommandQuery(event.target.value); setCommandIndex(0); }}
                onKeyDown={handleCommandKeyDown}
                placeholder="Search organisations and destinations"
                aria-label="Search navigation"
              />
              <button className="icon-button command-close" type="button" onClick={() => closeCommand()} aria-label="Close quick navigation">
                <Icon name="close" size={18} />
              </button>
            </div>
            <div id="command-results" className="command-results" role="listbox" aria-label="Navigation results">
              {filteredCommands.length ? filteredCommands.map((item, index) => (
                <button
                  id={`command-option-${index}`}
                  className={`command-item${commandIndex === index ? " is-selected" : ""}`}
                  type="button"
                  role="option"
                  aria-selected={commandIndex === index}
                  tabIndex={-1}
                  key={`${item.group}-${item.href}`}
                  onMouseEnter={() => setCommandIndex(index)}
                  onClick={() => { closeCommand(false); void navigate(item.href); }}
                >
                  <span className="command-item__icon"><Icon name={item.icon} /></span>
                  <span><strong>{item.label}</strong><small>{item.description}</small></span>
                  <Icon name="arrow-right" size={17} />
                </button>
              )) : <div className="command-empty"><Icon name="search" /><p>No matching destination</p></div>}
            </div>
            <div className="visually-hidden" role="status" aria-live="polite" aria-atomic="true">
              {filteredCommands[commandIndex]
                ? `${filteredCommands[commandIndex].label}, ${commandIndex + 1} of ${filteredCommands.length}`
                : "No matching destinations"}
            </div>
            <footer className="command-footer"><span><kbd>↑</kbd><kbd>↓</kbd> navigate</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span></footer>
          </section>
        </div>
      ) : null}
    </div>
  );
}
