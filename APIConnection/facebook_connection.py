# -*- coding: utf-8 -*-
import asyncio
import errno
import logging
import os
import time
from abc import ABC
from typing import Dict, List

import pandas as pd
from facebook import GraphAPI
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adreportrun import AdReportRun
from facebook_business.adobjects.user import User
from facebook_business.api import FacebookAdsApi
from pandas import DataFrame

from APIConnection.base_connection import BaseConnection
from APIConnection.exceptions import FBTimeOut
from APIConnection.settings import AD_INSIGHT_FIELD, FB_ACCESS_TOKEN
from APIConnection.utils import timeit

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

TIMEOUT = 60 * 5
FB_API_URL = "https://developers.facebook.com"
EXCLUDE_FB_ACC_INSIGHT_FIELDS = ["total_postbacks"]


class FBConnection(BaseConnection):
    """Wrapper class for fetching/parsing FB endpoints"""

    def __init__(self, access_token=None):
        self.access_token = access_token
        FacebookAdsApi.init(access_token=access_token)
        self.user = User(fbid="me")
        self.accounts = list(self.user.get_ad_accounts(fields=["id", "name"]))

    def get_sub_accounts(self) -> List[Dict]:
        """
        Get all list id of subaccounts
        Returns:

        """
        ans = []
        for account in self.accounts:
            ans.append({"id": account["id"], "name": account["name"]})
        return ans

    @staticmethod
    def get_ads_insights_reference_url():
        return f"{FB_API_URL}/docs/marketing-api/reference/ads-insights/"

    @staticmethod
    def get_ads_insights_variable_list():
        """Fetch insignt variables list"""
        fields_df = pd.read_csv(AD_INSIGHT_FIELD)
        fields = list(fields_df["Field 75"])
        return [field for field in fields if field not in EXCLUDE_FB_ACC_INSIGHT_FIELDS]

    @timeit
    async def get_report_df_for_account(
            self, account: str, start_date: str, end_date: str, dimensions: List[str]
    ) -> DataFrame:
        """Fetch insight ads data for an account account

        Args:
            account (str): account ID
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            dimensions (list(str)): fields list

        Returns:
            (:obj: `list`)
        """
        params = {
            "time_range": {"since": start_date, "until": end_date},
            "filtering": [],
            "level": "account",
            "time_increment": 1,
            "breakdowns": [],
        }
        try:
            account = AdAccount(account)
            if dimensions is None:
                dimensions = FBConnection.get_ads_insights_variable_list()
            async_job = account.get_insights(fields=dimensions, params=params, is_async=True)
            result_cursor = await self.wait_for_async_job(async_job)
            data = [item for item in result_cursor]
            return pd.DataFrame(data)
        except FBTimeOut:
            logging.error(f"TIMEOUT: Can not get data for account {account}")
            return pd.DataFrame()
        except Exception as e:
            logging.error(
                f"ERROR: Can not get data for account {account}. Detail {e}"
            )
            return pd.DataFrame()

    def save_insight_ads_accounts_to_excel(
            self, start_date, end_date, path="./", fields=None, sub_account_ids=None
    ):
        """Save insight ads data to excel files

        Args:
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            path (str): path or directory
            fields (list(str)): fields list
            sub_account_ids:
        Returns:
            None
        """

        if sub_account_ids is None:
            sub_account_ids = [s["id"] for s in self.get_sub_accounts()]

        if not os.path.exists(path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

        for id in sub_account_ids:
            if id in self.get_sub_accounts():
                self.save_insight_ads_data_for_account_to_excel(
                    id, start_date, end_date, f"{path}/{id}.xls", fields
                )

    async def save_insight_ads_data_for_account_to_excel(
            self, ad_account_id, start_date, end_date, file_path, fields=None
    ):
        """Save insight ads data to excel file

        Args:
            ad_account_id (str): account ID
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            file_path (str): path or directory
            fields (list(str)): fields list

        Returns:
            None
        """
        logging.info(f"Start processing account {ad_account_id}")
        if fields is None:
            fields = FBConnection.get_ads_insights_variable_list()
        df_insight = await self.get_report_df_for_account(
            ad_account_id, start_date, end_date, fields
        )
        if df_insight:
            df_insight.to_excel(file_path, index=False, merge_cells=True)

    @staticmethod
    async def wait_for_async_job(job):
        for loop in range(TIMEOUT):
            if loop == TIMEOUT - 1:
                raise FBTimeOut
            await asyncio.sleep(2)
            job = job.api_get()
            status = job[AdReportRun.Field.async_status]
            if status == "Job Completed":
                return job.get_result()

    def extract_connection_info(self):
        graph = GraphAPI(self.access_token)
        user_info = graph.get_object("me", fields="id,name,email")
        data = {
            "login_account": user_info.get("email", ""),
            "num_sub_account": len(self.get_sub_accounts()),
            "login_account_id": user_info.get("id", "")
        }
        return data
