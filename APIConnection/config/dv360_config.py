# Path to a file to cache auth credentials, so they survive multiple runs
# of the application. This avoids prompting the user for authorization every
# time the access token expires, by remembering the refresh token.
CREDENTIAL_STORE_FILE = "cached_auth.dat"
CREDENTIAL_STORE_DIR = "credential_cached_storage/"
SERVICE_ACCOUNT_CREDS = "/home/quydx/Desktop/APIConnection/dv360-api-277821-3996c8539429.json"
# Path to log file
LOG_FILE = "dv360.log"
# Logging level
LOG_LEVEL = "debug"

REPORT_TITLE = "DV360 Automation API-generated report"
# Refer https://developers.google.com/bid-manager/v1/reports to configure your report template
# List of allowed filters and metrics can be found here: https://developers.google.com/bid-manager/v1.1/filters-metrics
REPORT_FORMAT = "csv"
REPORT_TYPE = "TYPE_GENERAL"
REPORT_METRICS = [
    "METRIC_CLICKS",
    # "METRIC_CM360_POST-CLICK_REVENUE",
    # "METRIC_CM360_POST-VIEW_REVENUE",
    "METRIC_IMPRESSIONS",
    # "METRIC_LAST_CLICKS",
    # "METRIC_LAST_IMPRESSIONS",
    # "METRIC_REVENUE_ADVERTISER",
    # "METRIC_RICH_MEDIA_VIDEO_COMPLETIONS",
    # "METRIC_TOTAL_CONVERSIONS",
    # "METRIC_TOTAL_MEDIA_COST_ADVERTISER",
]
REPORT_FILTER_GROUP = [
    "FILTER_DATE",
    "FILTER_BUDGET_SEGMENT_BUDGET",
    "FILTER_BUDGET_SEGMENT_DESCRIPTION",
    "FILTER_BUDGET_SEGMENT_END_DATE",
    "FILTER_BUDGET_SEGMENT_PACING_PERCENTAGE",
    "FILTER_BUDGET_SEGMENT_START_DATE",
    "FILTER_BUDGET_SEGMENT_TYPE",
    # "FILTER_ADVERTISER",
    # "FILTER_ADVERTISER_NAME",
    # "FILTER_ADVERTISER_INTEGRATION_STATUS",
    # "FILTER_MEDIA_PLAN_NAME",
    # "FILTER_MEDIA_PLAN",
    # "FILTER_INSERTION_ORDER",
    # "FILTER_INSERTION_ORDER_NAME",
    # "FILTER_INSERTION_ORDER_STATUS",
    # "FILTER_LINE_ITEM",
    # "FILTER_LINE_ITEM_NAME",
    # "FILTER_LINE_ITEM_STATUS",
    # "FILTER_CREATIVE",
    # "FILTER_CREATIVE_ID",
    # "FILTER_CREATIVE_STATUS",
    # "FILTER_CREATIVE_SOURCE",
    # "FILTER_ADVERTISER_CURRENCY",
    # "FILTER_FLOODLIGHT_ACTIVITY",
    # "FILTER_FLOODLIGHT_ACTIVITY_ID",
    # "FILTER_CITY",
    # "FILTER_CITY_NAME",
    # "FILTER_REGION_NAME",
    # "FILTER_REGION",
    # "FILTER_COUNTRY",
    # "FILTER_OS", # Operating System => Not support
    # "FILTER_DEVICE_TYPE",
    # "FILTER_TIME_OF_DAY",
]
REPORT_FILTER_TYPE = "FILTER_ADVERTISER"
