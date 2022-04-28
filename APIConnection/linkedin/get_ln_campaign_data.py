#!/usr/bin/python3
import time

import requests
import pandas
import sys
import json
from datetime import datetime, timedelta
import datetime
import re
import os

sys.path.insert(0, os.path.abspath("../.."))

from APIConnection.config import linkedin_config
from APIConnection.logger import get_logger

logger = get_logger(
    "linkedin", file_name=linkedin_config.LOG_FILE, log_level=linkedin_config.LOG_LEVEL
)


# Function for date validation
def date_validation(date_text):
    try:
        while date_text != datetime.datetime.strptime(date_text, '%Y-%m-%d').strftime('%Y-%m-%d'):
            date_text = input('Please Enter the date in YYYY-MM-DD format\t')
        else:
            return datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except:
        raise Exception('linkedin_campaign_processing : year does not match format yyyy-mm-dd')


def metrics_validation(metrics):
    if len(metrics) > 20:
        logger.error("Too many metrics, the number of metrics should be smaller than 20")
        return False
    return True


def get_LinkedIn_campaigns_list(access_token, account, camapign_type_json):
    try:
        url = "https://api.linkedin.com/v2/adCampaignsV2?q=search&search.account.values[0]=urn:li:sponsoredAccount:" + str(account)

        headers = {"Authorization": "Bearer " + access_token}
        # make the http call
        r = requests.get(url=url, headers=headers)
        # defining the dataframe
        campaign_data_df = pandas.DataFrame(columns=["campaign_name", "campaign_id", "campaign_account",
                                                     "daily_budget", "unit_cost", "objective_type", "campaign_status",
                                                     "campaign_type"])

        if r.status_code != 200:
            logger.error(f"get_linkedIn_campaigns_list function : something went wrong : {r}")
        else:
            response_dict = json.loads(r.text)
            if "elements" in response_dict:
                campaigns = response_dict["elements"]
                # logger.info(f"Total number of campain in account : {len(campaigns)}")
                # loop over each campaigns in the account
                i = 0
                for campaign in campaigns:
                    tmp_dict = {}
                    # for each campign check the status; ignor DRAFT campaign
                    if "status" in campaign and campaign["status"] != "DRAFT":
                        i = i + 1
                        try:
                            campaign_name = campaign["name"]
                        except:
                            campaign_name = "NA"
                        tmp_dict["campaign_name"] = campaign_name

                        try:
                            campaign_id = campaign["id"]
                        except:
                            campaign_id = "NA"
                        tmp_dict["campaign_id"] = campaign_id

                        try:
                            campaign_acct = campaign["account"]
                            campaign_acct = re.findall(r'\d+', campaign_acct)[0]
                        except:
                            campaign_acct = "NA"
                        tmp_dict["campaign_account"] = campaign_acct

                        try:
                            daily_budget = campaign["dailyBudget"]["amount"]
                        except:
                            daily_budget = None
                        tmp_dict["daily_budget"] = daily_budget

                        try:
                            unit_cost = campaign["unitCost"]["amount"]
                        except:
                            unit_cost = None
                        tmp_dict["unit_cost"] = unit_cost

                        try:
                            campaign_obj = campaign["objectiveType"]
                            if campaign_obj in camapign_type_json["off_site"]:
                                tmp_dict["campaign_type"] = "off_site"
                            elif campaign_obj in camapign_type_json["on_site"]:
                                tmp_dict["campaign_type"] = "on_site"
                            else:
                                logger.error(" ### campaign ObjectiveType doesnt match CampaignType references ###")
                        except:
                            campaign_obj = None
                            pass
                        tmp_dict["objective_type"] = campaign_obj

                        campaign_status = campaign["status"]
                        tmp_dict["campaign_status"] = campaign_status

                        campaign_data_df = campaign_data_df.append(tmp_dict, ignore_index=True)

                # logger.info(f"Total number of campain in account (status != DRAFT) : {i}")
                try:
                    campaign_data_df["daily_budget"] = pandas.to_numeric(campaign_data_df["daily_budget"])
                    campaign_data_df["unit_cost"] = pandas.to_numeric(campaign_data_df["unit_cost"])
                except:
                    pass
            else:
                logger.error("key *elements* nmissing in JSON data from LinkedIn")

            return campaign_data_df
    except:
        logger.exception("get_linked_campaigns_list Failed :", sys.exc_info())


