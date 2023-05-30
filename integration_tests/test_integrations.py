from django.test import TestCase
import requests
from requests.auth import HTTPBasicAuth
from runner.models import RunStatus
import json
import os
import time
from operator import itemgetter
import unittest

SUBMIT_ROUTE = "/v0/run/operator/request/"
JOB_GROUP_ROUTE = "/v0/notifier/job-groups/"
NOTIFIER_CREATE_ROUTE = "/v0/notifier/create/"
RUN_ROUTE = "/v0/run/api/"
BEAGLE_URL = os.environ["BEAGLE_URL"]
BEAGLE_USERNAME = os.environ["BEAGLE_USERNAME"]
BEAGLE_PASSWORD = os.environ["BEAGLE_PASSWORD"]
TEST_CONFIG_PATH = os.environ["TEST_CONFIG_PATH"]
TEST_ENV = "RUN_INTEGRATION_TEST"
basic_auth = HTTPBasicAuth(BEAGLE_USERNAME, BEAGLE_PASSWORD)


class RunTestCase(TestCase):
    def setUp(self):
        self.test_data = []
        with open(TEST_CONFIG_PATH, "r") as test_file:
            self.test_data = json.load(test_file)

    @unittest.skipIf(TEST_ENV in os.environ and os.environ[TEST_ENV] == "TRUE", "is a large integration test")
    def test_submit_runs(self):
        run_status = {}
        job_groups = []
        for single_test in self.test_data:
            request_id, pipeline, version, expected_complete = itemgetter(
                "request", "pipeline", "version", "expected_complete"
            )(single_test)
            expected_complete = int(expected_complete)
            job_group_request = requests.post(BEAGLE_URL + JOB_GROUP_ROUTE, auth=basic_auth)
            self.assertTrue(job_group_request.ok)
            new_jobgroup = job_group_request.json()["id"]
            job_groups.append(new_jobgroup)
            time.sleep(1)
            notifier_request = requests.post(
                BEAGLE_URL + NOTIFIER_CREATE_ROUTE,
                data={"job_group": new_jobgroup, "pipeline": pipeline, "request_id": request_id},
                auth=basic_auth,
            )
            self.assertTrue(notifier_request.ok)
            submit_url = BEAGLE_URL + SUBMIT_ROUTE
            submit_payload = {
                "request_ids": [request_id],
                "pipeline": pipeline,
                "pipeline_version": version,
                "job_group_id": str(new_jobgroup),
            }
            run_id = str(pipeline) + "_" + str(version) + "_" + str(request_id)
            submit_response = requests.post(submit_url, json=submit_payload, auth=basic_auth)
            run_status[run_id] = {
                "job_group": new_jobgroup,
                "status": "Submitted",
                "num_running": None,
                "num_expected": expected_complete,
            }
            if not submit_response.ok:
                run_status[run_id]["status"] = "Not submitted"

        count = 0
        prev_running = None
        done = False
        while not done:
            run_status_request = requests.get(
                BEAGLE_URL + RUN_ROUTE, params={"job_groups": job_groups}, auth=basic_auth
            )
            status_dict = {}
            if run_status_request.ok:
                for single_run in run_status_request.json()["results"]:
                    job_group = single_run["job_group"]
                    if job_group not in status_dict:
                        status_dict[job_group] = []
                    status_dict[job_group].append(single_run["status"])
            for single_run_id in run_status:
                single_run = run_status[single_run_id]
                jobgroup = single_run["job_group"]
                prev_running = single_run["num_running"]
                status = single_run["status"]
                if status != "Submitted":
                    continue

                if RunStatus.FAILED.name in status_dict[jobgroup]:
                    single_run["status"] = "Failed"
                    continue
                if RunStatus.TERMINATED.name in status_dict[jobgroup]:
                    single_run["status"] = "Terminated"
                    continue
                count = status_dict[job_group].count(RunStatus.COMPLETED.name)
                if count == expected_complete:
                    single_run["status"] = "Completed"
                else:
                    curr_running = len(status_dict[job_group]) - count
                    if curr_running != prev_running:
                        prev_running = curr_running
                    else:
                        if curr_running == prev_running == 0:
                            single_run["status"] = "Hanging or Partially completed"
            status_list = [run_status[run_id]["status"] for run_id in run_status]
            if "Submitted" not in status_list:
                done = True
            else:
                self.assertTrue(count < 36)
                time.sleep(300)
                count += 1
        for single_run_id in run_status:
            single_run = run_status[single_run_id]
            self.assertEqual(single_run["status"], "Completed")
