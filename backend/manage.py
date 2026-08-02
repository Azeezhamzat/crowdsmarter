#!/usr/bin/env python
"""Django's command-line utility."""

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crowdsmarter.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django is not installed or not available on PYTHONPATH.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
