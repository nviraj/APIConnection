import requests
import json
import time
import logging

import pandas as pd

# from .exceptions import FBTimeOut

# logging.basicConfig(filename="ttd.log", level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

TIMEOUT = 1000
TTD_API_URL = "https://api.thetradedesk.com"


class TTDConnection:
    """Wrapper class for fetching/parsing Trade Desk endpoints"""

    def __init__(self, username=None, password=None, auth_token=None):
        self.username = username
        self.password = password
        if auth_token is None:
            self.auth_token = self.login(username, password)
        else:
            self.auth_token = auth_token

    @staticmethod
    def get_report_reference_url():
        return f"{TTD_API_URL}/v3/myreports/reportexecution/query/partners"

    def login(self, login, password, minutes_to_expire=1440):
        """login to account to generate auth Token

        Args:
            login (str): username
            password (str): password
            minutes_to_expire (int): expired time

        Returns:
            (str): auth token
        """
        auth_url = f"{TTD_API_URL}/v3/authentication"
        payload = {
            "Login": login,
            "Password": password,
            "TokenExpirationInMinutes": minutes_to_expire,
        }

        myResponse = requests.post(
            auth_url, headers={"Content-Type": "application/json"}, json=payload
        )

        if myResponse.ok:
            jData = json.loads(str(myResponse.content, "utf-8"))
            return jData["Token"]

        else:
            # If response code is not ok (200), print the resulting http error code with description
            myResponse.raise_for_status()

    def get_reports(self, partner_id, start_date, end_date, directory="./"):
        """Fetch report report

        Args:
            partner_id (str): partner ID
            start_date (str): date format of `YYYY-MM-DD`
            end_date (str): date format of `YYYY-MM-DD`
            directory (str): local directory to store reports

        Returns:
            None
        """

        payload = {
            "partnerIds": [partner_id],
            "SortFields": [{"FieldId": "Timezone", "Ascending": True}],
            "ReportExecutionStates": [
                "complete",
            ],
            "ExecutionSpansStartDate": start_date,
            "ExecutionSpansEndDate": end_date,
            "PageStartIndex": 0,
            "PageSize": 10,
        }

        type = "application/json"

        start_time = time.time()
        url = TTDConnection.get_report_reference_url()
        myResponse = requests.post(
            url,
            headers={"Content-Type": type, "TTD-Auth": self.auth_token},
            json=payload,
        )

        if myResponse.ok:
            try:
                jData = json.loads(str(myResponse.content, "utf-8"))

                for report in jData["Result"]:
                    url = report["ReportDeliveries"][0]["DownloadURL"]
                    report_name = report["ReportDeliveries"][0]["DeliveredPath"].split(
                        "/"
                    )[-1]
                    self.download_report(url, directory, report_name)
            except Exception as e:
                logging.error(f"ERROR: can not download the report. Details {e}")

        else:
            # If response code is not ok (200), print the resulting http error code with description
            myResponse.raise_for_status()

        elapsed_time = time.time() - start_time

        print("Execution time in seconds took: ", elapsed_time)

    def download_report(self, url, directory, report_name):
        """Download report from url

        Args:
            url (str): URL
            directory (str): local directory to store data
            report_name (str): report file name

        Returns:
            None
        """
        headers = {"Content-Type": "application/json", "TTD-Auth": self.auth_token}
        response = requests.get(url, headers=headers)

        try:

            with open(f"{directory}/{report_name}", "w") as f:
                f.write(str(response.content.decode("utf-8")))
        except Exception as e:
            logging.error(f"ERROR: can not download {url}. Details {e}")

    def extract_connection_info(self):
        data = {
            "login_account": self.username,
            "num_sub_account": 0,
            "login_account_id": None
        }
        return data
