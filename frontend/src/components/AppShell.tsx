import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { fetchCurrentUser, logoutSession } from "../features/auth/api";
import { listNotifications } from "../features/notifications/api";
import { listOrganisations } from "../features/organisations/api";
import { Icon, type IconName } from "./Icon";

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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState("");
  const [commandIndex, setCommandIndex] = useState(0);

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
    setSidebarOpen(false);
    setCommandOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((open) => !open);
      }
      if (event.key === "Escape") {
        setCommandOpen(false);
        setSidebarOpen(false);
      }
    }
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  useEffect(() => {
    if (commandOpen) {
      window.setTimeout(() => searchInputRef.current?.focus(), 30);
    } else {
      setCommandQuery("");
      setCommandIndex(0);
    }
  }, [commandOpen]);

  const commandItems = useMemo<CommandItem[]>(() => {
    const basics: CommandItem[] = [
      { label: "My work", description: "Your active decisions and next actions", href: "/app", icon: "home", group: "Navigate" },
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
  }, [organisations.data]);

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
      navigate(selectedCommand.href);
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
        onClick={() => setSidebarOpen(false)}
      />

      <aside className="app-sidebar" aria-label="Primary application navigation">
        <div className="app-sidebar__brand-row">
          <Link to="/app" className="brand brand--sidebar" aria-label="The CrowdSmarter application home">
            <span className="brand-mark brand-mark--premium" aria-hidden="true"><span /><span /><span /></span>
            <span className="brand-copy"><strong>The CrowdSmarter</strong><small>Decision intelligence</small></span>
          </Link>
          <button className="icon-button app-sidebar__close" type="button" onClick={() => setSidebarOpen(false)} aria-label="Close navigation">
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
            <button className="icon-button mobile-menu-button" type="button" onClick={() => setSidebarOpen(true)} aria-label="Open navigation">
              <Icon name="menu" />
            </button>
            <button className="command-trigger" type="button" onClick={() => setCommandOpen(true)}>
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

        <main className="main-content main-content--app">
          <Outlet />
        </main>
      </div>

      {commandOpen ? (
        <div className="command-overlay" role="dialog" aria-modal="true" aria-labelledby="command-title" onMouseDown={(event) => {
          if (event.currentTarget === event.target) setCommandOpen(false);
        }}>
          <section className="command-palette">
            <h2 className="visually-hidden" id="command-title">Quick navigation</h2>
            <div className="command-search">
              <Icon name="search" />
              <input
                ref={searchInputRef}
                value={commandQuery}
                onChange={(event) => { setCommandQuery(event.target.value); setCommandIndex(0); }}
                onKeyDown={handleCommandKeyDown}
                placeholder="Search organisations and destinations"
                aria-label="Search navigation"
              />
              <kbd>Esc</kbd>
            </div>
            <div className="command-results">
              {filteredCommands.length ? filteredCommands.map((item, index) => (
                <button className={`command-item${commandIndex === index ? " is-selected" : ""}`} type="button" key={`${item.group}-${item.href}`} onMouseEnter={() => setCommandIndex(index)} onClick={() => navigate(item.href)}>
                  <span className="command-item__icon"><Icon name={item.icon} /></span>
                  <span><strong>{item.label}</strong><small>{item.description}</small></span>
                  <Icon name="arrow-right" size={17} />
                </button>
              )) : <div className="command-empty"><Icon name="search" /><p>No matching destination</p></div>}
            </div>
            <footer className="command-footer"><span><kbd>↑</kbd><kbd>↓</kbd> navigate</span><span><kbd>Enter</kbd> open</span></footer>
          </section>
        </div>
      ) : null}
    </div>
  );
}
