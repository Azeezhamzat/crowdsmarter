from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contributions", "0002_hybrid_facilitation_feedback"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sessionparticipant",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="facilitation_participations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="sessionparticipant",
            name="external_label",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="sessionparticipant",
            name="stakeholder_group",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddConstraint(
            model_name="sessionparticipant",
            constraint=models.CheckConstraint(
                condition=models.Q(user__isnull=False) | ~models.Q(external_label=""),
                name="session_participant_identity_present",
            ),
        ),
        migrations.AddConstraint(
            model_name="sessionparticipant",
            constraint=models.UniqueConstraint(
                condition=~models.Q(external_label=""),
                fields=("session", "external_label"),
                name="one_external_label_per_session",
            ),
        ),
    ]
