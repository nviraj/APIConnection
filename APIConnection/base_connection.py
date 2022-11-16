import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List

import pandas as pd
from pandas import DataFrame

from APIConnection.utils import Monitor, timeit


class BaseConnection(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_sub_accounts(self) -> List[Dict]:
        pass

    @abstractmethod
    def extract_connection_info(self) -> Dict:
        pass

    @abstractmethod
    @timeit
    async def get_report_df_for_account(
        self, account: str, start_date: str, end_date: str, dimensions: List[str]
    ) -> DataFrame:
        pass

    async def get_sub_accounts_report_df(
        self, sub_accounts: List[str], start_date, end_date, dimensions
    ) -> DataFrame:
        final_df = pd.DataFrame()
        # for account in sub_accounts:
        #     logger.debug(f"Process {account}")
        m = Monitor()
        loop = asyncio.get_running_loop()
        tasks = [m.monitor_loop(loop)]
        tasks += [
            self.get_report_df_for_account(a, start_date, end_date, dimensions)
            for a in sub_accounts
        ]
        dfs = await asyncio.gather(*tasks)
        for df in dfs:
            # df = await self.get_report_df_for_account(account, start_date, end_date, dimensions)
            if not df.empty:
                final_df = pd.concat([final_df, df])
        final_df.columns = [col.lower().replace(" ", "_") for col in final_df.columns]
        return final_df

    @staticmethod
    def save_df_to_csv(df: DataFrame, file_name: str, target_folder: str) -> None:
        df.to_csv(f"{target_folder}/{file_name}")
