import sys
import argparse
sys.path.append(".")


def run_fb(args):
    from APIConnection.facebook_connection import FBConnection
    from APIConnection.settings import FB_ACCESS_TOKEN

    conn = FBConnection(access_token=FB_ACCESS_TOKEN)
    conn.save_insight_ads_accounts_to_excel(
        args.start_date, args.end_date, path="./results"
    )


def run_ttd(args):
    from APIConnection.tradedesk import TTDConnection
    from APIConnection.settings import TTD_AUTH_TOKEN

    if args.username is None or args.password is None:
        conn = TTDConnection(auth_token=TTD_AUTH_TOKEN)
    else:
        conn = TTDConnection(username=args.username, password=args.password)

    conn.get_reports("tm90ejd", args.start_date, args.end_date, "./results/TTD")


def run_gcm(args):
    from APIConnection.google_campaign_manager import GoogleCampaignManager

    gcm = GoogleCampaignManager()
    gcm.get_all_report_files(args.start_date, args.end_date)


def dv360(args):
    from APIConnection.dv360 import DV360
    from APIConnection.logger import get_logger
    from APIConnection.config import dv360_config

    logger = get_logger(
        "dv360", file_name=dv360_config.LOG_FILE, log_level=dv360_config.LOG_LEVEL
    )
    dv360_object = DV360(
        cred=args.cred,
        date_range=args.date,
        output=args.output,
        frequency=args.frequency,
        report_window=args.report_window,
    )
    dbm_service_object, dv360_service_object = dv360_object.get_service(version="v1")
    if args.create:
        queryId = dv360_object.create_report(dbm_service_object, dv360_service_object)
        logger.info(
            f"Created report with queryID {queryId}. you should store it somewhere for later use"
        )
    elif args.get:
        dv360_object.get_full_report(dbm_service_object, args.get)
    else:
        queryId = dv360_object.create_report(dbm_service_object, dv360_service_object)
        dv360_object.get_full_report(dbm_service_object, queryId)


def run_googleads(args):
    from APIConnection.google_ads_api import GoogleAds

    google_ads = GoogleAds()
    google_ads.save_ads_data_to_excel(args.start_date, args.end_date)


def linkedin(args):
    from APIConnection.linkedin.ln_main import Linkedin

    linkedin_object = Linkedin(
        client_name=args.client_name,
        cred=args.cred,
        output=args.output,
        s_date=args.start,
        e_date=args.end,
        query_type=args.query_type,
    )
    linkedin_object.ln_main()


def twitter(args):
    from APIConnection.twitter import TwitterConnection

    twitter = TwitterConnection()
    twitter.save_insight_ads_accounts_to_excel(
        args.start_date, args.end_date, args.output
    )


def run_google_trends(args):
    from APIConnection.google_trends import GoogleTrends

    google_trends = GoogleTrends()
    google_trends.save_daily_data_date_range_to_csv(
        args.keyword, args.start_date, args.end_date
    )

def run_google_analyst(args):
    from APIConnection.google_analytics import GoogleAnalyst

    google_analyst = GoogleAnalyst()
    google_analyst.save_data_to_csv(args.viewid, args.start_date, args.end_date)

