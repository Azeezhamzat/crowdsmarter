from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial")]

    operations = [
        migrations.RemoveConstraint(
            model_name="notification",
            name="notification_kind_valid",
        ),
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("assignment", "Assignment"),
                    ("lifecycle", "Lifecycle"),
                    ("review_due", "Review Due"),
                    ("ai_review", "AI Review"),
                    ("membership", "Membership"),
                    ("collaboration", "Collaboration"),
                    ("system", "System"),
                ],
                max_length=30,
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    kind__in=[
                        "assignment",
                        "lifecycle",
                        "review_due",
                        "ai_review",
                        "membership",
                        "collaboration",
                        "system",
                    ]
                ),
                name="notification_kind_valid",
            ),
        ),
    ]
