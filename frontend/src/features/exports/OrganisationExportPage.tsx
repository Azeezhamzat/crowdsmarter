import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getOrganisation } from "../organisations/api";
import { downloadOrganisationExport } from "./api";

export function OrganisationExportPage() {
  const { organisationId = "" } = useParams<{ organisationId: string }>();
  const organisation = useQuery({ queryKey: ["organisations", organisationId], queryFn: () => getOrganisation(organisationId), enabled: Boolean(organisationId) });
  const download = useMutation({ mutationFn: () => downloadOrganisationExport(organisationId) });
  const canExport = ["owner", "admin"].includes(organisation.data?.current_user_role ?? "");

  return (
    <div>
      <Link className="back-link" to={`/organisations/${organisationId}`}>← Organisation</Link>
      <div className="page-heading"><div><p className="eyebrow">Customer data ownership</p><h1>Export organisation data</h1><p className="muted">Download a portable copy of the complete CrowdSmarter tenant record.</p></div></div>
      <section className="export-hero" aria-labelledby="export-title">
        <span className="export-hero__icon"><Icon name="external" size={28} /></span>
        <div><h2 id="export-title">Complete organisation archive</h2><p>The ZIP contains versioned JSON for every governed domain, CSV copies of key registers, and a single multi-sheet Excel workbook. Password hashes and invitation token digests are excluded.</p></div>
        <button className="button button--primary" type="button" onClick={() => download.mutate()} disabled={!canExport || download.isPending}>{download.isPending ? "Preparing archive…" : "Download complete export"}</button>
      </section>
      {!canExport && organisation.data ? <StatusMessage kind="error">Only organisation owners and administrators may download the complete tenant archive.</StatusMessage> : null}
      {download.error ? <StatusMessage kind="error">{download.error instanceof ApiError ? download.error.message : "The export failed."}</StatusMessage> : null}
      {download.data ? <StatusMessage kind="success">Downloaded {download.data}</StatusMessage> : null}
      <div className="export-detail-grid">
        <article className="overview-card"><h2>Included</h2><ul className="trust-list"><li>Organisations, members, workspaces, and decisions</li><li>Options, evidence, assumptions, risks, and positions</li><li>Finalisations, implementation reviews, and lessons</li><li>Discussion, advisory reviews, invitations, and audit events</li></ul></article>
        <article className="overview-card"><h2>Format and safeguards</h2><ul className="trust-list"><li>Portable ZIP with JSON, CSV, and an Excel workbook</li><li>UTC timestamps and stable record identifiers</li><li>A content fingerprint (SHA-256) to confirm two exports match</li><li>No password or reusable invitation secrets</li><li>Every download is recorded in the audit log</li></ul></article>
      </div>
    </div>
  );
}
