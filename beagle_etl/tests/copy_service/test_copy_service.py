from django.test import TestCase
from beagle_etl.copy_service import CopyService


class JobViewTest(TestCase):

    def setUp(self):
        self.mapping = dict()
        self.recipe = 'IMPACT468'
        self.mapping['IMPACT468'] = {'/path/to': '/new/path/to'}
        # patch.dict('os.environ', {'BEAGLE_COPY_MAPPING': "{'IMPACT468': {'/path/to':'/default/path/to'}}"})

    def test_remap(self):
        old_path = '/path/to/file/file1.fastq'
        new_path = CopyService.remap(self.recipe, old_path, self.mapping)
        self.assertEqual(new_path, '/new/path/to/file/file1.fastq')

    def test_remap_no_mapping(self):
        old_path = '/some/other/path/to/file/file1.fastq'
        new_path = CopyService.remap(self.recipe, old_path, self.mapping)
        self.assertEqual(new_path, old_path)
