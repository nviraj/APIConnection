# -*- coding: utf-8 -*-
import argparse
import sys
import logging

import pandas as pd
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from .settings import GOOGLE_ADS_YAML, GOOGLE_ADS_FIELDS

QUERY_TABLE = "campaign"
FILTER_FIELD = "segments.date"

logging.basicConfig(filename="google_ads.log", level=logging.DEBUG)


class GoogleAds:
    """Wrapper class for fetching/parsing Googleads endpoints"""

    def __init__(self, main_manager_account="5674143645"):
        self.main_manager_account = main_manager_account

        self.googleads_client = GoogleAdsClient.load_from_storage(
            GOOGLE_ADS_YAML, version="v8"
        )
        self.googleads_service = self.googleads_client.get_service("GoogleAdsService")

        self.yaml_file = self._change_customer_id_yaml(
            GOOGLE_ADS_YAML, self.main_manager_account
        )

    def _change_customer_id_yaml(self, yaml_file, customer):
        with open(yaml_file, "r") as yaml:
            lines = yaml.readlines()
            index = [i for i, s in enumerate(lines) if "login_customer_id:" in s]
            lines[index[0]] = "login_customer_id: " + str(customer) + "\n"
        with open(yaml_file, "w") as yaml_w:
            for ln in lines:
                yaml_w.write(ln)
        return yaml_file

    def get_all_customer_ids(self):
        """retrieve all customer ids"""
        list_customers = []
        customer_service = self.googleads_client.get_service("CustomerService")
        accessible_customers = customer_service.list_accessible_customers()
        resource_names = accessible_customers.resource_names
        for resource_name in resource_names:
            list_customers.append(resource_name[-10:])
        return list_customers

    def get_list_acc(self, client, login_customer_id=None):
        """Gets the account hierarchy of the given MCC and login customer ID.

        Args:
          client: The Google Ads client.
          login_customer_id: Optional manager account ID. If none provided, this
          method will instead list the accounts accessible from the
          authenticated Google Ads account.
        """

        # Gets instances of the GoogleAdsService and CustomerService clients.
        googleads_service = client.get_service("GoogleAdsService")
        customer_service = client.get_service("CustomerService")

        # A collection of customer IDs to handle.
        seed_customer_ids = []
        # Creates a query that retrieves all child accounts of the manager
        # specified in search calls below.
        query = """
            SELECT
              customer_client.client_customer,
              customer_client.level,
              customer_client.manager,
              customer_client.descriptive_name,
              customer_client.currency_code,
              customer_client.time_zone,
              customer_client.id
            FROM customer_client
            WHERE customer_client.level <= 1"""

        # If a Manager ID was provided in the customerId parameter, it will be
        # the only ID in the list. Otherwise, we will issue a request for all
        # customers accessible by this authenticated Google account.
        if login_customer_id is not None:
            seed_customer_ids = [login_customer_id]
        else:
            print(
                "No manager ID is specified. The example will print the "
                "hierarchies of all accessible customer IDs."
            )

            customer_resource_names = (
                customer_service.list_accessible_customers().resource_names
            )

            for customer_resource_name in customer_resource_names:
                customer = customer_service.get_customer(
                    resource_name=customer_resource_name
                )
                print(customer.id)
                seed_customer_ids.append(customer.id)

        for seed_customer_id in seed_customer_ids:
            # Performs a breadth-first search to build a Dictionary that maps
            # managers to their child accounts (customerIdsToChildAccounts).
            unprocessed_customer_ids = [seed_customer_id]
            customer_ids_to_child_accounts = dict()
            root_customer_client = None

            while unprocessed_customer_ids:
                customer_id = int(unprocessed_customer_ids.pop(0))
                response = googleads_service.search(
                    customer_id=str(customer_id), query=query
                )

                # Iterates over all rows in all pages to get all customer
                # clients under the specified customer's hierarchy.
                for googleads_row in response:
                    customer_client = googleads_row.customer_client

                    # The customer client that with level 0 is the specified
                    # customer.
                    if customer_client.level == 0:
                        if root_customer_client is None:
                            root_customer_client = customer_client
                        continue

                    # For all level-1 (direct child) accounts that are a
                    # manager account, the above query will be run against them
                    # to create a Dictionary of managers mapped to their child
                    # accounts for printing the hierarchy afterwards.
                    if customer_id not in customer_ids_to_child_accounts:
                        customer_ids_to_child_accounts[customer_id] = []

                    customer_ids_to_child_accounts[customer_id].append(customer_client)

                    if customer_client.manager:
                        # A customer can be managed by multiple managers, so to
                        # prevent visiting the same customer many times, we
                        # need to check if it's already in the Dictionary.
                        if (
                            customer_client.id not in customer_ids_to_child_accounts
                            and customer_client.level == 1
                        ):
                            unprocessed_customer_ids.append(customer_client.id)

        # google_dict=customer_ids_to_child_accounts
        dict_acc = {}
        customer_id = customer_client.id

        for key in customer_ids_to_child_accounts.keys():
            for child_account in customer_ids_to_child_accounts[key]:
                dict_acc[child_account.id] = [
                    child_account.descriptive_name,
                    child_account.currency_code,
                    child_account.time_zone,
                    child_account.level,
                ]
        return customer_ids_to_child_accounts

    def all_child_acc(self, client):
        """retrieve all child account"""
        dict_acc = self.get_list_acc(client, self.main_manager_account)
        list_child_acc = []
        for key in dict_acc.keys():
            for child_account in dict_acc[key]:
                # if child_account.id not in list(dict_acc.keys()): #not get the manager accounts
                list_child_acc.append(
                    [child_account.id, child_account.descriptive_name]
                )
        return list_child_acc

    def save_ads_data_to_excel(self, start_date, end_date, dir="./"):
        """pull and save data to csv"""

        def _build_query(
            SELECT=list,
            FROM=str,
            WHERE=str,
            START_DATE=str,
            END_DATE=str,
            ORDER=str,
            DESC=True,
        ):
            query = "\n    SELECT\n"
            for metric in SELECT:
                query += "      " + metric + ",\n"
            query = query[:-2] + "\n    FROM " + FROM
            query += " WHERE " + WHERE
            query += " BETWEEN '" + START_DATE + "' AND '" + END_DATE + "'"
            query += "    ORDER BY " + ORDER
            if DESC == True:
                query += " DESC"
            else:
                query += " ASC"
            return query

        df_main = pd.DataFrame()
        list_child_acc = self.all_child_acc(self.googleads_client)

        query = _build_query(
            SELECT=GOOGLE_ADS_FIELDS,
            FROM=QUERY_TABLE,
            WHERE=FILTER_FIELD,
            START_DATE=start_date,
            END_DATE=end_date,
            ORDER=FILTER_FIELD,
        )
        for acc in list_child_acc:
            try:
                df = self.get_customer_data(str(acc[0]), query)
                df_main = df_main.append(df)
            except Exception as e:
                logging.error(f"Can not download data from {acc}. Detail {e}")

        for customer in self.get_all_customer_ids():
            try:
                yaml_file = self._change_customer_id_yaml(self.yaml_file, customer)
                self.googleads_client = GoogleAdsClient.load_from_storage(
                    yaml_file, version="v8"
                )
                df = self.get_customer_data(str(customer), query)
                df_main = df_main.append(df)
            except Exception as e:
                logging.error(f"Can not download data from {customer}. Detail {e}")
        filename = f"{dir}/{self.main_manager_account}_{start_date}-{end_date}.csv"
        df_main.to_csv(filename, index=False)

    def get_customer_data(self, customer_id, query):
        """get customer data given cutomer id and query"""
        ga_service = self.googleads_client.get_service("GoogleAdsService")
        # Issues a search request using streaming.
        search_request = self.googleads_client.get_type("SearchGoogleAdsStreamRequest")
        search_request.customer_id = customer_id
        search_request.query = query
        response = ga_service.search_stream(search_request)
        query_list = query.strip().split()
        metrics = query_list[1 : query_list.index("FROM")]
        all_data = []
        for batch in response:
            for row in batch.results:
                single_row = dict()
                # single_row['date']=row.segments.date
                for metric in metrics:
                    metric = metric.replace(",", "")
                    single_row[metric] = str(
                        getattr(
                            getattr(row, metric.split(".")[0]), metric.split(".")[1]
                        )
                    )
                all_data.append(single_row)

        df = pd.DataFrame(all_data)
        return df


# create a for loop for each customer and change the yaml file
