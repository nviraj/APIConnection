import io
import os
import argparse
import sys
import time
from csv import reader, writer
from pprint import pprint
import httplib2
import logging
from datetime import date, timedelta

from googleapiclient import http
from googleapiclient import discovery

from oauth2client import client
from oauth2client import file as oauthFile
from oauth2client import tools


from .settings import GOOGLE_COMPAIGN_MANAGER_REPORT, GOOGLE_CLIENT_SECRET
from . import dfareporting_utils

logging.basicConfig(filename="google_campaign_manager.log", level=logging.DEBUG)

SUCCESS = True
FAIL = False
CHUNK_SIZE = 32 * 1024 * 1024

API_NAME = "dfareporting"
API_VERSION = "v3.4"
API_SCOPES = [
    "https://www.googleapis.com/auth/dfareporting",
    "https://www.googleapis.com/auth/dfatrafficking",
    "https://www.googleapis.com/auth/ddmconversions",
]

# CREDENTIAL_STORE_FILE = '/Users/giangb/projects/APIConnection/APIConnection/dfareporting.dat'
CREDENTIAL_STORE_FILE = "./dfareporting.dat"


class GoogleCampaignManager:
    """Wrapper class for fetching/parsing GCM endpoints"""

    def __init__(self, service=None):
        self.client_secret_file = GOOGLE_CLIENT_SECRET
        self.service = service if service is not None else self.get_service()

    def get_service(self):
        # Check whether credentials exist in the credential store. Using a credential
        # store allows auth credentials to be cached, so they survive multiple runs
        # of the application. This avoids prompting the user for authorization every
        # time the access token expires, by remembering the refresh token.
        storage = oauthFile.Storage(CREDENTIAL_STORE_FILE)
        credentials = storage.get()

        # If no credentials were found, go through the authorization process and
        # persist credentials to the credential store.

        if credentials is None or credentials.invalid:
            flow = client.flow_from_clientsecrets(
                self.client_secret_file,
                scope=API_SCOPES,
                message=tools.message_if_missing(self.client_secret_file),
            )
            credentials = tools.run_flow(
                flow, storage, tools.argparser.parse_known_args()[0]
            )

        # Use the credentials to authorize an httplib2.Http instance.
        http = credentials.authorize(httplib2.Http())

        # Construct a service object via the discovery service.
        service = discovery.build("dfareporting", "v3.4", http=http)
        return service

    def get_profile_id(self):
        """retrieve all profile ids in the current account"""
        request = self.service.userProfiles().list()
        # Execute request and print response.
        response = request.execute()

        res = []
        for profile in response["items"]:
            res.append(profile["profileId"])
            print(
                'Found user profile with ID %s and user name "%s".'
                % (profile["profileId"], profile["userName"])
            )

        return res

    def get_all_report_ids(self, profile_id):
        """get all reports created under the profile id"""
        request = self.service.reports().list(profileId=profile_id)
        res = []
        while True:
            response = request.execute()
            for item in response["items"]:
                res.append(item["id"])
            if response["items"] and response["nextPageToken"]:
                request = self.service.reports().list_next(request, response)
            else:
                break
        return res

    def get_report_metadata(self, profile_id, report_id):
        """retrieve report metadata"""

        request = self.service.reports().get(profileId=profile_id, reportId=report_id)
        response = request.execute()

    def get_all_report_files(self, start_date, end_date):
        """loop through all reports declared in config file and download them"""
        for report_config in GOOGLE_COMPAIGN_MANAGER_REPORT:
            profile_id, report_id = (
                report_config["profile_id"],
                report_config["report_id"],
            )

            # update date range for the report
            if self.update_date_range_for_report(
                profile_id, report_id, start_date, end_date
            ):
                # pull data with updated report
                self.get_report_content(
                    profile_id, report_id, f"{profile_id}_{report_id}.csv"
                )
            else:
                logging.error(f"Can not set date range for report {report_id}")

    def update_date_range_for_report(self, profile_id, report_id, start_date, end_date):
        """Update report id with new date range"""
        body = {}
        body["criteria"] = {"dateRange": {"startDate": start_date, "endDate": end_date}}

        try:
            patched_report = (
                self.service.reports()
                .patch(profileId=profile_id, reportId=report_id, body=body)
                .execute()
            )
            return SUCCESS
        except Exception as e:
            logging.error(e)
            return FAIL

    def get_report_content(self, profile_id, report_id, filename):
        """Download report file

        Args:
            profile_id(int): profile id
            report_id(int): report id
            filename(str): the name of file download to
        """
        try:
            # construct a get request for the specified report
            request = self.service.reports().run(
                profileId=profile_id, reportId=report_id
            )
            result = request.execute()
            file_id = result["id"]
            report_file = (
                self.service.files().get(reportId=report_id, fileId=file_id).execute()
            )
            out_file = io.FileIO(filename, mode="wb")
            # check status of report file
            request = (
                self.service.reports()
                .files()
                .list(profileId=profile_id, reportId=report_id)
            )
            response = request.execute()

            while response["items"][0]["status"] != "REPORT_AVAILABLE":
                time.sleep(30)  # delay for 30 seconds before checking again
                request = (
                    self.service.reports()
                    .files()
                    .list(profileId=profile_id, reportId=report_id)
                )
                response = request.execute()

            request = self.service.files().get_media(
                reportId=report_id, fileId=file_id
            )  # construct request to download file

            # Create a media downloader instance.
            # Optional: adjust the chunk size used when downloading the file.
            downloader = http.MediaIoBaseDownload(
                out_file, request, chunksize=CHUNK_SIZE
            )

            # Execute the get request and download the file.
            download_finished = False
            while download_finished is False:
                _, download_finished = downloader.next_chunk()

            print(
                "File %s downloaded to %s"
                % (report_file["id"], os.path.realpath(out_file.name))
            )

        except client.AccessTokenRefreshError:
            print(
                "The credentials have been revoked or expired, please re-run the application to re-authorize"
            )

    def find_report(self, profile_id, by_name):
        """Find report by name"""

        def _is_target_report(report, by_name):
            """find report given a part of name"""
            if by_name in report["name"]:
                return True
            return False

        target = None
        # Construct the request.
        request = service.reports().list(profileId=profile_id)
        while True:
            response = request.execute()
            for report in response["items"]:
                if _is_target_report(report, by_name):
                    target = report
                    break

            if not target and response["items"] and response["nextPageToken"]:
                request = self.service.reports().list_next(request, response)
            else:
                break

    def create_report(self, profile_id):
        try:
            # 1. Create a report resource.
            report = self.create_report_resource()

            # 2. Define the report criteria.
            self.define_report_criteria(report)

            # 3. (optional) Look up compatible fields.
            self.find_compatible_fields(self.service, profile_id, report)

            # 4. Add dimension filters to the report criteria.
            # add_dimension_filters(service, profile_id, report)

            # 5. Save the report resource.
            report = self.insert_report_resource(self.service, profile_id, report)

        except client.AccessTokenRefreshError:
            print(
                "The credentials have been revoked or expired, please re-run the "
                "application to re-authorize"
            )

    def create_report_resource(self):
        """Creates a report resource."""
        report = {
            # Set the required fields "name" and "type".
            "name": "Example Standard Report",
            "type": "STANDARD",
            # Set optional fields.
            "fileName": "example_report",
            "format": "CSV",
        }

        print(
            'Creating %s report resource with name "%s".'
            % (report["type"], report["name"])
        )

        return report

    def define_report_criteria(self, report):
        """Defines a criteria for the report."""
        # Define a date range to report on. This example uses explicit start and end
        # dates to mimic the "LAST_30_DAYS" relative date range.
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        # Create a report criteria.
        criteria = {
            "dateRange": {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
            },
            "dimensions": [
                {"name": "advertiser"},
                {"name": "campaign"},
                {"name": "site"},
                {"name": "placement"},
                {"name": "date"},
                {"name": "creative"},
                {"name": "platformType"},
                {"name": "packageRoadblock"},
            ],
            "metricNames": [
                "impressions",
                "clicks",
                "clickRate",
                "activeViewViewableImpressions",
                "activeViewMeasurableImpressions",
                "activeViewEligibleImpressions",
                "totalConversions",
                "mediaCost",
            ],
        }

        # Add the criteria to the report resource.
        report["criteria"] = criteria

        print("\nAdded report criteria:\n%s" % criteria)

    def find_compatible_fields(self, service, profile_id, report):
        """Finds and adds a compatible dimension/metric to the report."""
        fields = (
            service.reports()
            .compatibleFields()
            .query(profileId=profile_id, body=report)
            .execute()
        )

        report_fields = fields["reportCompatibleFields"]

        if report_fields["dimensions"]:
            # Add a compatible dimension to the report.
            report["criteria"]["dimensions"].append(
                {"name": report_fields["dimensions"][0]["name"]}
            )
        elif report_fields["metrics"]:
            # Add a compatible metric to the report.
            report["criteria"]["metricNames"].append(
                report_fields["metrics"][0]["name"]
            )

        print(
            "\nUpdated report criteria (with compatible fields):\n%s"
            % report["criteria"]
        )

    def add_dimension_filters(self, service, profile_id, report):
        """Finds and adds a valid dimension filter to the report."""
        # Query advertiser dimension values for report run dates.
        request = {
            "dimensionName": "advertiser",
            "endDate": report["criteria"]["dateRange"]["endDate"],
            "startDate": report["criteria"]["dateRange"]["startDate"],
        }

        values = (
            service.dimensionValues()
            .query(profileId=profile_id, body=request)
            .execute()
        )

        if values["items"]:
            # Add a value as a filter to the report criteria.
            report["criteria"]["dimensionFilters"] = [values["items"]]

        print(
            "\nUpdated report criteria (with valid dimension filters):\n%s"
            % report["criteria"]
        )

    def insert_report_resource(self, service, profile_id, report):
        """Inserts the report."""
        #   return
        inserted_report = (
            service.reports().insert(profileId=profile_id, body=report).execute()
        )

        print("\nSuccessfully inserted new report with ID %s." % inserted_report["id"])

        return inserted_report
