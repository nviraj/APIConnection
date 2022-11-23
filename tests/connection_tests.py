import asyncio

import pandas as pd

from APIConnection.config.dv360_config import REPORT_METRICS
from APIConnection.facebook_connection import FBConnection
from APIConnection.logger import logger
from APIConnection.settings import FB_ACCESS_TOKEN
from APIConnection.tradedesk import TTDConnection
from APIConnection.twitter import TwitterConnection
from APIConnection.utils import timeit, Monitor
from build.lib.APIConnection.dv360 import DV360


def test_combine_report_by_date_fb():
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


def test_save_data_to_file_fb():
    conn = FBConnection(access_token=FB_ACCESS_TOKEN)
    conn.save_insight_ads_accounts_to_excel(
        start_date="2022-01-01",
        end_date="2022-08-02",
        fields=["clicks", "conversions"],
        sub_account_ids=["act_27385599"]
    )


@timeit
def test_run_full_report_account():
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


def test_trade_desk():
    ttd = TTDConnection(
        username="ttd_api2_tm90ejd@coegi.com",
        password="Coegi2018!"
    )
    logger.info(ttd.login())
    logger.info(ttd.extract_connection_info())
    accounts = ttd.get_sub_accounts()
    # urls = ttd.get_reports(
    #     partner_id=accounts[0]["id"],
    #     start_date="2022-09-01",
    #     end_date="2022-09-02",
    #     directory="./report",
    #     get_urls_only=True
    # )
    # logger.info(urls)
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
    logger.info(df)


def test_dv360():
    # Retrieve command line arguments.
    # flags = samples_util.get_arguments(sys.argv, __doc__, parents=[argparser])
    with open("credential_cached_storage/cached_auth.dat", "r") as f:
        content = f.read()
    dv360 = DV360(
        frequency="ONE_TIME",
        date_range="CURRENT_DAY",
        report_window=24,
        cached_credential=content
    )

    # LIST QUERIES, USERS
    # logger.info(dbm_service_object)
    # logger.info(dv360.dbm_service.queries().listqueries().execute())
    # logger.info(dv360.dv360_service.users().list().execute())

    # GET REPORTS
    logger.info(dv360.extract_connection_info())
    df = dv360.get_sub_accounts_report_df(
        [], "CURRENT_DAY", REPORT_METRICS
    )
    logger.info(df)
    logger.info(df[["clicks", "impressions", "spend"]])
    # df.to_csv("dv360.csv")

    # query_id = dv360.create_report()
    # plogger.info(query_id)
    # query_id = 1000669689
    # plogger.info(dv360.dbm_service.queries().getquery(queryId=query_id).execute())
    # df = dv360.dbm_service.get_full_report_df(query_id)
    # df = pd.read_csv(
    #     "/home/quydx/datapal/datapal-compose/submodules/APIConnection/APIConnection/2022_09_17-172722.csv"
    # )
    # logger.info(df)
    # logger.info(df.info())


def test_tw():
    if __name__ == "__main__":
        tw = TwitterConnection()
        # logger.info(tw.get_sub_accounts())
        data = tw.get_sub_accounts_report_df(
            ["kgs38", "61lmup"], "2022-08-15", "2022-08-20", ["ENGAGEMENT", "BILLING"])
        logger.info(data[["clicks", "date_start", "campaign_id", "campaign_name"]])
        # logger.info(tw.get_supported_metrics_group())
