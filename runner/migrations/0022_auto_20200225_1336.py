# Generated by Django 2.2.9 on 2020-02-25 18:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0021_auto_20200221_2231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pipeline',
            name='operator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='beagle_etl.Operator'),
        ),
    ]
