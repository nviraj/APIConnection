import asyncio

from APIConnection.facebook_connection import FBConnection
from APIConnection.settings import FB_ACCESS_TOKEN

if __name__ == "__main__":
    conn = FBConnection(access_token=FB_ACCESS_TOKEN)
    # print(conn.accounts)
    print(conn.get_sub_accounts())
    res = asyncio.get_event_loop().run_until_complete(
        asyncio.gather(
            conn.get_sub_accounts_report_df(
                start_date="2022-01-01",
                end_date="2022-11-12",
                dimensions=["clicks", "conversions"],
                sub_accounts=["act_27385599"]
            ),
            conn.get_sub_accounts_report_df(
                start_date="2021-01-01",
                end_date="2021-12-30",
                dimensions=["clicks", "conversions"],
                sub_accounts=["act_27385599"]
            ),
        )
    )
    print(res)
    # conn.save_insight_ads_accounts_to_excel(
    #     start_date="2022-01-01",
    #     end_date="2022-08-02",
    #     fields=["clicks", "conversions"],
    #     sub_account_ids=["act_27385599"]
    # )

