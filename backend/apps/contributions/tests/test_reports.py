import pytest

from apps.contributions.reports import build_facilitation_report_html
from apps.contributions.services import (
    create_facilitation_record,
    create_session,
    save_facilitation_authority_response,
    update_session_status,
)


@pytest.mark.django_db
def test_printable_report_redacts_confidential_offline_identity(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status="open_for_contribution", title="Community services")
    session = create_session(
        actor=decision.owner,
        decision=decision,
        title="Access workshop",
        objective="Understand access barriers.",
        influence_boundary="Service access and communication choices.",
        fixed_constraints="Existing statutory duties.",
        participation_channels=["in_person", "phone"],
    )
    session = update_session_status(actor=decision.owner, session=session, status="open")
    create_facilitation_record(
        actor=decision.owner,
        session=session,
        kind="participant_statement",
        body="Telephone access is unreliable in the evenings.",
        channel="phone",
        origin="participant_input",
        attribution="confidential",
        speaker_label="Sensitive participant identity",
    )
    session = update_session_status(actor=decision.owner, session=session, status="closed")
    save_facilitation_authority_response(
        actor=decision.owner,
        session=session,
        what_we_heard="Evening telephone access is unreliable.",
        what_changed="A daytime callback route will be added.",
        what_did_not_change="",
        rationale="",
        next_steps="Test the callback route with the next participant group.",
        publish=True,
    )

    report = build_facilitation_report_html(session).decode("utf-8")

    assert "CrowdSmarter facilitation record" in report
    assert "Evening telephone access is unreliable." in report
    assert "Confidential participant input" in report
    assert "Sensitive participant identity" not in report
    assert "Save as PDF" in report