def get_LinkedIn_campaign(account, access_token, campaigns_ids, s_date, e_date, qry_type):
    try:
        # calling date validation funtion for start_date format check
        startDate = date_validation(s_date)
        dt = startDate + timedelta(1)
        week_number = dt.isocalendar()[1]
        # calling date validation funtion for end_date format check
        endDate = date_validation(e_date)
        # defining the dataframe
        metrics = linkedin_config.REPORT_METRICS
        submetrics_set = []
        if len(metrics) > 20:
            n_submetrics = int(len(metrics) / 20)
            for n_s in range(n_submetrics):
                submetrics_set.append(metrics[20 * n_s: 20 * (n_s + 1)])
            if len(metrics) % 20 != 0:
                submetrics_set.append(metrics[20 * n_submetrics: len(metrics)])
        fields_str_set = []
        for submetrics in submetrics_set:
            fields_str = ','.join(submetrics)
            fields_str_set.append(fields_str)
        base_columns = ['account_id', 'account_name', 'campaign_id', 'start_date', 'end_date', 'week', 'month']
        campaign_analytics_data = pandas.DataFrame(columns=base_columns.extend(metrics))
        for cmp_id in campaigns_ids:
            campaigns_response_list = []
            for f_str in fields_str_set:
                # Building api query in form of url
                dateRange_start = "dateRange.start.day=" + str(startDate.day) + "&dateRange.start.month=" + str(
                    startDate.month) + "&dateRange.start.year=" + str(startDate.year)
                dateRange_end = "dateRange.end.day=" + str(endDate.day) + "&dateRange.end.month=" + str(
                    endDate.month) + "&dateRange.end.year=" + str(endDate.year)

                url = "https://api.linkedin.com/v2/adAnalyticsV2?q=analytics&pivot=CAMPAIGN&" + dateRange_start + "&" + dateRange_end + "&timeGranularity=ALL&campaigns[0]=urn:li:sponsoredCampaign:" + str(
                    cmp_id) + "&fields=" + str(f_str)
                # print(f"Querying data for with url: {url}")
                # defining header for authentication
                headers = {"Authorization": "Bearer " + access_token}
                # make the http call
                r = requests.get(url=url, headers=headers)

                if r.status_code != 200:
                    print(r.json())
                    logger.error(f"*get_LinkedIn_campaign : something went wrong : {r.text}")
                else:
                    response_dict = json.loads(r.text)
                    print(f"Campaign id = {cmp_id}")
                    print(f"Response = {response_dict}")
                    if "elements" in response_dict:
                        campaigns = response_dict["elements"]
                        if campaigns:
                            campaigns_response_list.append(campaigns)
                    else:
                        logger.error("\nkey *elements* nmissing in JSON data from LinkedIn")
                time.sleep(2.4)
            flag = False
            cmp_res_data = []
            for cmp_data_set in campaigns_response_list:
                for i, cmp_data in enumerate(cmp_data_set):
                    if not isinstance(cmp_data, dict):
                        print(type(cmp_data))
                        print(cmp_data)
                    if not flag:
                        cmp_res_data.append(cmp_data)
                    else:
                        if cmp_res_data:
                            cmp_res_data[i].update(cmp_data)
                    flag = True
            if cmp_res_data:
                for campaign in cmp_res_data:
                    tmp_dict = {}
                    tmp_dict["account_id"] = account['account_id']
                    tmp_dict["account_name"] = account['account_name']
                    tmp_dict["campaign_id"] = cmp_id
                    tmp_dict["start_date"] = startDate
                    tmp_dict["end_date"] = endDate
                    if qry_type in ["week", "weekly"]:
                        tmp_dict["week"] = week_number
                    elif qry_type in ["month", "monthly"]:
                        tmp_dict["month"] = startDate.month
                    for metric in metrics:
                        try:
                            if isinstance(campaign[metric], list) or isinstance(campaign[metric], dict):
                                tmp_dict[metric] = ""
                            else:
                                tmp_dict[metric] = campaign[metric]
                        except:
                            tmp_dict[metric] = ""
                    campaign_analytics_data = campaign_analytics_data.append(tmp_dict, ignore_index=True)

        return campaign_analytics_data
    except:
        logger.exception("\n*get_linked_campaigns_analytics Failed :", sys.exc_info())
