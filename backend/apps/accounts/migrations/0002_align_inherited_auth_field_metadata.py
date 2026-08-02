"""Align inherited Django authentication field metadata with the model state."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Complete inherited help text omitted from the initial migration."""

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="groups",
            field=models.ManyToManyField(
                blank=True,
                help_text=(
                    "The groups this user belongs to. A user will get all permissions "
                    "granted to each of their groups."
                ),
                related_name="user_set",
                related_query_name="user",
                to="auth.group",
                verbose_name="groups",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "Designates whether this user should be treated as active. "
                    "Unselect this instead of deleting accounts."
                ),
                verbose_name="active",
            ),
        ),
    ]
