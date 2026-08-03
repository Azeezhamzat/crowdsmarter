import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { listMemberships } from "../organisations/api";
import { createForesightCanvas, listForesightCanvases } from "./api";

function personName(user: { first_name: string; last_name: string; email: string }): string {
  return [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email;
}

export function ForesightCanvasesPage() {
  const { organisationId = "" } = useParams<{ organisationId: string }>();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    title: "",
    focal_question: "",
    scope: "",
    horizon_year: new Date().getFullYear() + 10,
    owner_id: "",
    status: "draft",
  });

  const canvases = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "canvases"],
    queryFn: () => listForesightCanvases(organisationId),
    enabled: Boolean(organisationId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", organisationId, "memberships"],
    queryFn: () => listMemberships(organisationId),
    enabled: Boolean(organisationId),
  });
  const create = useMutation({
    mutationFn: () => createForesightCanvas(organisationId, {
      ...form,
      owner_id: form.owner_id || undefined,
    }),
    onSuccess: async () => {
      setForm({
        title: "",
        focal_question: "",
        scope: "",
        horizon_year: new Date().getFullYear() + 10,
        owner_id: "",
        status: "draft",
      });
      await queryClient.invalidateQueries({
        queryKey: ["organisations", organisationId, "foresight", "canvases"],
      });
    },
  });

  return (
    <div className="foresight-canvas-index">
      <Link className="back-link" to={`/organisations/${organisationId}/foresight`}>← Signal intelligence</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Interpret · systems foresight</p>
          <h1>Foresight canvases</h1>
          <p className="muted">Turn signals into drivers, causal relationships, consequences, transition pathways, and decision implications.</p>
        </div>
      </div>

      {canvases.isError ? <StatusMessage kind="error">The foresight canvases could not be loaded.</StatusMessage> : null}
      {create.isError ? <StatusMessage kind="error">{create.error instanceof ApiError ? create.error.message : "The canvas could not be created."}</StatusMessage> : null}

      <div className="reasoning-grid foresight-canvas-index__grid">
        <section className="page-primary">
          <div className="section-heading">
            <div><p className="eyebrow">Structured inquiries</p><h2>Active canvases</h2></div>
            <span className="role-badge">{canvases.data?.length ?? 0} total</span>
          </div>
          <div className="foresight-canvas-list">
            {canvases.data?.map((canvas) => (
              <Link className="foresight-canvas-card" key={canvas.id} to={`/organisations/${organisationId}/foresight/canvases/${canvas.id}`}>
                <div className="foresight-canvas-card__top">
                  <span className={`status-badge status-badge--${canvas.status}`}>{canvas.status_label}</span>
                  <span className="role-badge">Horizon {canvas.horizon_year}</span>
                </div>
                <h3>{canvas.title}</h3>
                <p>{canvas.focal_question}</p>
                <div className="foresight-canvas-card__meta">
                  <span><Icon name="activity" /> {canvas.driver_count} drivers</span>
                  <span><Icon name="decision" /> {canvas.implication_count} implications</span>
                  <span><Icon name="users" /> {personName(canvas.owner)}</span>
                </div>
                <span className="foresight-canvas-card__action">Open canvas <Icon name="arrow-right" size={17} /></span>
              </Link>
            ))}
            {!canvases.isPending && !canvases.data?.length ? (
              <div className="empty-state"><Icon name="spark" /><h3>No foresight canvas yet</h3><p>Create one around a focal question that matters strategically.</p></div>
            ) : null}
          </div>
        </section>

        <aside className="side-panel foresight-create-panel">
          <p className="eyebrow">Bound the inquiry</p>
          <h2>Create a canvas</h2>
          <form onSubmit={(event) => { event.preventDefault(); create.mutate(); }}>
            <label htmlFor="canvas-title">Canvas title</label>
            <input id="canvas-title" required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Future of regional food systems" />
            <label htmlFor="canvas-question">Focal question</label>
            <textarea id="canvas-question" rows={4} required value={form.focal_question} onChange={(event) => setForm({ ...form, focal_question: event.target.value })} placeholder="How might changes in climate, technology and farmer demographics reshape…?" />
            <label htmlFor="canvas-scope">System boundary and scope</label>
            <textarea id="canvas-scope" rows={5} required value={form.scope} onChange={(event) => setForm({ ...form, scope: event.target.value })} placeholder="Geography, sectors, actors, exclusions and assumptions…" />
            <div className="form-row">
              <div><label htmlFor="canvas-horizon">Horizon year</label><input id="canvas-horizon" type="number" min="2000" max="2200" required value={form.horizon_year} onChange={(event) => setForm({ ...form, horizon_year: Number(event.target.value) })} /></div>
              <div><label htmlFor="canvas-status">Status</label><select id="canvas-status" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option value="draft">Draft</option><option value="active">Active</option></select></div>
            </div>
            <label htmlFor="canvas-owner">Accountable owner</label>
            <select id="canvas-owner" value={form.owner_id} onChange={(event) => setForm({ ...form, owner_id: event.target.value })}>
              <option value="">Me</option>
              {memberships.data?.filter((item) => item.status === "active").map((item) => <option key={item.user.id} value={item.user.id}>{personName(item.user)}</option>)}
            </select>
            <button className="button button--primary button--full" disabled={create.isPending} type="submit">{create.isPending ? "Creating…" : "Create foresight canvas"}</button>
          </form>
        </aside>
      </div>
    </div>
  );
}
