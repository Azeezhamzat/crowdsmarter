# Phase 3.0.1 model metadata hotfix

This hotfix replaces model-level check-constraint comprehensions that referred to nested `TextChoices` classes from inside Django model `Meta` classes. Python does not make the enclosing model class namespace directly available inside the nested `Meta` class body, which caused Django startup to fail with `NameError: name 'Status' is not defined`.

The correction uses explicit, migration-aligned values in the model constraints. It changes no database records and introduces no schema difference from the existing Phase 3 migrations.
