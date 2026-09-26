from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_climate_resilience_seed_is_blocked_outside_debug():
    with pytest.raises(CommandError, match="disabled unless DJANGO_DEBUG=true"):
        call_command(
            "seed_climate_resilience_commons",
            dry_run=True,
            stdout=StringIO(),
        )
