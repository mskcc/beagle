from django.test import TestCase
import requests
from requests.auth import HTTPBasicAuth
from runner.models import RunStatus
import json
import os
import time
from operator import itemgetter
import unittest
import subprocess
from datetime import datetime

SUBMIT_ROUTE = "/v0/run/operator/request/"
JOB_GROUP_ROUTE = "/v0/notifier/job-groups/"
NOTIFIER_CREATE_ROUTE = "/v0/notifier/create/"
RUN_ROUTE = "/v0/run/api/"
TEST_ENV = "RUN_INTEGRATION_TEST"
OPEN_API_ROUTE = "/?format=openapi"
SLACK_POST_ROUTE = "https://slack.com/api/chat.postMessage"
SLACK_UPDATE_ROUTE = "https://slack.com/api/chat.update"


run_status_color = {
    "Submitted": "#2F8AB7",
    "Terminated": "#F6BBC1",
    "Failed": "#F2606A",
    "Completed": "#779846",
    "Stalled": "#FFD57E",
    "Not Submitted": "#C05B8C",
}


class RunTestCase(TestCase):
    def setUp(self):
        self.test_data = []
        if "TEST_CONFIG_PATH" in os.environ:
            TEST_CONFIG_PATH = os.environ["TEST_CONFIG_PATH"]
            with open(TEST_CONFIG_PATH, "r") as test_file:
                self.test_data = json.load(test_file)
            self.beagle_url = os.environ["BEAGLE_URL"]
            self.ridgeback_url = os.environ["BEAGLE_RIDGEBACK_URL"]
            self.beagle_path = os.environ["BEAGLE_PATH"]
            self.ridgeback_path = os.environ["RIDGEBACK_PATH"]
            self.beagle_username = os.environ["BEAGLE_USERNAME"]
            self.beagle_password = os.environ["BEAGLE_PASSWORD"]
            self.beagle_git = os.environ["BEAGLE_GIT"]
            self.ridgeback_git = os.environ["RIDGEBACK_GIT"]
            self.slack_channel = os.environ["SLACK_CHANNEL"]
            self.slack_token = os.environ["SLACK_TOKEN"]
            self.build_number = os.environ["BUILD_NUMBER"]
            self.build_url = os.environ["BUILD_URL"]
            self.beagle_basic_auth = HTTPBasicAuth(self.beagle_username, self.beagle_password)

    def send_slack_message(self, run_status, ts, channel):
        beagle_version, beagle_url, ridgeback_version, ridgeback_url = self.get_service_versions()
        current_time = datetime.strftime(datetime.now(), "%a %H-%M")

        footer_block = {
            "blocks": [
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Beagle version: <{beagle_url}| {beagle_version}>"},
                        {"type": "mrkdwn", "text": f"Ridgeback version: <{ridgeback_url}| {ridgeback_version}>"},
                        {"type": "mrkdwn", "text": f"Last updated: {current_time}>"},
                        {"type": "mrkdwn", "text": f"Build: <{self.build_url}| {self.build_number}>"},
                    ],
                },
            ]
        }
        header_block = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "Good news everyone! Tests are now running on staging beagle",
                        "emoji": True,
                    },
                },
                {"type": "divider"},
            ],
            "color": "#FFFFFF",
        }
        attachment_list = [header_block]
        run_id_list = run_status.keys().sort()
        for single_run_id in run_id_list:
            status = run_status[single_run_id]["status"]
            color = run_status_color[status]
            job_group = run_status[single_run_id]["job_group"]
            count = run_status[single_run_id]["num_total"]
            job_group_link = self.beagle_url + RUN_ROUTE + "?job_groups=" + job_group
            job_text = f"{status} - <{job_group_link}|{single_run_id}> - {count} jobs"
            single_block = {
                "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": job_text}}],
                "color": color,
            }
            attachment_list.append(single_block)
        attachment_list.append(footer_block)
        slack_response = None
        if not ts:
            slack_response = requests.post(
                SLACK_POST_ROUTE,
                params={"channel": self.slack_channel, "attachments": attachment_list},
                headers={"Authorization": f"Bearer {self.slack_token}"},
            )
        else:
            slack_response = requests.post(
                SLACK_UPDATE_ROUTE,
                params={"channel": channel, "attachments": attachment_list, "ts": ts},
                headers={"Authorization": f"Bearer {self.slack_token}"},
            )
            if not slack_response.ok:
                slack_response = requests.post(
                    SLACK_POST_ROUTE,
                    params={"channel": self.slack_channel, "attachments": attachment_list},
                    headers={"Authorization": f"Bearer {self.slack_token}"},
                )
        if slack_response and slack_response.ok:
            return slack_response.json()["ts"], slack_response.json()["channel"]

    def get_service_versions(self):
        beagle_hash = subprocess.run(["git", "-C", self.beagle_path, "rev-parse", "HEAD"]).stdout
        beagle_openapi = requests.get(self.beagle_url + OPEN_API_ROUTE)
        ridgeback_hash = subprocess.run(["git", "-C", self.beagle_path, "rev-parse", "HEAD"]).stdout
        ridgeback_openapi = requests.get(self.ridgeback_url + OPEN_API_ROUTE)
        if beagle_openapi.ok:
            beagle_version = beagle_openapi.json()["info"]["title"]["version"]
        else:
            beagle_version = "NA"
        if beagle_hash:
            beagle_url = self.beagle_git + "/tree/" + beagle_hash
        else:
            beagle_url = self.beagle_git
        if ridgeback_openapi.ok:
            ridgeback_version = ridgeback_openapi.json()["info"]["title"]["version"]
        else:
            ridgeback_version = "NA"
        if ridgeback_hash:
            ridgeback_url = self.ridgeback_git + "/tree/" + ridgeback_hash
        else:
            ridgeback_url = self.ridgeback_git
        return beagle_version, beagle_url, ridgeback_version, ridgeback_url

    @unittest.skipIf(TEST_ENV not in os.environ, "is a large integration test")
    def test_submit_runs(self):
        run_status = {}
        job_groups = []
        for single_test in self.test_data:
            request_id, pipeline, version, expected_complete = itemgetter(
                "request", "pipeline", "version", "expected_complete"
            )(single_test)
            expected_complete = int(expected_complete)
            job_group_request = requests.post(
                self.beagle_url + JOB_GROUP_ROUTE, auth=self.beagle_self.beagle_basic_auth
            )
            self.assertTrue(job_group_request.ok)
            new_jobgroup = job_group_request.json()["id"]
            job_groups.append(new_jobgroup)
            time.sleep(1)
            notifier_request = requests.post(
                self.beagle_url + NOTIFIER_CREATE_ROUTE,
                data={"job_group": new_jobgroup, "pipeline": pipeline, "request_id": request_id},
                auth=self.beagle_basic_auth,
            )
            self.assertTrue(notifier_request.ok)
            submit_url = self.beagle_url + SUBMIT_ROUTE
            submit_payload = {
                "request_ids": [request_id],
                "pipeline": pipeline,
                "pipeline_version": version,
                "job_group_id": str(new_jobgroup),
            }
            run_id = str(pipeline) + "_" + str(version) + "_" + str(request_id)
            submit_response = requests.post(submit_url, json=submit_payload, auth=self.beagle_basic_auth)
            run_status[run_id] = {
                "job_group": new_jobgroup,
                "status": "Submitted",
                "num_running": None,
                "num_expected": expected_complete,
                "num_total": 0,
            }
            if not submit_response.ok:
                run_status[run_id]["status"] = "Not Submitted"

        count = 0
        prev_running = None
        done = False
        ts = None
        channel = None
        while not done:
            run_status_request = requests.get(
                self.beagle_url + RUN_ROUTE, params={"job_groups": job_groups}, auth=self.beagle_basic_auth
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
                jobgroup_run_statuses = status_dict[jobgroup]
                total_jobs = len(jobgroup_run_statuses)
                single_run["num_total"] = total_jobs
                if status != "Submitted":
                    continue

                if RunStatus.FAILED.name in jobgroup_run_statuses:
                    single_run["status"] = "Failed"
                    continue
                if RunStatus.TERMINATED.name in jobgroup_run_statuses:
                    single_run["status"] = "Terminated"
                    continue
                count = jobgroup_run_statuses.count(RunStatus.COMPLETED.name)
                if count == expected_complete:
                    single_run["status"] = "Completed"
                else:
                    curr_running = total_jobs - count
                    if curr_running != prev_running:
                        prev_running = curr_running
                    else:
                        if curr_running == prev_running == 0:
                            single_run["status"] = "Stalled"
            status_list = [run_status[run_id]["status"] for run_id in run_status]
            ts, channel = self.send_slack_message(run_status, ts, channel)
            if "Submitted" not in status_list:
                done = True
            else:
                self.assertTrue(count < 36)
                time.sleep(300)
                count += 1
        for single_run_id in run_status:
            single_run = run_status[single_run_id]
            self.assertEqual(single_run["status"], "Completed")
