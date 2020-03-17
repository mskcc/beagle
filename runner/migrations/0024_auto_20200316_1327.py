# Generated by Django 2.2.9 on 2020-03-16 13:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notifier', '0001_initial'),
        ('runner', '0023_merge_20200227_1441'),
    ]

    operations = [
        migrations.AddField(
            model_name='operatorrun',
            name='job_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='notifier.JobGroup'),
        ),
        migrations.AddField(
            model_name='run',
            name='job_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='notifier.JobGroup'),
        ),
    ]
