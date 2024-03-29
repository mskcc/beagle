# Generated by Django 2.2.8 on 2020-01-22 18:19

import django.contrib.postgres.fields
from django.db import migrations, models


def add_operators(apps, _):
    Operator = apps.get_model("beagle_etl", "Operator")

    Operator.objects.all().delete()

    Operator.objects.create(
        slug="tempo",
        class_name="TempoOperator",
        recipes=["Agilent_51MB", "HumanWholeGenome", "ShallowWGS", "WholeExomeSequencing"],
        active=True,
    )

    Operator.objects.create(
        slug="argos",
        class_name="ArgosOperator",
        recipes=["IMPACT341", "IMPACT+ (341 genes plus custom content)", "IMPACT410", "IMPACT468"],
        active=True,
    )

    Operator.objects.create(slug="access", class_name="AccessOperator", recipes=["MSK-ACCESS_v1"], active=True)


def remove_operators(apps, _):
    Operator = apps.get_model("beagle_etl", "Operator")

    Operator.objects.filter(class_name__in=["ArgosOperator", "AccessOperator", "TempoOperator"]).delete()

    Operator.objects.create(active=True, recipes=["None"], class_name="None")


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0011_auto_20191209_2319"),
    ]

    operations = [
        migrations.AddField(
            model_name="operator",
            name="class_name",
            field=models.CharField(default="None", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="operator",
            name="slug",
            field=models.CharField(default="None", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="operator",
            name="recipes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(default=False, max_length=50), default=["None"], size=None
            ),
            preserve_default=False,
        ),
        migrations.RunPython(add_operators, remove_operators),
    ]
