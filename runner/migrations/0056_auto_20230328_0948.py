# Generated by Django 2.2.28 on 2023-03-28 09:48

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0055_auto_20230112_1159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='executionevents',
            name='id',
            field=models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='operatorerrors',
            name='id',
            field=models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='operatorrun',
            name='id',
            field=models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='operatortrigger',
            name='id',
            field=models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='id',
            field=models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='port',
            name='id',
            field=models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='run',
            name='id',
            field=models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False),
        ),
    ]
