# Generated by Django 5.2 on 2025-04-25 04:26

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_api', '0006_alter_tourpackage_last_booking_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='tourbooking',
            name='tracking_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]
