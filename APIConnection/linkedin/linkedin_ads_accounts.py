#!/usr/bin/python3
# command to run the code: python3 ./linkedin_ads_account.py
import requests
import json
import pandas
import sys


def get_linkedin_ads_account(access_token):
    try:
        account_ids = []
        url = "https://api.linkedin.com/v2/adAccountsV2?q=search&search.type.values[0]=BUSINESS&search.status.values[0]=ACTIVE"

        headers = {"Authorization": "Bearer " + access_token}
        # make the http call
        r = requests.get(url=url, headers=headers)

        if r.status_code != 200:
            print("\n ### something went wrong ### ", r)
        else:
            response_dict = json.loads(r.text)
            if "elements" in response_dict:
                accounts = response_dict["elements"]
                for acc in accounts:
                    account_id = acc["id"]
                    account_name = acc["name"]
                    account_currency = acc["currency"]
                    tmp_dict = {}
                    tmp_dict["account_id"] = account_id
                    tmp_dict["account_name"] = account_name
                    tmp_dict["account_currency"] = account_currency
                    account_ids.append(tmp_dict)
        return account_ids
    except:
        print("\n*** get_linkedin_ads account funtion Failed *** ", sys.exc_info())
        raise

def get_account_ids(cred_file):
    try:
        print("LinkedIn Ads Account data extraction process Starts")
        # loading and reading crdentials from JSON file.
        linkedin_cred = open(cred_file, 'r')
        cred_json = json.load(linkedin_cred)
        access_token = cred_json["client_name"]["access_token"]
        # call authentication function
        account_ids = get_linkedin_ads_account(access_token)

        return account_ids
        print("\nLinkedin Ads Account data extraction process Finished")
    except:
        print("\n*** Linkedin Ads Account data extraction processing Failed *** ", sys.exc_info())
        return []

if __name__ == '__main__':
    cred_file = "/home/steve/Desktop/datapal/linkedin_cred_1.json"
    get_account_ids(cred_file)