# Generated by Django 2.2.8 on 2020-01-02 18:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('file_system', '0011_filetype_valid_extensions'),
    ]

    def slugify_title(apps, schema_editor):
        '''
        We can't import the Post model directly as it may be a newer
        version than this migration expects. We use the historical version.
        '''
        File = apps.get_model('file_system', 'File')
        file1 = File.objects.get(
            path='/juno/work/taylorlab/cmopipeline//mskcc-igenomes/grch37/baits/AgilentExon_51MB_b37_v3_baits.interval_list')
        file1.path = '/juno/work/taylorlab/cmopipeline/mskcc-igenomes/grch37/baits/AgilentExon_51MB_b37_v3_baits.interval_list'
        file1.save()
        file2 = File.objects.get(
            path='/juno/work/taylorlab/cmopipeline//mskcc-igenomes/grch37/targets/AgilentExon_51MB_b37_v3_targets.plus5bp.bed.gz')
        file2.path = '/juno/work/taylorlab/cmopipeline/mskcc-igenomes/grch37/targets/AgilentExon_51MB_b37_v3_targets.plus5bp.bed.gz'
        file2.save()
        file3 = File.objects.get(
            path='/juno/work/taylorlab/cmopipeline//mskcc-igenomes/grch37/targets/AgilentExon_51MB_b37_v3_targets.plus5bp.bed.gz.tbi')
        file3.path = '/juno/work/taylorlab/cmopipeline/mskcc-igenomes/grch37/targets/AgilentExon_51MB_b37_v3_targets.plus5bp.bed.gz.tbi'
        file3.save()
        file4 = File.objects.get(
            path='/juno/work/taylorlab/cmopipeline//mskcc-igenomes/grch37/targets/AgilentExon_51MB_b37_v3_targets.interval_list')
        file4.path = '/juno/work/taylorlab/cmopipeline/mskcc-igenomes/grch37/targets/AgilentExon_51MB_b37_v3_targets.interval_list'
        file4.save()

    operations = [
    ]
