# Generated by Django 5.2 on 2025-04-25 21:53

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_api', '0008_alter_tourbooking_tracking_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='tourpackage',
            name='tracking_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]
