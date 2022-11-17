import asyncio
from unittest import TestCase

import pandas as pd

from APIConnection.facebook_connection import FBConnection
from APIConnection.logger import logger
from APIConnection.settings import FB_ACCESS_TOKEN
from APIConnection.utils import timeit, Monitor


class ConnectionTesting(TestCase):

    def test_combine_report_by_date_fb(self):
        conn = FBConnection(access_token=FB_ACCESS_TOKEN)
        res1, res2, res3 = asyncio.get_event_loop().run_until_complete(
            asyncio.gather(
                conn.get_sub_accounts_report_df(
                    start_date="2022-01-01",
                    end_date="2022-06-01",
                    dimensions=["clicks", "conversions"],
                    sub_accounts=["act_27385599"]
                ),
                conn.get_sub_accounts_report_df(
                    start_date="2022-06-02",
                    end_date="2022-11-14",
                    dimensions=["clicks", "conversions"],
                    sub_accounts=["act_27385599"]
                ),
                conn.get_sub_accounts_report_df(
                    start_date="2022-01-01",
                    end_date="2022-11-14",
                    dimensions=["clicks", "conversions"],
                    sub_accounts=["act_27385599"]
                ),
            )
        )
        res1_res2 = pd.concat([res1, res2])
        logger.debug(res1_res2)
        logger.debug(res3)
        pd.testing.assert_frame_equal(
            res1_res2.reset_index(drop=True),
            res3.reset_index(drop=True),
            check_dtype=False
        )

    def test_save_data_to_file_fb(self):
        conn = FBConnection(access_token=FB_ACCESS_TOKEN)
        conn.save_insight_ads_accounts_to_excel(
            start_date="2022-01-01",
            end_date="2022-08-02",
            fields=["clicks", "conversions"],
            sub_account_ids=["act_27385599"]
        )

    @timeit
    def test_run_full_report_account(self):
        conn = FBConnection(access_token=FB_ACCESS_TOKEN)
        loop = asyncio.get_event_loop()
        # m = Monitor()
        # asyncio.run(m.monitor_loop(loop))
        # loop.set_debug(True)
        df = loop.run_until_complete(conn.get_sub_accounts_report_df(
            sub_accounts=[s["id"] for s in conn.get_sub_accounts()][:],
            start_date="2022-01-01",
            end_date="2022-11-15",
            dimensions=None
        ))
        logger.debug(df.head(10))
        assert df.empty is False
