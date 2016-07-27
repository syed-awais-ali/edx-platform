# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='version',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='cert_html_view_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='days_early_for_beta',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='enrollment_start',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='enrollment_end',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='enrollment_domain',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='invitation_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='max_student_enrollments_allowed',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='announcement',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='catalog_visibility',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='course_video_url',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='effort',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='short_description',
            field=models.TextField(null=True),
        ),
    ]
