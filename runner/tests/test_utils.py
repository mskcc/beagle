import os
import pprint
from uuid import UUID
from django.test import TestCase
from runner.utils import has_bid
from runner.utils import get_BID_from_location
from runner.utils import InvalidBIDError
from runner.utils import get_bids_from_Port_db_values
from runner.utils import DbValuesLackClassKeyError
from runner.utils import get_all_bids_from_Port
from django.conf import settings
from django.core.management import call_command
from file_system.models import File
from runner.models import Port, PortType, Run

class TestHasBid(TestCase):
    def test_true(self):
        self.assertTrue(True)

    def test_has_bid1(self):
        """
        Test that a location without a bid is recognized
        """
        location = 'juno:///juno/work/ci/resources/curated_bams/IDT_Exome_v1_FP_b37/s_C_006635_N001_d.Group8.rg.md.abra.printreads.bam'
        self.assertTrue(has_bid(location) == False)

    def test_has_bid2(self):
        """
        Test that a location without a bid is recognized
        """
        location = '/juno/work/ci/resources/curated_bams/IDT_Exome_v1_FP_b37/s_C_006635_N001_d.Group8.rg.md.abra.printreads.bam'
        self.assertTrue(has_bid(location) == False)

    def test_has_bid3(self):
        """
        Test that a location with a bid is recognized
        """
        location = 'bid:foo'
        self.assertTrue(has_bid(location) == True)

    def test_has_bid4(self):
        """
        Test that a location with a bid is recognized
        """
        location = 'bid:///foo'
        self.assertTrue(has_bid(location) == True)

class TestGetBIDFromLocation(TestCase):
    def test_get_bid1(self):
        """
        Test that a bid can be extracted from a location
        """
        location = 'bid://foo'
        bid = get_BID_from_location(location)
        self.assertTrue(bid == 'foo')

    def test_get_bid2(self):
        """
        Test that a bid can be extracted from a location
        """
        location = 'bid://0fdc6110-b18f-4ef0-9c50-9905bf4a22a9'
        bid = get_BID_from_location(location)
        self.assertTrue(bid == '0fdc6110-b18f-4ef0-9c50-9905bf4a22a9')

    def test_get_bid3(self):
        """
        Test that an invalid bid raises an Exception
        """
        self.assertRaises(InvalidBIDError, get_BID_from_location, location = '/some/path')
        self.assertRaises(InvalidBIDError, get_BID_from_location, location = 'bid:foo')
        self.assertRaises(InvalidBIDError, get_BID_from_location, location = 'bid:/foo')
        self.assertRaises(InvalidBIDError, get_BID_from_location, location = 'bid:///foo')

class TestBIDsFromDbValues(TestCase):
    def test_true(self):
        self.assertTrue(True)

    def test_bids_from_Port_db_values1(self):
        """
        Test that the correct bids are returned from a valid db_values entry
        """
        db_values = {
        'class' : 'File',
        'location': 'bid://0fdc6110-b18f-4ef0-9c50-9905bf4a22a9'
        }
        bids = get_bids_from_Port_db_values(db_values)
        expected_bids = ['0fdc6110-b18f-4ef0-9c50-9905bf4a22a9']
        self.assertTrue(bids == expected_bids)

    def test_bids_from_Port_db_values2(self):
        """
        Test that no bids are returned if item is not 'class' = 'File'
        """
        db_values = {
        'class' : 'foo',
        'location': 'bid://0fdc6110-b18f-4ef0-9c50-9905bf4a22a9'
        }
        bids = get_bids_from_Port_db_values(db_values)
        expected_bids = []
        self.assertTrue(bids == expected_bids)

    def test_bids_from_Port_db_values3(self):
        """
        Test that an error is raised if the 'class' key is not present
        """
        db_values = {
        'location': 'bid://0fdc6110-b18f-4ef0-9c50-9905bf4a22a9'
        }
        self.assertRaises(DbValuesLackClassKeyError, get_bids_from_Port_db_values, db_values = db_values)

    def test_bids_from_Port_db_values4(self):
        """
        Test that an error is raised if the location is not a valid bid
        """
        db_values = {
        'class' : 'File',
        'location': '/0fdc6110-b18f-4ef0-9c50-9905bf4a22a9'
        }
        self.assertRaises(InvalidBIDError, get_bids_from_Port_db_values, db_values = db_values)

    def test_bids_from_Port_db_values5(self):
        """
        Test returned bids from a list of db_values
        """
        db_values = [
        {
        'class' : 'File',
        'location': 'bid://0fdc6110-b18f-4ef0-9c50-9905bf4a22a9'
        },
        {
        'class' : 'File',
        'location': 'bid://cc2f2eb4-f471-4ae7-a0fb-1aaa5c144c2e'
        }
        ]
        expected_bids = ['0fdc6110-b18f-4ef0-9c50-9905bf4a22a9', 'cc2f2eb4-f471-4ae7-a0fb-1aaa5c144c2e']
        bids = get_bids_from_Port_db_values(db_values)
        self.assertTrue(bids == expected_bids)

    def test_bids_from_Port_db_values6(self):
        """
        Test that error is raise if there is an invalid db_value in a list of values
        """
        db_values = [
        {
        'class' : 'File',
        'location': 'bid://0fdc6110-b18f-4ef0-9c50-9905bf4a22a9'
        },
        {
        'class' : 'File',
        'location': '//cc2f2eb4-f471-4ae7-a0fb-1aaa5c144c2e'
        }
        ]
        self.assertRaises(InvalidBIDError, get_bids_from_Port_db_values, db_values = db_values)

class TestGetBIDSFromPort(TestCase):
    """
    """
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
        self.assertTrue(Run.objects.all()[0].id == UUID('ca18b090-03ad-4bef-acd3-52600f8e62eb'))
        self.assertTrue(len(Port.objects.all()) == 47)

        roslin_input_queryset = Port.objects.filter(port_type=PortType.INPUT).all()
        roslin_output_queryset = Port.objects.filter(port_type=PortType.OUTPUT).all()
        self.assertTrue(len(roslin_input_queryset) == 12)
        self.assertTrue(len(roslin_output_queryset) == 35)

    def test_get_File_ids_from_Port1(self):
        """
        Test that we can get correct bid's from an instance of Port
        Test two different Port instances that have the two recognized 'schema' types
        """
        call_command('loaddata',
            os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.run.json"),
            verbosity=0)
        call_command('loaddata',
            os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.port.output.json"),
            verbosity=0)

        port_instance = Port.objects.get(id = UUID('3abd6a10-21d2-49be-bc83-31dd207759ec'))
        bids = get_all_bids_from_Port(port_instance)
        expected_bids = ['b835c33c-d241-42fc-beb2-e1ce1c41a77d']
        self.assertTrue(bids == expected_bids)

        port_instance = Port.objects.get(id = UUID('0be0ceba-0959-4173-a65c-0e6f13604211'))
        bids = get_all_bids_from_Port(port_instance)
        expected_bids = [
        '0f1e06cb-c77b-4988-994f-797eab18cbea',
        '48dd6384-7034-4cc7-9027-7df71496eb27',
        '2c2b195f-514c-4107-af3a-8488cf6547ea',
        '2af79d18-4ba7-4aef-8505-bd775d47b00d',
        '2a1736ce-50fd-4721-92da-474f67318c8d'
        ]
        self.assertTrue(bids == expected_bids)
