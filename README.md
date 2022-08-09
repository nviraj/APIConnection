# APIConnection
## 1. Installation
To install dependencies, simply run
```
pip install -r requirments.txt
```
## 2. Run
## 2.1. Run dv360 module
### 2.1.1. Generate credentials
- To run dv360 module. Firstly, you should do some steps to set up your DV360 account manually. You can refer the document in the following url: https://developers.google.com/display-video/api/guides/getting-started/overview.
- After above step, you'll be presented with an OAuth 2.0 client ID and client secret, which you can download in JSON format and save for later use.
### 2.1.2. Adjust DV360 report template configuration file (Optional)
- Path to DV360 report template configuration file: `APIConnection/config/dv360_config.py`.
- Read the guide from comment section of this file and complete your configuration file (optional - you can leave it as default).
### 2.1.3. Run module
- You can get the usage of this module by running following command.
```
python main.py dv360 -h
```
```
usage: main.py dv360 [-h] [--date DATE] --cred CRED [--output OUTPUT] [--create] [--get GET] [--frequency FREQUENCY] [--report_window REPORT_WINDOW]

optional arguments:
  -h, --help            show this help message and exit
  --date DATE, -d DATE  Date range of dv360 report data, refer: https://developers.google.com/bid-manager/v1.1/queries#metadata.dataRange
  --cred CRED           Path to OAuth credential json file
  --output OUTPUT, -o OUTPUT
                        Output directory of report data
  --create, -c          Create new report on DV360 platform
  --get GET, -g GET     Get report on DV360 platform, enter queryID
  --frequency FREQUENCY, -f FREQUENCY
                        Frequency for report generation
  --report_window REPORT_WINDOW
                        The age a report must be in hours at a maximum to be considered fresh.

```
- Example:
```
python main.py dv360 -d PREVIOUS_DAY --cred cred.json -o output_reports/dv360
```

### 2.1.4. Best practice for dv360 module
- Create report firstly with `-c` option. You can create the report one time and get the report multiple times (Note: If you choose report frequency is daily, then you can get report daily.)
- Get the report with `-g` option.

## 2.2. Run fb/ttd/google cm/google ads modules

```
python main.py [fb|ttd|gcm|ga] -s 2021-10-01 -e 2021-10-05
```
## 2.3. Run google_ads_api module
### 2.3.1. Generate credentials
You'll need to supply the following information in the config file of your client library.
•	Developer token
•	Client customer ID
•	OAuth2 client ID and client secret
•	OAuth2 access and refresh tokens
This information is stored in the file “yaml” which will be read by google api “load_from_storage” function
More details at: 
https://developers.google.com/google-ads/api/docs/first-call/overview

### 2.3.2. Google Ads Query Language
The Google Ads Query Language is intergrated into the googleads api. The Google Ads Query Language can query the Google Ads API for Resources and their related attributes, segments, and metrics using
https://developers.google.com/google-ads/api/docs/query/overview

instead of using build-in "_build_query" function in google_ads_api, users can write their own queries follow Google Ads Query Language.

### 2.3.3. Keywords Performance Report
All attributes, segments, and metrics can be found at:
https://developers.google.com/adwords/api/docs/appendix/reports/keywords-performance-report

## 2.4. Run google_trends module
```
python main.py gt -k tesla -s 2021-10-01 -e 2021-10-05
```

## 2.5. Run linkedin module
### 2.5.1. Generate credentials
- Refer the setup in the following blog: https://www.jeevangupta.com/linkedin-api-setup-guide-2020/
### 2.5.2. Adjust Linkedin report template configuration file (Optional)
- Path to Linkedin report template configuration file: `APIConnection/config/linkedin_config.py`.
- Read the guide from comment section of this file and complete your configuration file (optional - you can leave it as default).
### 2.5.3. Run module
- You can get the usage of this module by running following command.
```
python main.py linkedin -h
```
```
usage: main.py linkedin [-h] [--client_name CLIENT_NAME] --cred CRED [--output OUTPUT] --start START --end END --query_type QUERY_TYPE

optional arguments:
  -h, --help            show this help message and exit
  --client_name CLIENT_NAME, -c CLIENT_NAME
                        The name of client in cred file
  --cred CRED           Path to OAuth credential json file
  --output OUTPUT, -o OUTPUT
                        Output directory of report data
  --start START, -s START
                        The start date (YYYY-MM-DD) to get the report
  --end END, -e END     The end date (YYYY-MM-DD) to get the report
  --query_type QUERY_TYPE, -q QUERY_TYPE
                        The query type, it can be week/weekly/month/monthly

```
- Example:
```
python3 main.py linkedin -c client_name --cred cred.json -s 2021-10-01 -e 2021-11-19 -q week
```

### 2.5.4. Cred example format

```
{
    "client_name":
    {
        "id":1,
        "access_token":"Replace it with LinkedIn access token",
        "client_id":"Replace it with LinkedIn app ID",
        "client_secret":"Replace it with LinkedIn app secret",
    }
}
```
