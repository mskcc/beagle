from django.db import migrations

def forwards(apps, schema_editor):
    Operator = apps.get_model("beagle_etl", "Operator")
    for op in Operator.objects.all():
        op.recipes_json = {"genePanel": op.recipes or []}
        op.save(update_fields=["recipes_json"])

class Migration(migrations.Migration):

    dependencies = [
        ('beagle_etl', '0039_auto_20250603_1635'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
