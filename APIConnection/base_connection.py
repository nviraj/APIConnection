from abc import ABC, abstractmethod
from typing import List, Dict

import pandas as pd
from pandas import DataFrame


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
    def get_report_df_for_account(
            self, account: str, start_date: str, end_date: str, dimensions: List[str]
    ) -> DataFrame:
        pass

    def get_sub_accounts_report_df(
            self, sub_accounts: List[str], start_date, end_date, dimensions
    ) -> DataFrame:
        final_df = pd.DataFrame()
        for account in sub_accounts:
            df = self.get_report_df_for_account(account, start_date, end_date, dimensions)
            df["account_id"] = account
            final_df = pd.concat([final_df, df])
        final_df.columns = [col.lower().replace(" ", "_") for col in final_df.columns]
        return final_df

    @staticmethod
    def save_df_to_csv(df: DataFrame, file_name: str, target_folder: str) -> None:
        df.to_csv(f"{target_folder}/{file_name}")
