# -*- coding: utf-8 -*-
import os
import errno
import time
import logging

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.adreportrun import AdReportRun
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.user import User
import pandas as pd
from .settings import AD_INSIGHT_FIELD
from .exceptions import FBTimeOut

logging.basicConfig(filename="fb.log", level=logging.DEBUG)

TIMEOUT = 100
FB_API_URL = "https://developers.facebook.com"
EXCLUDE_FB_ACC_INSIGHT_FIELDS = ["total_postbacks"]


class FBConnection:
    """Wrapper class for fetching/parsing FB endpoints"""

    def __init__(self, access_token=None):
        self.access_token = access_token
        FacebookAdsApi.init(access_token=access_token)
        user = User(fbid="me")
        self.accounts = list(user.get_ad_accounts())

    @staticmethod
    def get_ads_insights_reference_url():
        return f"{FB_API_URL}/docs/marketing-api/reference/ads-insights/"

    @staticmethod
    def get_ads_insights_variable_list():
        """Fetch insignt variables list"""
        fields_df = pd.read_csv(AD_INSIGHT_FIELD)
        fields = list(fields_df["Field 75"])
        return [field for field in fields if field not in EXCLUDE_FB_ACC_INSIGHT_FIELDS]

    def save_insight_ads_accounts_to_excel(
        self, start_date, end_date, path="./", fields=None
    ):
        """Save insight ads data to excel files

        Args:
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            path (str): path or directory
            fields (list(str)): fields list

        Returns:
            None
        """

        if not os.path.exists(path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

        for acc in self.accounts:
            try:
                self.save_insight_ads_data_for_account_to_excel(
                    acc["id"], start_date, end_date, f"{path}/{acc['id']}.xls", fields
                )
            except FBTimeOut:
                logging.error(f"TIMEOUT: Can not get data for account {acc['id']}")
            except Exception as e:
                logging.error(
                    f"ERROR: Can not get data for account {acc['id']}. Detail {e}"
                )

    def get_insight_ads_data_for_account(
        self, ad_account_id, start_date, end_date, fields
    ):
        """Fetch insight ads data for an account account

        Args:
            add_account_id (str): account ID
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            fields (list(str)): fields list

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
        account = AdAccount(ad_account_id)
        if fields is None:
            fields = FBConnection.get_ads_insights_variable_list()
        async_job = account.get_insights(fields=fields, params=params, is_async=True)

        result_cursor = self._wait_for_async_job(async_job)
        return [item for item in result_cursor]

    def save_insight_ads_data_for_account_to_excel(
        self, ad_account_id, start_date, end_date, file_path, fields=None
    ):
        """Save insight ads data to excel file

        Args:
            add_account_id (str): account ID
            start_date (str): string format of 'YYYY-MM-DD'
            end_date (str): string format of 'YYYY-MM-DD'
            path (str): path or directory
            fields (list(str)): fields list

        Returns:
            None
        """
        logging.info(f"Start processing account {ad_account_id}")
        if fields is None:
            fields = FBConnection.get_ads_insights_variable_list()
        data = self.get_insight_ads_data_for_account(
            ad_account_id, start_date, end_date, fields
        )
        df_insight = pd.DataFrame.from_dict(data)
        df_insight.to_excel(file_path, index=False, merge_cells=True)

    def _wait_for_async_job(self, job):
        for loop in range(TIMEOUT):
            if loop == TIMEOUT - 1:
                raise FBTimeOut
            time.sleep(2)
            job = job.api_get()
            status = job[AdReportRun.Field.async_status]
            if status == "Job Completed":
                return job.get_result()
