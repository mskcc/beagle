from django.db import migrations

METADATA_KEY = "genePanel"

def migrate_recipe_data(apps, schema_editor):
    Operator = apps.get_model("runner", "Operator")
    for op in Operator.objects.all():
        val = op.recipes
        op.recipes_json = {METADATA_KEY: [val] if val else []}
        op.save(update_fields=["recipes_json"])

class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0040_auto_20250603_1607"),
    ]

    operations = [
        migrations.RunPython(migrate_recipe_data, reverse_code=migrations.RunPython.noop),
    ]
