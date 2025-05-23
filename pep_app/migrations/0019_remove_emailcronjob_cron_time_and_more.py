# Generated by Django 5.1.7 on 2025-04-26 08:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pep_app', '0018_remove_emailcronjob_specific_date_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailcronjob',
            name='cron_time',
        ),
        migrations.RemoveField(
            model_name='emailcronjob',
            name='frequency',
        ),
        migrations.AddField(
            model_name='emailcronjob',
            name='email_category',
            field=models.ForeignKey(blank=True, help_text='Select the email category', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cron_jobs', to='pep_app.emailtemplatecategory'),
        ),
        migrations.AddField(
            model_name='emailcronjob',
            name='partner',
            field=models.ForeignKey(blank=True, help_text='Partner associated with this cron job', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cron_jobs', to='pep_app.partners'),
        ),
        migrations.AlterField(
            model_name='emailcronjob',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='User who created the cron job', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_cron_jobs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='emailcronjob',
            name='end_date',
            field=models.DateField(help_text='End date in UTC. Cron job will stop running after this date.'),
        ),
        migrations.AlterField(
            model_name='emailcronjob',
            name='start_date',
            field=models.DateField(help_text='Start date in UTC. Cron job will start checking for contacts from this date.'),
        ),
    ]
