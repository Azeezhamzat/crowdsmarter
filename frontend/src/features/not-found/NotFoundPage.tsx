import { Link } from "react-router";

import { Icon } from "../../components/Icon";
import { LogoMark } from "../../components/Logo";

export function NotFoundPage() {
  return (
    <div className="public-site public-site--executive not-found-page">
      <header className="public-header public-header--executive">
        <Link className="public-brand" to="/" aria-label="CrowdSmarter home">
          <LogoMark size={38} />
          <span><strong>CrowdSmarter</strong><small>Foresight. Collective intelligence. Decisions.</small></span>
        </Link>
        <div className="public-header__actions">
          <Link className="public-nav__signin" to="/login">Sign in</Link>
          <Link className="public-button public-button--primary public-header__demo" to="/request-demo">Request a demo</Link>
        </div>
      </header>
      <main id="main-content" className="not-found-page__main" tabIndex={-1}>
        <div className="not-found-page__card">
          <span className="not-found-page__icon" aria-hidden="true"><Icon name="search" size={28} /></span>
          <p className="public-eyebrow">Page not found</p>
          <h1>That destination is not part of this workspace.</h1>
          <p>The address may be incomplete, outdated, or unavailable to this account.</p>
          <div className="not-found-page__actions">
            <Link className="public-button public-button--primary public-button--large" to="/">Return to the public site</Link>
            <Link className="public-button public-button--secondary public-button--large" to="/app">Open my work</Link>
          </div>
        </div>
      </main>
    </div>
  );
}
