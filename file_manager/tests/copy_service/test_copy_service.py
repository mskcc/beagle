from django.test import TestCase
from file_manager.copy_service.copy_service import CopyService


class CopyServiceTest(TestCase):
    def setUp(self):
        self.mapping = dict()
        self.recipe = "IMPACT468"
        self.mapping["IMPACT468"] = {"/path/to": "/new/path/to"}
        # patch.dict('os.environ', {'BEAGLE_COPY_MAPPING': "{'IMPACT468': {'/path/to':'/default/path/to'}}"})

    def test_remap(self):
        old_path = "/path/to/file/file1.fastq"
        new_path = CopyService.remap(self.recipe, old_path, self.mapping)
        self.assertEqual(new_path, "/new/path/to/file/file1.fastq")

    def test_remap_no_mapping(self):
        old_path = "/some/other/path/to/file/file1.fastq"
        new_path = CopyService.remap(self.recipe, old_path, self.mapping)
        self.assertEqual(new_path, old_path)

    def test_remap_multiple_prefixes(self):
        """Test that remap handles multiple path prefixes correctly"""
        mapping = {
            "IMPACT468": {
                "/path/to/source1": "/staging/dest1",
                "/path/to/source2": "/staging/dest2",
            }
        }

        path1 = "/path/to/source1/file1.fastq"
        new_path1 = CopyService.remap(self.recipe, path1, mapping)
        self.assertEqual(new_path1, "/staging/dest1/file1.fastq")

        path2 = "/path/to/source2/file2.fastq"
        new_path2 = CopyService.remap(self.recipe, path2, mapping)
        self.assertEqual(new_path2, "/staging/dest2/file2.fastq")

    def test_remap_different_recipe(self):
        """Test that remap only applies mappings for the correct recipe"""
        mapping = {
            "IMPACT468": {"/path/to": "/staging/impact"},
            "HEMEPACT": {"/path/to": "/staging/heme"},
        }

        path = "/path/to/file.fastq"
        new_path_impact = CopyService.remap("IMPACT468", path, mapping)
        self.assertEqual(new_path_impact, "/staging/impact/file.fastq")

        new_path_heme = CopyService.remap("HEMEPACT", path, mapping)
        self.assertEqual(new_path_heme, "/staging/heme/file.fastq")

    def test_get_mapping(self):
        """Test internal _get_mapping method"""
        prefix, dst = CopyService._get_mapping(self.recipe, "/path/to/file.fastq", self.mapping)
        self.assertEqual(prefix, "/path/to")
        self.assertEqual(dst, "/new/path/to")

    def test_get_mapping_no_match(self):
        """Test _get_mapping when no prefix matches"""
        prefix, dst = CopyService._get_mapping(self.recipe, "/other/path/file.fastq", self.mapping)
        self.assertIsNone(prefix)
        self.assertIsNone(dst)

    def test_get_reverse_mapping(self):
        """Test reverse mapping to convert staged path back to original"""
        staged_path = "/new/path/to/file/file1.fastq"
        dst, prefix = CopyService.get_reverse_mapping(self.recipe, staged_path, self.mapping)
        self.assertEqual(dst, "/new/path/to")
        self.assertEqual(prefix, "/path/to")

    def test_get_reverse_mapping_no_match(self):
        """Test reverse mapping when no destination matches"""
        other_path = "/some/other/path/file.fastq"
        dst, prefix = CopyService.get_reverse_mapping(self.recipe, other_path, self.mapping)
        self.assertIsNone(dst)
        self.assertIsNone(prefix)

    def test_reverse_mapping_symmetry(self):
        """Test that remap and reverse_mapping are symmetric"""
        original_path = "/path/to/subdir/file.fastq"

        # Forward mapping
        staged_path = CopyService.remap(self.recipe, original_path, self.mapping)
        self.assertEqual(staged_path, "/new/path/to/subdir/file.fastq")

        # Reverse mapping should give us back the components
        dst, prefix = CopyService.get_reverse_mapping(self.recipe, staged_path, self.mapping)
        self.assertEqual(dst, "/new/path/to")
        self.assertEqual(prefix, "/path/to")

        # Reconstruct original
        reconstructed = staged_path.replace(dst, prefix)
        self.assertEqual(reconstructed, original_path)
