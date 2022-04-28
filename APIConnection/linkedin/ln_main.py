#!/usr/local/bin/python3
# command to run this code $ python3 ./file_directory/ln_main.py -c client_name -d ./filePath/ln_cred.config -s 2020-07-05(startDate) -e 2020-07-11(endDate) -q week/month
import getopt
import sys
import datetime
import os.path
import pandas as pd

from .get_ln_campaign_data import *
from .linkedin_ads_accounts import *

sys.path.insert(0, os.path.abspath("../.."))

from APIConnection.config import linkedin_config
from APIConnection.logger import get_logger

logger = get_logger(
    "linkedin", file_name=linkedin_config.LOG_FILE, log_level=linkedin_config.LOG_LEVEL
)


def isFile(fileName):
    if (not os.path.isfile(fileName)):
        raise ValueError("You must provide a valid filename as parameter")


class Linkedin(object):
    def __init__(self, client_name, cred, output, s_date, e_date, query_type):
        self.client_name = client_name
        self.cred = cred
        self.output = output
        self.s_date = s_date
        self.e_date = e_date
        self.query_type = query_type

    def ln_main(self):
        try:
            timestamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d : %H:%M')
            logger.info(f"DATE : {timestamp}")
            logger.info("LinkedIn data extraction process Started")
            # reading LinkedIn credential json file
            cred_file_path = open(self.cred, 'r')
            logger.info(f"Creadential path = {self.cred}")
            cred_json = json.load(cred_file_path)

            # reading campaign type reference json file
            camapign_type_json = linkedin_config.CAMPAIGN_CATEGORY

            # Initializing variable with data from cred file
            org_id = cred_json[self.client_name]["id"]
            access_token = cred_json[self.client_name]["access_token"]
            app_id = cred_json[self.client_name]["client_id"]
            app_secret = cred_json[self.client_name]["client_secret"]
            accounts = get_account_ids(self.cred)

            now = datetime.datetime.now()  # current date and time
            date_time = now.strftime("%Y_%m_%d-%H%M%S")
            report_filename = date_time + ".csv"
            report_output_file = os.path.join(self.output, report_filename)
            os.system(f"mkdir -p {self.output}")

            # call the LinkedIn API query function (i.e get_linkedin_campaign_data)
            # i = 0
            for account in accounts:
                # i += 1
                # if i == 3:
                #     break
                print(f"ACCOUNT = {account}")
                ln_campaign_df = get_LinkedIn_campaigns_list(access_token, account['account_id'], camapign_type_json)

                if not ln_campaign_df.empty:
                    # get campaign analytics data
                    campaign_ids = ln_campaign_df["campaign_id"]
                    ln_campaign_analytics = get_LinkedIn_campaign(account, access_token, campaign_ids, self.s_date, self.e_date, self.query_type)
                    # Stack the DataFrames on top of each other
                    with open(report_output_file, 'a') as f:
                        ln_campaign_analytics.to_csv(f, sep='\t', header=f.tell() == 0, index=False)
                    # print("\nLinkedIn campaigns analytics :\n", ln_campaign_analytics)
                else:
                    logger.error(f"!!Dataframe (campaigns_df) of account with id {account['account_id']} is empty !!!")

            logger.info("LN_MAIN : LinkedIn data extraction Process Finished \n")
        except:
            logger.error("LN_MAIN : LinkedIn data extraction processing Failed !!!!:", sys.exc_info())
