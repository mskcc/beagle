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
PIPELINE_ROUTE = "/v0/run/pipelines/"
RUN_ROUTE = "/v0/run/api/"
TEST_ENV = "RUN_INTEGRATION_TEST"
OPEN_API_ROUTE = "/?format=openapi"
SLACK_POST_ROUTE = "https://slack.com/api/chat.postMessage"
SLACK_UPDATE_ROUTE = "https://slack.com/api/chat.update"
PIPELINES_TO_WAIT = ["aion"]

run_status_color = {
    "Submitted": "#d57eff",
    "Waiting": "#FF00FF",
    "Running": "#2F8AB7",
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
            self.service_env = os.environ["SERVICE_ENV"]
            self.beagle_username = os.environ["BEAGLE_USERNAME"]
            self.beagle_password = os.environ["BEAGLE_PASSWORD"]
            self.beagle_git = os.environ["BEAGLE_GIT"]
            self.ridgeback_git = os.environ["RIDGEBACK_GIT"]
            self.slack_channel = os.environ["SLACK_CHANNEL"]
            self.slack_token = os.environ["SLACK_TOKEN"]
            self.build_number = os.environ["BUILD_NUMBER"]
            self.build_url = os.environ["BUILD_URL"]
            self.resume = os.environ["RESUME"]
            self.num_hours = int(os.environ["NUM_HOURS"])
            self.beagle_basic_auth = HTTPBasicAuth(self.beagle_username, self.beagle_password)
            self.pipeline_info_list = None

    def send_slack_message(self, run_status, ts, channel):
        beagle_version, beagle_url, ridgeback_version, ridgeback_url = self.get_service_versions()
        current_time = datetime.strftime(datetime.now(), "%a %H:%M")

        footer_block = {
            "blocks": [
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Beagle version: <{beagle_url}| {beagle_version}>"},
                        {"type": "mrkdwn", "text": f"Ridgeback version: <{ridgeback_url}| {ridgeback_version}>"},
                        {"type": "mrkdwn", "text": f"Last updated: {current_time}"},
                        {"type": "mrkdwn", "text": f"Build: <{self.build_url}| #{self.build_number}>"},
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
                        "text": f"Good news everyone! Tests are now running on {self.service_env}!",
                        "emoji": True,
                    },
                },
                {"type": "divider"},
            ],
            "color": "#FFFFFF",
        }
        attachment_list = [header_block]
        run_id_list = list(run_status.keys())
        run_id_list.sort()
        for single_jobgroup_id in run_id_list:
            single_run = run_status[single_jobgroup_id]
            run_id = single_run["run_id"]
            status = single_run["status"]
            color = run_status_color[status]
            count = single_run["num_total"]
            if status == "Submitted" and count > 0:
                status = "Running"
            job_group_link = self.beagle_url + RUN_ROUTE + "?job_groups=" + single_jobgroup_id
            job_text = f"{status} - <{job_group_link}|{run_id}> - {count} jobs"
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
                params={"channel": self.slack_channel, "attachments": json.dumps(attachment_list)},
                headers={"Authorization": f"Bearer {self.slack_token}"},
            )
        else:
            slack_response = requests.post(
                SLACK_UPDATE_ROUTE,
                params={"channel": channel, "attachments": json.dumps(attachment_list), "ts": ts},
                headers={"Authorization": f"Bearer {self.slack_token}"},
            )
            if not slack_response.ok:
                slack_response = requests.post(
                    SLACK_POST_ROUTE,
                    params={"channel": self.slack_channel, "attachments": json.dumps(attachment_list)},
                    headers={"Authorization": f"Bearer {self.slack_token}"},
                )
        if (
            slack_response
            and slack_response.ok
            and "ts" in slack_response.json()
            and "channel" in slack_response.json()
        ):
            return slack_response.json()["ts"], slack_response.json()["channel"]

    def get_service_versions(self):
        beagle_hash = None
        ridgeback_hash = None
        beagle_hash_process = subprocess.run(
            ["git", "-C", self.beagle_path, "rev-parse", "HEAD"], capture_output=True, text=True
        )
        if beagle_hash_process.returncode == 0:
            beagle_hash = beagle_hash_process.stdout.strip()
        beagle_openapi = requests.get(self.beagle_url + OPEN_API_ROUTE)
        ridgeback_hash_process = subprocess.run(
            ["git", "-C", self.ridgeback_path, "rev-parse", "HEAD"], capture_output=True, text=True
        )
        if ridgeback_hash_process.returncode == 0:
            ridgeback_hash = ridgeback_hash_process.stdout.strip()
        ridgeback_openapi = requests.get(self.ridgeback_url + OPEN_API_ROUTE)
        if beagle_openapi.ok:
            beagle_version = beagle_openapi.json()["info"]["version"]
        else:
            beagle_version = "NA"
        if beagle_hash:
            beagle_url = self.beagle_git + "/tree/" + beagle_hash
        else:
            beagle_url = self.beagle_git
        if ridgeback_openapi.ok:
            ridgeback_version = ridgeback_openapi.json()["info"]["version"]
        else:
            ridgeback_version = "NA"
        if ridgeback_hash:
            ridgeback_url = self.ridgeback_git + "/tree/" + ridgeback_hash
        else:
            ridgeback_url = self.ridgeback_git
        return beagle_version, beagle_url, ridgeback_version, ridgeback_url

    def resume_job(self, test_obj, job_groups, run_status):
        request_id, pipeline, version, expected_complete = itemgetter(
            "request", "pipeline", "version", "expected_complete"
        )(test_obj)
        job_group_id = None
        if not self.pipeline_info_list:
            pipeline_request = requests.get(
                self.beagle_url + PIPELINE_ROUTE, params={"page_size": 100}, auth=self.beagle_basic_auth
            )
            if pipeline_request.ok:
                self.pipeline_info_list = pipeline_request.json()["results"]
            else:
                return None
        app_id = None
        for single_app in self.pipeline_info_list:
            if single_app["name"] == pipeline and single_app["version"] == version:
                app_id = single_app["id"]
        if app_id:
            job_group_request = requests.get(
                self.beagle_url + RUN_ROUTE,
                params={"apps": app_id, "request_ids": request_id, "page_size": 1, "values_run": "job_group"},
                auth=self.beagle_basic_auth,
            )
            if job_group_request.ok:
                job_group_list = job_group_request.json()["results"]
                if job_group_list:
                    job_group_id = job_group_list[0]
        if job_group_id:
            job_groups.append(job_group_id)
            run_id = str(pipeline) + " ( " + str(version) + " )  - " + str(request_id)
            run_status[job_group_id] = {
                "job_group": job_group_id,
                "status": "Submitted",
                "num_running": None,
                "num_expected": expected_complete,
                "num_total": 0,
                "submit_payload": None,
                "run_id": run_id,
            }
            return job_group_id
        return None

    def prepare_job(self, test_obj, job_groups, run_status):
        request_id, pipeline, version, expected_complete = itemgetter(
            "request", "pipeline", "version", "expected_complete"
        )(test_obj)
        expected_complete = int(expected_complete)
        job_group_request = requests.post(self.beagle_url + JOB_GROUP_ROUTE, auth=self.beagle_basic_auth)
        self.assertTrue(job_group_request.ok)
        new_jobgroup = job_group_request.json()["id"]
        job_groups.append(new_jobgroup)
        run_id = str(pipeline) + " ( " + str(version) + " )  - " + str(request_id)
        submit_payload = {
            "request_ids": [request_id],
            "pipeline": pipeline,
            "pipeline_version": version,
            "job_group_id": str(new_jobgroup),
        }

        run_status[new_jobgroup] = {
            "job_group": new_jobgroup,
            "status": "Not Submitted",
            "num_running": None,
            "num_expected": expected_complete,
            "num_total": 0,
            "submit_payload": submit_payload,
            "run_id": run_id,
        }
        return new_jobgroup

    def submit_job(self, run_status, job_group):
        submit_payload = run_status[job_group]["submit_payload"]
        if submit_payload:
            submit_url = self.beagle_url + SUBMIT_ROUTE
            submit_response = requests.post(submit_url, json=submit_payload, auth=self.beagle_basic_auth)
            if submit_response.ok:
                run_status[job_group]["status"] = "Submitted"

    @unittest.skipIf(TEST_ENV not in os.environ, "is a large integration test")
    def test_submit_runs(self):
        run_status = {}
        job_groups = []
        for single_test in self.test_data:
            job_group = None
            if self.resume == "true":
                job_group = self.resume_job(single_test, job_groups, run_status)
            if not job_group:
                job_group = self.prepare_job(single_test, job_groups, run_status)
            if single_test["pipeline"] not in PIPELINES_TO_WAIT:
                self.submit_job(run_status, job_group)
            else:
                run_status[job_group]["status"] = "Waiting"
        count = 0
        prev_running = None
        done = False
        ts = None
        channel = None
        while not done:
            run_status_request = requests.get(
                self.beagle_url + RUN_ROUTE,
                params={"job_groups": job_groups, "page_size": 100},
                auth=self.beagle_basic_auth,
            )
            status_dict = {}
            if run_status_request.ok:
                for single_run in run_status_request.json()["results"]:
                    job_group = single_run["job_group"]
                    if job_group not in status_dict:
                        status_dict[job_group] = []
                    status_dict[job_group].append(single_run["status"])
            for single_job_group in run_status:
                single_run = run_status[single_job_group]
                prev_running = single_run["num_running"]
                status = single_run["status"]
                expected_complete = single_run["num_expected"]
                run_status_list = []
                if single_job_group in status_dict:
                    run_status_list = status_dict[single_job_group]
                total_jobs = len(run_status_list)
                single_run["num_total"] = total_jobs
                if status != "Submitted":
                    continue

                if RunStatus.FAILED.name in run_status_list:
                    single_run["status"] = "Failed"
                    continue
                if RunStatus.TERMINATED.name in run_status_list:
                    single_run["status"] = "Terminated"
                    continue
                count = run_status_list.count(RunStatus.COMPLETED.name)
                if count == expected_complete:
                    single_run["status"] = "Completed"
                else:
                    curr_running = total_jobs - count
                    single_run["num_running"] = curr_running
                    if curr_running == prev_running == 0:
                        single_run["status"] = "Stalled"
                run_status[single_job_group] = single_run
            ts, channel = self.send_slack_message(run_status, ts, channel)
            status_list = [run_status[job_group]["status"] for job_group in run_status]
            if "Submitted" not in status_list:
                if "Waiting" in status_list:
                    for single_job_group in run_status:
                        if run_status[single_job_group]["status"] == "Waiting":
                            self.submit_job(run_status, single_job_group)
                else:
                    done = True
            else:
                self.assertTrue(count < self.num_hours)
                time.sleep(3600)
                count += 1
        for single_job_group in run_status:
            single_run = run_status[single_job_group]
            self.assertEqual(single_run["status"], "Completed")
