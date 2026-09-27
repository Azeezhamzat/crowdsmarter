"""Printable, shareable facilitation reports built from governed session records."""

from __future__ import annotations

from html import escape

from django.utils import timezone

from .models import (
    FacilitationAuthorityResponse,
    FacilitationQualityReview,
    FacilitationRecord,
    FacilitationSession,
)


def _text(value: str) -> str:
    return escape(value or "Not recorded.").replace("\n", "<br>")


def _person_name(user) -> str:  # type: ignore[no-untyped-def]
    return " ".join(filter(None, [user.first_name, user.last_name])) or user.email


def _record_source(record: FacilitationRecord, *, include_confidential_identities: bool) -> str:
    if record.origin == FacilitationRecord.Origin.FACILITATOR_SYNTHESIS:
        return "Facilitator synthesis"
    if record.attribution == FacilitationRecord.Attribution.ANONYMOUS:
        return "Anonymous participant input"
    if (
        record.attribution == FacilitationRecord.Attribution.CONFIDENTIAL
        and not include_confidential_identities
    ):
        return "Confidential participant input"
    if record.speaker_label:
        return record.speaker_label
    if record.source_participant_id:
        return record.source_participant.display_label
    return record.get_attribution_display()


def build_facilitation_report_html(
    session: FacilitationSession, *, include_confidential_identities: bool = False
) -> bytes:
    """Return a self-contained HTML report suitable for printing or Save as PDF."""
    records = list(
        session.records.select_related(
            "agenda_item", "source_participant__user", "created_by"
        ).all()
    )
    agenda_items = list(session.agenda_items.prefetch_related("records").all())
    participants = list(session.participants.select_related("user").all())
    try:
        response = session.authority_response
    except FacilitationAuthorityResponse.DoesNotExist:
        response = None
    try:
        quality_review = session.quality_review
    except FacilitationQualityReview.DoesNotExist:
        quality_review = None

    channel_labels = dict(FacilitationSession.Channel.choices)
    channels = (
        ", ".join(
            channel_labels.get(channel, channel) for channel in session.participation_channels
        )
        or "Not recorded"
    )
    date_text = (
        timezone.localtime(session.starts_at).strftime("%d %B %Y, %H:%M")
        if session.starts_at
        else "Not scheduled"
    )
    attendance_rows = (
        "".join(
            "<tr>"
            f"<td>{escape(item.display_label)}</td>"
            f"<td>{escape(item.get_role_display())}</td>"
            f"<td>{escape(item.get_attendance_display())}</td>"
            "</tr>"
            for item in participants
        )
        or '<tr><td colspan="3">No named participants recorded.</td></tr>'
    )
    agenda_rows = (
        "".join(
            "<tr>"
            f"<td>{item.order}. {escape(item.title)}</td>"
            f"<td>{escape(item.method or 'Not recorded')}</td>"
            f"<td>{item.planned_minutes}</td>"
            f"<td>{item.actual_minutes if item.actual_minutes is not None else '—'}</td>"
            f"<td>{escape(item.get_status_display())}</td>"
            f"<td>{item.records.count()}</td>"
            "</tr>"
            for item in agenda_items
        )
        or '<tr><td colspan="6">No structured run-of-show was recorded.</td></tr>'
    )
    record_cards = (
        "".join(
            '<article class="record">'
            f"<h3>{escape(item.get_kind_display())}</h3>"
            f"<p>{_text(item.body)}</p>"
            "<dl>"
            f"<div><dt>Source</dt><dd>{escape(_record_source(item, include_confidential_identities=include_confidential_identities))}</dd></div>"
            f"<div><dt>Agenda item</dt><dd>{escape(item.agenda_item.title if item.agenda_item_id else 'Not linked')}</dd></div>"
            f"<div><dt>Channel</dt><dd>{escape(item.get_channel_display())}</dd></div>"
            f"<div><dt>Permission to quote</dt><dd>{'Yes' if item.permission_to_quote else 'No'}</dd></div>"
            f"<div><dt>Follow-up owner</dt><dd>{escape(item.follow_up_owner or 'Not assigned')}</dd></div>"
            "</dl></article>"
            for item in records
        )
        or "<p>No structured session records have been captured.</p>"
    )

    if response:
        response_html = (
            f'<p class="response-status">{escape(response.get_status_display())} authority response</p>'
            f"<h3>What we heard</h3><p>{_text(response.what_we_heard)}</p>"
            f"<h3>What changed</h3><p>{_text(response.what_changed)}</p>"
            f"<h3>What did not change</h3><p>{_text(response.what_did_not_change)}</p>"
            f"<h3>Why</h3><p>{_text(response.rationale)}</p>"
            f"<h3>What happens next</h3><p>{_text(response.next_steps)}</p>"
        )
    else:
        response_html = "<p>The accountable authority has not yet issued a response.</p>"

    if quality_review:
        quality_html = (
            f'<p class="response-status">Overall quality {quality_review.overall_score}/5</p>'
            "<dl>"
            f"<div><dt>Inclusion</dt><dd>{quality_review.inclusion_score}/5</dd></div>"
            f"<div><dt>Boundary clarity</dt><dd>{quality_review.clarity_score}/5</dd></div>"
            f"<div><dt>Facilitator neutrality</dt><dd>{quality_review.neutrality_score}/5</dd></div>"
            f"<div><dt>Meaningful participation</dt><dd>{quality_review.participation_score}/5</dd></div>"
            f"<div><dt>Follow-through</dt><dd>{quality_review.follow_through_score}/5</dd></div>"
            "</dl>"
            f"<h3>What worked</h3><p>{_text(quality_review.what_worked)}</p>"
            f"<h3>Improve next time</h3><p>{_text(quality_review.improve_next_time)}</p>"
            f"<h3>Unresolved risks</h3><p>{_text(quality_review.unresolved_risks)}</p>"
        )
    else:
        quality_html = "<p>No post-session quality review has been recorded.</p>"

    generated_at = timezone.localtime(timezone.now()).strftime("%d %B %Y, %H:%M %Z")
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{escape(session.title)} — facilitation report</title>
<style>
@page {{ size: A4; margin: 18mm; }}
:root {{ color-scheme: light; font-family: Inter, Arial, sans-serif; color: #14251f; }}
body {{ max-width: 920px; margin: 0 auto; line-height: 1.55; font-size: 14px; }}
header {{ border-bottom: 4px solid #176b52; padding-bottom: 18px; margin-bottom: 24px; }}
.eyebrow, dt {{ color: #176b52; font-size: 11px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ font-size: 30px; line-height: 1.15; margin: 6px 0; }} h2 {{ margin-top: 28px; }} h3 {{ margin-bottom: 5px; }}
.meta, dl {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
.meta div, .record, .response {{ border: 1px solid #cfdad5; border-radius: 10px; padding: 12px; break-inside: avoid; }}
.meta strong, dd {{ display: block; margin: 3px 0 0; }}
section {{ break-inside: avoid-page; }} .record {{ margin: 10px 0; }} .record p {{ white-space: normal; }}
dl {{ margin-bottom: 0; }} dl div {{ min-width: 0; }} dd {{ margin-left: 0; overflow-wrap: anywhere; }}
table {{ width: 100%; border-collapse: collapse; }} th, td {{ text-align: left; border-bottom: 1px solid #dce4e0; padding: 8px; }}
.response {{ border-left: 5px solid #176b52; }} .response-status {{ font-weight: 800; color: #176b52; }}
footer {{ margin-top: 32px; padding-top: 12px; border-top: 1px solid #cfdad5; color: #52645d; font-size: 11px; }}
@media print {{ body {{ max-width: none; }} .screen-note {{ display: none; }} }}
@media (max-width: 620px) {{ .meta, dl {{ grid-template-columns: 1fr; }} body {{ padding: 16px; }} }}
</style></head><body>
<p class="screen-note">This report is print-ready. Use your browser's Print command and choose “Save as PDF”.</p>
<header><p class="eyebrow">CrowdSmarter facilitation record</p><h1>{escape(session.title)}</h1><p>{escape(session.decision.title)}</p></header>
<div class="meta"><div><span class="eyebrow">Date</span><strong>{escape(date_text)}</strong></div><div><span class="eyebrow">Facilitator</span><strong>{escape(_person_name(session.facilitator))}</strong></div><div><span class="eyebrow">Status</span><strong>{escape(session.get_status_display())}</strong></div><div><span class="eyebrow">Participation channels</span><strong>{escape(channels)}</strong></div></div>
<section><h2>Session brief</h2><h3>Objective</h3><p>{_text(session.objective)}</p><h3>What participants could influence</h3><p>{_text(session.influence_boundary)}</p><h3>Fixed constraints</h3><p>{_text(session.fixed_constraints)}</p><h3>Accessibility arrangements</h3><p>{_text(session.accessibility_arrangements)}</p><h3>Consent and attribution boundary</h3><p>{_text(session.consent_boundary)}</p><h3>Participation guidance</h3><p>{_text(session.participation_guidance)}</p><h3>Agenda</h3><p>{_text(session.agenda)}</p><h3>Missing perspectives</h3><p>{_text(session.missing_perspectives)}</p></section>
<section><h2>Run of show</h2><table><thead><tr><th>Agenda item</th><th>Method</th><th>Planned min</th><th>Actual min</th><th>Status</th><th>Records</th></tr></thead><tbody>{agenda_rows}</tbody></table></section>
<section><h2>Attendance</h2><table><thead><tr><th>Participant</th><th>Role</th><th>Attendance</th></tr></thead><tbody>{attendance_rows}</tbody></table></section>
<section><h2>What the session produced</h2>{record_cards}</section>
<section><h2>Facilitator quality review</h2><div class="response">{quality_html}</div></section>
<section><h2>Authority feedback loop</h2><div class="response">{response_html}</div></section>
<footer>Generated by CrowdSmarter on {escape(generated_at)}. Session ID: {session.id}. Decision ID: {session.decision_id}.</footer>
</body></html>"""
    return document.encode("utf-8")
