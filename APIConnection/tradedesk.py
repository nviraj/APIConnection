import io
import json
import logging
import time
import traceback
from typing import List, Dict

import pandas as pd
import requests
from pandas import DataFrame

from APIConnection.base_connection import BaseConnection

# from .exceptions import FBTimeOut

# logging.basicConfig(filename="ttd.log", level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

TIMEOUT = 1000
TTD_API_URL = "https://api.thetradedesk.com"


class TTDConnection(BaseConnection):
    """Wrapper class for fetching/parsing Trade Desk endpoints"""

    def __init__(self, username=None, password=None, auth_token=None):
        self.username = username
        self.password = password
        if auth_token is None:
            self.auth_token = self.login()
        else:
            self.auth_token = auth_token

    def call_api(self, url: str, payload: dict):
        headers = {"Content-Type": 'application/json', "TTD-Auth": self.auth_token}
        res = requests.get(
            url, headers=headers, json=payload
        )

        if res.ok:
            res = json.loads(str(res.content, "utf-8"))
            return res

        else:
            # If response code is not ok (200), print the resulting http error code with description
            res.raise_for_status()

    @staticmethod
    def get_report_reference_url():
        return f"{TTD_API_URL}/v3/myreports/reportexecution/query/partners"

    def login(self, minutes_to_expire=1440):
        auth_url = f"{TTD_API_URL}/v3/authentication"
        payload = {
            "Login": self.username,
            "Password": self.password,
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

    def get_sub_accounts(self):
        # print(self.call_api("https://api.thetradedesk.com/v3/advertiser", payload={}))
        return [{"id": "tm90ejd", "name": ""}]

    def get_reports(self, partner_id, start_date, end_date, directory="./", get_urls_only=False):
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
                urls = []
                for report in jData["Result"]:
                    url = report["ReportDeliveries"][0]["DownloadURL"]
                    if get_urls_only:
                        urls.append(url)
                    else:
                        report_name = report["ReportDeliveries"][0]["DeliveredPath"].split(
                            "/"
                        )[-1]
                        self.download_report(url, directory, report_name)
                return urls
            except Exception as e:
                logging.error(f"ERROR: can not download the report. Details {e}")

        else:
            # If response code is not ok (200), print the resulting http error code with description
            myResponse.raise_for_status()

        elapsed_time = time.time() - start_time

        print("Execution time in seconds took: ", elapsed_time)

    def download_report(self, url, directory, report_name, write_to_file=True):
        """Download report from url

        Args:
            write_to_file:
            url (str): URL
            directory (str): local directory to store data
            report_name (str): report file name

        Returns:
            None
        """
        headers = {"Content-Type": "application/json", "TTD-Auth": self.auth_token}
        response = requests.get(url, headers=headers)

        try:
            if write_to_file:
                with open(f"{directory}/{report_name}", "w") as f:
                    f.write(str(response.content.decode("utf-8")))
            else:
                return str(response.content.decode("utf-8"))
        except Exception as e:
            logging.error(f"ERROR: can not download {url}. Details {e}")

    def extract_connection_info(self):
        data = {
            "login_account": self.username,
            "num_sub_account": 0,
            "login_account_id": None
        }
        return data

    def get_report_df_for_account(
            self, account: str, start_date: str, end_date: str, dimensions: List[str]
    ) -> DataFrame:

        payload = {
            "partnerIds": [account],
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
        url = TTDConnection.get_report_reference_url()
        myResponse = requests.post(
            url,
            headers={"Content-Type": type, "TTD-Auth": self.auth_token},
            json=payload,
        )

        if myResponse.ok:
            try:
                jData = json.loads(str(myResponse.content, "utf-8"))
                print(jData)
                df = pd.DataFrame(jData["Result"])
                df = df[
                    df['ReportScheduleName'] == 'Coegi, Coegi (CAD)  | Yesterday | daily_ttd_feesreport'
                ]
                link = df.to_dict('records')[0]['ReportDeliveries'][0]['DownloadURL']
                content = self.download_report(
                    url=link, directory="./", report_name="temp",
                    write_to_file=False
                )
                df = pd.read_csv(io.StringIO(content))
                return df
            except Exception as e:
                print(traceback.format_exc())
                logging.error(f"ERROR: can not download the report. Details {e}")

        else:
            myResponse.raise_for_status()


if __name__ == "__main__":
    ttd = TTDConnection(
        username="ttd_api2_tm90ejd@coegi.com",
        password="Coegi2018!"
    )
    print(ttd.login())
    print(ttd.extract_connection_info())
    accounts = ttd.get_sub_accounts()
    # urls = ttd.get_reports(
    #     partner_id=accounts[0]["id"],
    #     start_date="2022-09-01",
    #     end_date="2022-09-02",
    #     directory="./report",
    #     get_urls_only=True
    # )
    # print(urls)
    # df = ttd.get_report_df_for_account(
    #     account=accounts[0]["id"],
    #     start_date="2022-09-01",
    #     end_date="2022-09-02",
    #     dimensions=[]
    # )
    df = ttd.get_sub_accounts_report_df(
        [accounts[0]["id"]],
        start_date="2022-09-01",
        end_date="2022-09-02",
        dimensions=[]
    )
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', None)
    print(df)