import os
from uuid import UUID
from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from file_system.models import File
from runner.models import Port, PortType, Run

class TestPorts(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "runner.pipeline.json"
    ]

    def test_true(self):
        self.assertTrue(True)

    def test_fixtures1(self):
        """
        Sanity test to make sure our Port fixtures look right
        """
        # load fixtures for testing example use case
        call_command('loaddata',
            os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.run.json"),
            verbosity=0)
        call_command('loaddata',
            os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.port.output.json"),
            verbosity=0)
        call_command('loaddata',
            os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.port.input.json"),
            verbosity=0)

        # sanity check for fixture validation
        self.assertTrue(len(Run.objects.all()) == 1)
        self.assertTrue(len(Port.objects.all()) == 47)

        roslin_input_queryset = Port.objects.filter(port_type=PortType.INPUT).all()
        roslin_output_queryset = Port.objects.filter(port_type=PortType.OUTPUT).all()
        self.assertTrue(len(roslin_input_queryset) == 12)
        self.assertTrue(len(roslin_output_queryset) == 35)
