import asyncio

import pandas as pd

from APIConnection.facebook_connection import FBConnection
from APIConnection.settings import FB_ACCESS_TOKEN

if __name__ == "__main__":
    conn = FBConnection(access_token=FB_ACCESS_TOKEN)
    # print(conn.accounts)
    print(conn.get_sub_accounts())
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
    print(res1_res2)
    print(res3)
    pd.testing.assert_frame_equal(res1_res2.reset_index(drop=True), res3.reset_index(drop=True), check_dtype=False)
    # conn.save_insight_ads_accounts_to_excel(
    #     start_date="2022-01-01",
    #     end_date="2022-08-02",
    #     fields=["clicks", "conversions"],
    #     sub_account_ids=["act_27385599"]
    # )

