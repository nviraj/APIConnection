# -*- coding: utf-8 -*-
import datetime
import errno
import logging
import os
from abc import ABC
from collections import defaultdict
from typing import List, Dict

import pandas as pd
import requests
import tweepy
from twitter_ads import API_VERSION
from twitter_ads.campaign import Campaign
from twitter_ads.client import Client
from twitter_ads.enum import METRIC_GROUP, GRANULARITY, PLACEMENT
from twitter_ads.utils import split_list

from APIConnection.base_connection import BaseConnection
from APIConnection.exceptions import TwitterTimeout
from APIConnection.settings import (
    TWITTER_ACCESS_TOKEN,
    TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN_SECRET,
)

# logging.basicConfig(filename="twitter.log", level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

TIMEOUT = 100
API_URL = "https://ads-api.twitter.com"
MAX_HANDLING_IDENTITIES = 20
DEFAULT_METRIC_GROUPS = [METRIC_GROUP.ENGAGEMENT, METRIC_GROUP.BILLING, METRIC_GROUP.VIDEO]

granularity = GRANULARITY.DAY
placement = [PLACEMENT.ALL_ON_TWITTER, PLACEMENT.PUBLISHER_NETWORK]


class TwitterConnection(BaseConnection):
    """Wrapper class for fetching/parsing Twitter endpoints"""

    def __init__(
            self,
            key: str = TWITTER_CONSUMER_KEY,
            secret: str = TWITTER_CONSUMER_SECRET,
            token: str = TWITTER_ACCESS_TOKEN,
            token_secret: str = TWITTER_ACCESS_TOKEN_SECRET
    ):
        self.consumer_key = key
        self.secret = secret
        self.token = token
        self.token_secret = token_secret
        # initialize the client
        self.client = Client(
            self.consumer_key,
            self.secret,
            self.token,
            self.token_secret
        )
        self.accounts = self.get_sub_accounts()
        self.user_api = self.tw_user_api()

    def tw_user_api(self):
        auth = tweepy.OAuthHandler(self.consumer_key, self.secret)
        auth.set_access_token(self.token, self.token_secret)
        api = tweepy.API(auth)
        return api

    def _get_bearer_token(self) -> str:
        response = requests.post(
            "https://api.twitter.com/oauth2/token",
            auth=(self.consumer_key, self.secret),
            data={"grant_type": "client_credentials"},
        )

        if response.status_code != 200:
            raise Exception(
                f"Cannot get a Bearer token (HTTP %d): %s"
                % (response.status_code, response.text)
            )

        body = response.json()
        return body["access_token"]

    @staticmethod
    def get_supported_metrics_group():
        return [name for name in dir(METRIC_GROUP) if not name.startswith('_')]

    def get_accounts(self):
        url = f"{API_URL}/{API_VERSION}/accounts/"
        response = requests.get(url,
                                headers={"Authorization": f"Bearer {self._get_bearer_token()}"})

        if response.status_code != 200:
            raise Exception(
                f"Cannot get a Bearer token (HTTP %d): %s"
                % (response.status_code, response.text)
            )

        body = response.json(
            # 10
        )
        return body

    def get_sub_accounts(self) -> List[Dict]:
        """

        Returns: list of ad account id

        """
        return [{"id": acc.id, "name": acc.name} for acc in list(self.client.accounts())]

    def save_insight_ads_accounts_to_excel(self, start_date, end_date, metrics_group,
                                           output_dir="./"):
        """Save insight ads data to excel files

        Args:
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            output_dir (str): output dir
            metrics_group
        Returns:
            None
        """

        if not os.path.exists(output_dir):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), output_dir)

        for acc in self.accounts:
            try:
                self.save_insight_ads_data_for_account_to_excel(
                    acc, start_date, end_date, metrics_group, f"{output_dir}/{acc}.xls"
                )
            except TwitterTimeout:
                logging.error(f"TIMEOUT: Can not get data for account {acc}")
            except Exception as e:
                logging.error(f"ERROR: Can not get data for account {acc}. Detail {e}")
                raise e

    @staticmethod
    def convert_analysis_data_to_df(campaign_data: Dict, analytics_data: Dict) -> pd.DataFrame:
        res = []
        for data in analytics_data:
            row = {}
            id = data["id"]
            try:
                metrics = data["id_data"][0]["metrics"]
                row["Time period"] = str(data["time_period"])
                row["Date start"] = str(data["date_start"])
                row["Date stop"] = str(data["date_stop"])
                row["Campaign name"] = campaign_data[id]["name"]
                row["Campaign id"] = campaign_data[id]["id"]

                if campaign_data[id]["objective"] == "VIDEO_VIEWS":
                    row["Objective"] = "Video views"
                elif campaign_data[id]["objective"] == "CUSTOM":
                    row["Objective"] = "Custom"
                elif campaign_data[id]["objective"] == "ENGAGEMENTS":
                    row["Objective"] = "Engagements"
                elif campaign_data[id]["objective"] == "WEBSITE_CLICKS":
                    row["Objective"] = "Website clicks"

                row["Status"] = campaign_data[id]["status"]
                row["Account name"] = campaign_data[id]["account_name"]
                row["Campaign start"] = campaign_data[id]["start_time"]
                row["Campaign end"] = campaign_data[id]["end_time"]
                row["Total budget"] = campaign_data[id][
                    "total_budget_amount_local_micro"
                ]
                row["Impressions"] = (
                    sum(metrics["impressions"]) if metrics["impressions"] else 0
                )
                row["clicks"] = (
                    sum(metrics["clicks"]) if metrics["clicks"] else 0
                )
                row["Spend"] = (
                    sum(metrics["billed_charge_local_micro"])
                    if metrics["billed_charge_local_micro"]
                    else 0
                )
                row["Results"] = (
                    sum(metrics["url_clicks"]) if metrics["url_clicks"] else 0
                )
                if "Objective" in row:
                    if row["Objective"] == "Website clicks":
                        row["Result type"] = "Link clicks"
                    elif row["Objective"] == "Video views":
                        row["Result type"] = "Video views"
                    elif row["Objective"] in ["Engagements", "Custom"]:
                        row["Result type"] = "Tweet engagements"
                else:
                    row["Result type"] = ""

                row["Result rate"] = (
                        100 * row["Results"] / (1.0e-6 + row["Impressions"])
                )
                row["Result rate type"] = (
                    row["Result type"] + " rate" if "Result type" in row else ""
                )
                row["Cost per Result"] = row["Spend"] / (1.0e-6 + row["Results"])
                row["Cost per result type"] = (
                    f"Cost per {row['Result type']}" if "Result type" in row else ""
                )
                row["Daily budget"] = campaign_data[id][
                    "daily_budget_amount_local_micro"
                ]
                res.append(row)
            except Exception as e:
                raise e

        df_insight = pd.DataFrame(res)
        return df_insight

    def get_report_df_for_account(
            self, account: str, start_date: str, end_date: str, dimensions: List[str]
    ) -> pd.DataFrame:
        campaign_data, analytics_data = self.fetch_analytic_data_for_account(
            account, start_date, end_date, dimensions
        )
        df = self.convert_analysis_data_to_df(campaign_data, analytics_data)
        df["account_id"] = account
        return df

    def save_insight_ads_data_for_account_to_excel(
            self, account_id, start_date, end_date, metrics_group, file_path
    ):
        """Save insight ads data to excel file

        Args:
            account_id (str): account ID
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            metrics_group :
            file_path:

        Returns:
            None
        """
        logging.info(f"Start processing account {account_id}")
        campaign_data, analytics_data = self.fetch_analytic_data_for_account(
            account_id, start_date, end_date, metrics_group
        )
        df_insight = self.convert_analysis_data_to_df(campaign_data, analytics_data)
        df_insight.to_excel(file_path, index=False, merge_cells=True)

    def fetch_analytic_data_for_account(
            self, account_id: str, start_date: str, end_date: str,
            metrics_group=None
    ):
        """Fetch insight ads data for an account account

        Args:
            account_id (str): account ID
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            metrics_group (list(str)): fields list

        Returns:
            (:obj: `list`)
        """
        if metrics_group is None:
            metrics_group = DEFAULT_METRIC_GROUPS
        account = self.client.accounts(account_id)
        campaign_data = defaultdict(dict)

        for campaign in account.campaigns():
            line_items = list(account.line_items(None, campaign_ids=campaign.id))
            campaign_data[campaign.id]["name"] = campaign.name
            campaign_data[campaign.id]["id"] = campaign.id
            campaign_data[campaign.id]["account_name"] = account.name
            campaign_data[campaign.id]["start_time"] = campaign.start_time
            campaign_data[campaign.id]["end_time"] = campaign.end_time
            campaign_data[campaign.id][
                "daily_budget_amount_local_micro"
            ] = campaign.daily_budget_amount_local_micro
            campaign_data[campaign.id][
                "total_budget_amount_local_micro"
            ] = campaign.total_budget_amount_local_micro
            campaign_data[campaign.id][
                "reasons_not_servable"
            ] = campaign.reasons_not_servable
            if line_items:
                campaign_data[campaign.id]["objective"] = line_items[0].objective
                campaign_data[campaign.id]["status"] = line_items[0].entity_status

        ids = list(map(lambda x: x.id, account.campaigns()))

        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        analytics_data = []
        while start < end:
            for row in self._fetch_line_item_data(
                    account, ids, start, start + datetime.timedelta(hours=24), metrics_group
            ):
                row["time_period"] = start
                row["date_start"] = start.strftime("%Y-%m-%d")
                row["date_stop"] = start.strftime("%Y-%m-%d")
                analytics_data.append(row)
            start = start + datetime.timedelta(hours=24)

        return campaign_data, analytics_data

    def _fetch_line_item_data(self, account, ids, start_date, end_date, metrics_group):
        """
        Fetch analytics data

        Args:
            account (obj): account object
            ids (list(string)): list of identities under the account
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'

        Returns:
            (:obj: `list`)
        """
        kwargs = {
            "granularity": granularity,
            "placement": placement,
            "start_time": start_date,
            "end_time": end_date,
        }
        sync_data = []
        # Sync/Async endpoint can handle max 20 entity IDs per request
        # so split the ids list into multiple requests
        for chunk_ids in split_list(ids, MAX_HANDLING_IDENTITIES):
            try:
                sync_data += Campaign.all_stats(
                    account, chunk_ids, metrics_group, **kwargs
                )
            except Exception as e:
                logging.error(e)
                raise e
        return sync_data

    def extract_connection_info(self):
        user = self.tw_user_api().verify_credentials()
        data = {
            "login_account": user.name,
            "num_sub_account": len(self.accounts),
            "login_account_id": user.id
        }
        return data


if __name__ == "__main__":
    tw = TwitterConnection()
    # print(tw.get_sub_accounts())
    data = tw.get_sub_accounts_report_df(
        ["kgs38", "61lmup"], "2022-08-15", "2022-08-20", ["ENGAGEMENT", "BILLING"])
    print(data[["clicks", "date_start", "campaign_id", "campaign_name"]])
    # print(tw.get_supported_metrics_group())
