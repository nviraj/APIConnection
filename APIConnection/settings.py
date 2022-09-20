import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

# Please provide facebook access token here
FB_ACCESS_TOKEN = ""
# For trade desk, there are two ways to authorize API calls. You can
# use either simple auth or access token. Please provide the access token here; otherwise
# you need to run the program with simple auth
TTD_AUTH_TOKEN = ""
GG_OAUTH2_CRED = "/home/quydx/datapal/datapal-compose/submodules/APIConnection/datapal-oauth2.json"
AD_INSIGHT_FIELD = f"{dir_path}/config/Facebook_fields_ads_insights.csv"


# Path to client secrets
GOOGLE_CLIENT_SECRET = ""

GOOGLE_COMPAIGN_MANAGER_REPORT = [
    {"profile_id": 5800697, "report_id": 871396013},
    {"profile_id": 5801376, "report_id": 872430830},
    {"profile_id": 5824646, "report_id": 872801372},
    {"profile_id": 5824319, "report_id": 872801630},
    {"profile_id": 5824916, "report_id": 872801657},
    {"profile_id": 6117321, "report_id": 872803054},
]

# Path to google ads yaml
GOOGLE_ADS_YAML = ""

GOOGLE_ADS_FIELDS = [
    "customer.descriptive_name",
    "campaign.id",
    "campaign.name",
    "metrics.impressions",
    "metrics.clicks",
    "metrics.cost_micros",
    "segments.date",
    "customer.currency_code",
]

TWITTER_ACCOUNTS = ["kgs38", "61lmup", "8wmsmr", "pdvo6g", "18ce53wags1", "18ce53yyrf7"]
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_TOKEN = ''
TWITTER_ACCESS_TOKEN_SECRET = ''

GOOGLE_ANALYST_CRED = "path_to_the_credential_file"
