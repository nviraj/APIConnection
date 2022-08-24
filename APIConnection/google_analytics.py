import logging
from pprint import pprint
from typing import List, Dict, Any, Optional

import httplib2
import pandas as pd
from googleapiclient.discovery import build
from oauth2client import client
from oauth2client import file
from oauth2client import tools

# from apiclient.discovery import build

SCOPES = [
    # 'https://www.googleapis.com/auth/userinfo.email',
    # 'https://www.googleapis.com/auth/userinfo.profile',
    # "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.readonly"
]
# CLIENT_SECRETS_PATH = '/home/quydx/Desktop/APIConnection/client_secret.json'
CLIENT_SECRETS_PATH = 'C:\\Users\\Admin\\Desktop\\APIConnection\\ga_quybulu.json'
# VIEW_ID = '107519727'


# logging.basicConfig(filename="google_analyst.log", level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


class GoogleAnalyst:
    """Wrapper class for fetching/parsing GoogleAnalyst endpoints"""

    def __init__(self, connection_id: Optional[str]):
        self.client = client.flow_from_clientsecrets(
            CLIENT_SECRETS_PATH, scope=SCOPES,
            message=tools.message_if_missing(CLIENT_SECRETS_PATH)
        )
        self.cached_credential_path = (
            f"{connection_id}_analyticsreporting.dat" if connection_id else "analyticsreporting.dat"
        )

    def get_summaries(self):
        storage = file.Storage(self.cached_credential_path)
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(self._flow, storage)
        print("test")
        http = credentials.authorize(http=httplib2.Http())
        analytics = build('analytics', 'v3', http=http)
        return analytics.management().accountSummaries().list().execute()

    @property
    def _flow(self):
        return client.flow_from_clientsecrets(
            CLIENT_SECRETS_PATH, scope=SCOPES,
            message=tools.message_if_missing(CLIENT_SECRETS_PATH)
        )

    @property
    def _analytics(self):
        # Prepare credentials, and authorize HTTP object with them.
        # If the credentials don't exist or are invalid run through the native client
        # flow. The Storage object will ensure that if successful the good
        # credentials will get written back to a file.
        storage = file.Storage(self.cached_credential_path)
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(self._flow, storage)
        http = credentials.authorize(http=httplib2.Http())
        # Build the service object.
        analytics = build('analyticsreporting', 'v4', http=http)
        return analytics

    def get_report(self, view_id, start_date, end_date):
        # Use the Analytics Service Object to query the Analytics Reporting API V4.
        data_all = self._analytics.reports().batchGet(
            body={
                'reportRequests': [
                    {
                        'viewId': view_id,
                        #  'dateRanges': [{'startDate': '7daysAgo', 'endDate': 'today'}],
                        'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                        'dimensions': [{'name': 'ga:sourceMedium'}],
                        'metrics': [{'expression': 'ga:users'},
                                    {'expression': 'ga:newUsers'},
                                    {'expression': 'ga:sessions'},
                                    {'expression': 'ga:bounceRate'},
                                    {'expression': 'ga:pageviewsPerSession'},
                                    {'expression': 'ga:avgSessionDuration'},
                                    {'expression': 'ga:goalConversionRateAll'},
                                    {'expression': 'ga:goalCompletionsAll'},
                                    {'expression': 'ga:goalValueAll'}, ]
                    }]
            }
        ).execute()
        column_names = [data_all['reports'][0]['columnHeader']['dimensions'][0][3:]]
        for metrics in data_all['reports'][0]['columnHeader']['metricHeader'][
            'metricHeaderEntries']:
            column_names.append(metrics['name'][3:])

        metrics_all = []
        for metric in data_all['reports'][0]['data']['rows']:
            list_row = []
            list_row.append(metric['dimensions'][0])
            for ga_data in metric['metrics']:
                list_row.extend(ga_data['values'])
            metrics_all.append(list_row)
        df = pd.DataFrame(metrics_all, columns=column_names)

        return df

    def save_data_to_csv(self, view_id, start_date, end_date, dir="./"):
        df_main = self.get_report(view_id, start_date, end_date)
        filename = f"{dir}/{view_id}_{start_date}-{end_date}.csv"
        df_main.to_csv(filename, index=False)

    def get_sub_account(self) -> List[str]:
        user_summeries = self.get_summaries()
        return [account["id"] for account in user_summeries["items"]]

    def extract_connection_info(self) -> Dict[str, Any]:
        user_summeries = self.get_summaries()
        data = {
            "business_account": user_summeries.get("username", ""),
            "num_sub_account": len(user_summeries["items"]),
            "business_account_id": user_summeries.get("id", ""),
            "views": [item["profiles"][0]["id"] for a in user_summeries.get("items", []) for item in
                      a["webProperties"]]
        }
        return data


if __name__ == "__main__":
    ga = GoogleAnalyst()
    pprint(ga.get_summaries())
    # print(ga.extract_connection_info())
    # ga.save_data_to_csv(viewID="")

    # from google_auth_oauthlib.flow import InstalledAppFlow
    # from googleapiclient.discovery import build
    #
    # flow = InstalledAppFlow.from_client_secrets_file(
    #     CLIENT_SECRETS_PATH,
    #     scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email',
    #             'https://www.googleapis.com/auth/userinfo.profile'],
    #     # redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    # )
    # # print(flow.authorization_url())
    #
    # flow.run_local_server()
    # credentials = flow.credentials
    # #
    # # Optionally, view the email address of the authenticated user.
    # user_info_service = build('oauth2', 'v2', credentials=credentials)
    # user_info = user_info_service.userinfo().get().execute()
    # print(user_info)
