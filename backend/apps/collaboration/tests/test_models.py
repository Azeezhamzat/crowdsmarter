import pytest
from django.core.exceptions import ValidationError

from apps.collaboration.models import DiscussionEntry


@pytest.mark.django_db
def test_reply_must_share_decision(decision_factory):  # type: ignore[no-untyped-def]
    first = decision_factory()
    second = decision_factory()
    parent = DiscussionEntry.objects.create(
        organisation=first.organisation,
        decision=first,
        author=first.owner,
        kind=DiscussionEntry.Kind.NOTE,
        body="First decision note.",
    )
    reply = DiscussionEntry(
        organisation=second.organisation,
        decision=second,
        author=second.owner,
        kind=DiscussionEntry.Kind.NOTE,
        body="Invalid reply.",
        reply_to=parent,
    )
    with pytest.raises(ValidationError, match="same decision"):
        reply.full_clean()
