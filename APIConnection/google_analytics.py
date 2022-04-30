import argparse
import logging

from apiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools
import pandas as pd

from .settings import GOOGLE_ANALYST_CRED

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
CLIENT_SECRETS_PATH = '/Users/giangb/projects/APIConnection/client_secret_desktop.json' # Path to client_secrets.json file.
# VIEW_ID = '107519727'


# logging.basicConfig(filename="google_analyst.log", level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


class GoogleAnalyst:
    """Wrapper class for fetching/parsing GoogleAnalyst endpoints"""

    def __init__(self):
      self.client = client.flow_from_clientsecrets(
        CLIENT_SECRETS_PATH, scope=SCOPES,
        message=tools.message_if_missing(CLIENT_SECRETS_PATH))
    
    @property
    def _flow(self):
      return client.flow_from_clientsecrets(
        CLIENT_SECRETS_PATH, scope=SCOPES,
        message=tools.message_if_missing(CLIENT_SECRETS_PATH))

    @property
    def _analytics(self):
      # Prepare credentials, and authorize HTTP object with them.
      # If the credentials don't exist or are invalid run through the native client
      # flow. The Storage object will ensure that if successful the good
      # credentials will get written back to a file.
      storage = file.Storage('analyticsreporting.dat')
      credentials = storage.get()
      if credentials is None or credentials.invalid:
        credentials = tools.run_flow(self._flow, storage, [])
      http = credentials.authorize(http=httplib2.Http())

      # Build the service object.
      analytics = build('analyticsreporting', 'v4', http=http)

      return analytics

    def get_report(self, viewID, start_date, end_date):
    # Use the Analytics Service Object to query the Analytics Reporting API V4.
      data_all=self._analytics.reports().batchGet(
        body={
          'reportRequests': [
          {
            'viewId': viewID,
            #  'dateRanges': [{'startDate': '7daysAgo', 'endDate': 'today'}],
            'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
            'dimensions':[{'name':'ga:sourceMedium'}],
            'metrics': [{'expression': 'ga:users'},{'expression': 'ga:newUsers'},{'expression': 'ga:sessions'},{'expression': 'ga:bounceRate'},{'expression': 'ga:pageviewsPerSession'},
                        {'expression': 'ga:avgSessionDuration'},{'expression': 'ga:goalConversionRateAll'},{'expression': 'ga:goalCompletionsAll'},{'expression': 'ga:goalValueAll'},]
          }]
        }
      ).execute()
      column_names=[data_all['reports'][0]['columnHeader']['dimensions'][0][3:]]
      for metrics in data_all['reports'][0]['columnHeader']['metricHeader']['metricHeaderEntries']:
          column_names.append(metrics['name'][3:])
          
      metrics_all=[]
      for metric in  data_all['reports'][0]['data']['rows']:
          list_row=[]
          list_row.append(metric['dimensions'][0])
          for ga_data in metric['metrics']:
              list_row.extend(ga_data['values'])
          metrics_all.append(list_row)
      df=pd.DataFrame(metrics_all, columns = column_names)

      return df
    
    def save_data_to_csv(self, viewID, start_date, end_date, dir="./"):
      df_main = self.get_report(viewID, start_date, end_date)
      filename = f"{dir}/{viewID}_{start_date}-{end_date}.csv"
      df_main.to_csv(filename, index=False)

    