if __name__ == "__main__":
    main_parser = argparse.ArgumentParser()
    service_subparsers = main_parser.add_subparsers(help="Sub-command help")
    # Create the parser for the sub-command
    parser_dv360 = service_subparsers.add_parser(
        "dv360", help="DV360 Automation API-generated report tool"
    )
    parser_dv360.add_argument(
        "--date",
        "-d",
        type=str,
        default="LAST_7_DAYS",
        help="Date range of dv360 report data, refer: https://developers.google.com/bid-manager/v1.1/queries#metadata.dataRange",
    )
    parser_dv360.add_argument(
        "--cred", type=str, required=True, help="Path to OAuth credential json file"
    )
    parser_dv360.add_argument(
        "--output",
        "-o",
        type=str,
        default="output_reports/dv360",
        help="Output directory of report data",
    )
    parser_dv360.add_argument(
        "--create",
        "-c",
        action="store_true",
        help="Create new report on DV360 platform",
    )
    parser_dv360.add_argument(
        "--get", "-g", type=str, help="Get report on DV360 platform, enter queryID"
    )
    parser_dv360.add_argument(
        "--frequency",
        "-f",
        type=str,
        default="ONE_TIME",
        help="Frequency for report generation",
    )
    parser_dv360.add_argument(
        "--report_window",
        default=12,
        type=int,
        help="The age a report must be in hours at a maximum to be considered fresh.",
    )
    parser_dv360.set_defaults(func=dv360)

    # FB
    parser_fb = service_subparsers.add_parser(
        "fb", help="FB Automation API-generated report tool"
    )
    parser_fb.add_argument(
        "--start_date", "-s", type=str, help="Date range of ttd report data"
    )
    parser_fb.add_argument(
        "--end_date", "-e", type=str, help="Date range of ttd report data"
    )
    parser_fb.set_defaults(func=run_fb)

    # TTD
    parser_ttd = service_subparsers.add_parser(
        "ttd", help="TradeDesk Automation API-generated report tool"
    )
    parser_ttd.add_argument(
        "--start_date", "-s", type=str, help="Date range of ttd report data"
    )
    parser_ttd.add_argument(
        "--end_date", "-e", type=str, help="Date range of ttd report data"
    )
    parser_ttd.add_argument(
        "--username", "-u", type=str, help="username", required=False
    )
    parser_ttd.add_argument(
        "--password", "-p", type=str, help="password", required=False
    )
    parser_ttd.set_defaults(func=run_ttd)

    # Google campaign manager
    parser_gcm = service_subparsers.add_parser(
        "gcm", help="GCM API-generated report tool"
    )
    parser_gcm.add_argument(
        "--start_date", "-s", type=str, help="Date range of ttd report data"
    )
    parser_gcm.add_argument(
        "--end_date", "-e", type=str, help="Date range of ttd report data"
    )
    parser_gcm.set_defaults(func=run_gcm)

    parser_ga = service_subparsers.add_parser("ga", help="GA API-generated report tool")
    parser_ga.add_argument(
        "--start_date", "-s", type=str, help="Date range of ttd report data"
    )
    parser_ga.add_argument(
        "--end_date", "-e", type=str, help="Date range of ttd report data"
    )
    parser_ga.set_defaults(func=run_googleads)

    parser_gt = service_subparsers.add_parser(
        "gt", help="Google Trends-generated report tool"
    )
    parser_gt.add_argument("--keyword", "-k", type=str, help="Keyword")
    parser_gt.add_argument(
        "--start_date", "-s", type=str, help="Date range of google trends data"
    )
    parser_gt.add_argument(
        "--end_date", "-e", type=str, help="Date range of google trends data"
    )

    parser_gt.set_defaults(func=run_google_trends)

    # Linkedin
    parser_linkedin = service_subparsers.add_parser(
        "linkedin", help="Linkedin Automation API-generated report tool"
    )
    parser_linkedin.add_argument(
        "--client_name",
        "-c",
        type=str,
        default="client_name",
        help="The name of client in cred file",
    )
    parser_linkedin.add_argument(
        "--cred", type=str, required=True, help="Path to OAuth credential json file"
    )
    parser_linkedin.add_argument(
        "--output",
        "-o",
        type=str,
        default="output_reports/linkedin",
        help="Output directory of report data",
    )
    parser_linkedin.add_argument(
        "--start",
        "-s",
        type=str,
        required=True,
        help="The start date (YYYY-MM-DD) to get the report",
    )
    parser_linkedin.add_argument(
        "--end",
        "-e",
        type=str,
        required=True,
        help="The end date (YYYY-MM-DD) to get the report",
    )
    parser_linkedin.add_argument(
        "--query_type",
        "-q",
        type=str,
        required=True,
        help="The query type, it can be week/weekly/month/monthly",
    )
    parser_linkedin.set_defaults(func=linkedin)

    # Twitter
    parser_twitter = service_subparsers.add_parser(
        "twitter", help="Twitter Automation API-generated report tool"
    )

    parser_twitter.add_argument(
        "--output",
        "-o",
        type=str,
        default="./output_reports/twitter",
        help="Output directory of report data",
    )
    parser_twitter.add_argument(
        "--start_date",
        "-s",
        type=str,
        required=True,
        help="The start date (YYYY-MM-DD) to get the report",
    )
    parser_twitter.add_argument(
        "--end_date",
        "-e",
        type=str,
        required=True,
        help="The end date (YYYY-MM-DD) to get the report",
    )
    parser_twitter.set_defaults(func=twitter)


    # Google Analyst
    parser_google_analyst = service_subparsers.add_parser(
        "google_analyst", help="Google Analyst Automation API-generated report tool"
    )

    parser_google_analyst.add_argument(
        "--output",
        "-o",
        type=str,
        default="./output_reports/google_analyst",
        help="Output directory of report data",
    )
    parser_google_analyst.add_argument(
        "--view_id",
        "-vid",
        type=str,
        required=True,
        help="The viewID to get the report",
    )
    parser_google_analyst.add_argument(
        "--start_date",
        "-s",
        type=str,
        required=True,
        help="The start date (YYYY-MM-DD) to get the report",
    )
    parser_google_analyst.add_argument(
        "--end_date",
        "-e",
        type=str,
        required=True,
        help="The end date (YYYY-MM-DD) to get the report",
    )
    parser_google_analyst.set_defaults(func=run_google_analyst)

    args = main_parser.parse_args()
    args.func(args)

# Example: python main.py dv360 -d PREVIOUS_DAY -c cred.json
# Example: python3 main.py [fb|ttd|gcm] -s 2021-10-01 -e 2021-10-05
