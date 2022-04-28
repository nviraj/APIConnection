# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 17:49:33 2021

@author: AndrewP
"""

import pandas as pd                        
from pytrends.request import TrendReq
from datetime import date, timedelta
from functools import partial
from time import sleep
from calendar import monthrange
from pytrends.exceptions import ResponseError


START_YEAR=2021
START_MON=9
STOP_YEAR=2021
STOP_MON=10
today = date.today()
today = today.strftime("%Y-%m-%d")
KEY_WORD='tesla'
pytrends = TrendReq()
CAT=0

us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
}

def get_last_date_of_month(year: int, month: int) -> date:
    """Given a year and a month returns an instance of the date class
    containing the last day of the corresponding month.
    """
    return date(year, month, monthrange(year, month)[1])


def convert_dates_to_timeframe(start: date, stop: date) -> str:
    """Given two dates, returns a stringified version of the interval between
    the two dates which is used to retrieve data for a specific time frame
    from Google Trends.
    """
    return f"{start.strftime('%Y-%m-%d')} {stop.strftime('%Y-%m-%d')}"


def _fetch_data(pytrends, build_payload, timeframe: str) -> pd.DataFrame:
    """Attempts to fecth data and retries in case of a ResponseError."""
    attempts, fetched = 0, False
    while not fetched:
        try:
            build_payload(timeframe=timeframe)
        except ResponseError as err:
            print(err)
            print(f'Trying again in {60 + 5 * attempts} seconds.')
            sleep(60 + 5 * attempts)
            attempts += 1
            if attempts > 3:
                print('Failed after 3 attemps, abort fetching.')
                break
        else:
            fetched = True
    return pytrends.interest_over_time()


def _fetch_data_region(pytrends, build_payload,resolution:str, timeframe: str) -> pd.DataFrame:
    """Attempts to fecth data and retries in case of a ResponseError."""
    attempts, fetched = 0, False
    while not fetched:
        try:
            build_payload(timeframe=timeframe)
        except ResponseError as err:
            print(err)
            print(f'Trying again in {60 + 5 * attempts} seconds.')
            sleep(60 + 5 * attempts)
            attempts += 1
            if attempts > 3:
                print('Failed after 3 attemps, abort fetching.')
                break
        else:
            fetched = True
    return pytrends.interest_by_region(resolution)


def get_daily_data(word: str,
                 start_year: int,
                 start_mon: int,
                 stop_year: int,
                 stop_mon: int,
                 geo: str = 'US',
                 verbose: bool = True,
                 wait_time: float = 5.0) -> pd.DataFrame:
    """Given a word, fetches daily search volume data from Google Trends and
    returns results in a pandas DataFrame.
    Details: Due to the way Google Trends scales and returns data, special
    care needs to be taken to make the daily data comparable over different
    months. To do that, we download daily data on a month by month basis,
    and also monthly data. The monthly data is downloaded in one go, so that
    the monthly values are comparable amongst themselves and can be used to
    scale the daily data. The daily data is scaled by multiplying the daily
    value by the monthly search volume divided by 100.
    For a more detailed explanation see http://bit.ly/trendsscaling
    Args:
        word (str): Word to fetch daily data for.
        start_year (int): the start year
        start_mon (int): start 1st day of the month
        stop_year (int): the end year
        stop_mon (int): end at the last day of the month
        geo (str): geolocation
        verbose (bool): If True, then prints the word and current time frame
            we are fecthing the data for.
    Returns:
        complete (pd.DataFrame): Contains 4 columns.
            The column named after the word argument contains the daily search
            volume already scaled and comparable through time.
            The column f'{word}_unscaled' is the original daily data fetched
            month by month, and it is not comparable across different months
            (but is comparable within a month).
            The column f'{word}_monthly' contains the original monthly data
            fetched at once. The values in this column have been backfilled
            so that there are no NaN present.
            The column 'scale' contains the scale used to obtain the scaled
            daily data.
    """

    # Set up start and stop dates
    start_date = date(start_year, start_mon, 1) 
    stop_date = get_last_date_of_month(stop_year, stop_mon)

    # Start pytrends for US region
    pytrends = TrendReq(hl='en-US', tz=360)
    # Initialize build_payload with the word we need data for
    build_payload = partial(pytrends.build_payload,
                            kw_list=[word], cat=0, geo=geo, gprop='')

    # Obtain monthly data for all months in years [start_year, stop_year]
    monthly = _fetch_data(pytrends, build_payload,
                         convert_dates_to_timeframe(start_date, stop_date))

    # Get daily data, month by month
    results = {}
    # if a timeout or too many requests error occur we need to adjust wait time
    current = start_date
    while current < stop_date:
        last_date_of_month = get_last_date_of_month(current.year, current.month)
        timeframe = convert_dates_to_timeframe(current, last_date_of_month)
        if verbose:
            print(f'{word}:{timeframe}')
        results[current] = _fetch_data(pytrends, build_payload, timeframe)
        current = last_date_of_month + timedelta(days=1)
        sleep(wait_time)  # don't go too fast or Google will send 429s

    daily = pd.concat(results.values()).drop(columns=['isPartial'])
    complete = daily.join(monthly, lsuffix='_unscaled', rsuffix='_monthly')

    # Scale daily data by monthly weights so the data is comparable
    complete[f'{word}_monthly'].ffill(inplace=True)  # fill NaN values
    complete['scale'] = complete[f'{word}_monthly'] / 100
    complete[word] = complete[f'{word}_unscaled'] * complete.scale

    return complete


def get_region_data(word: str,
                 start_year: int,
                 start_mon: int,
                 stop_year: int,
                 stop_mon: int,
                 geo: str = 'US',
                 resolution: str='CITY',
                 wait_time: float = 5.0) -> pd.DataFrame:

    # Set up start and stop dates
    start_date = date(start_year, start_mon, 1) 
    stop_date = get_last_date_of_month(stop_year, stop_mon)

    # Start pytrends for US region
    pytrends = TrendReq(hl='en-US', tz=360)
    # Initialize build_payload with the word we need data for
    build_payload = partial(pytrends.build_payload,
                            kw_list=[word], cat=0, geo=geo, gprop='')

    # Obtain monthly data for all months in years [start_year, stop_year]
    IBR = _fetch_data_region(pytrends, build_payload,resolution,
                         convert_dates_to_timeframe(start_date, stop_date))
    sleep(wait_time)  # don't go too fast or Google will send 429s
    return IBR
  
    

df_IOT=get_daily_data(word= KEY_WORD,
             start_year= START_YEAR,
             start_mon= START_MON,
             stop_year= STOP_YEAR,
             stop_mon= STOP_MON,
             geo= 'US',
             verbose = False,
             wait_time = 4.0)
df_IOT.columns=['US_unscale','US_monthly','isPartial','scale','US_value']
df_IOT=df_IOT[['US_unscale','US_monthly','scale','US_value']]
#related topic with the key word
df_RT=pytrends.related_topics()
#related query with the key word
df_RQ=pytrends.related_queries()
#interest by region
df_IBR=get_region_data(word= KEY_WORD,
         start_year= START_YEAR,
         start_mon= START_MON,
         stop_year= STOP_YEAR,
         stop_mon= STOP_MON,
         geo= 'US',
         resolution='REGION',
         wait_time = 4.0)
df_IBR=df_IBR[df_IBR.index.str.startswith('District of Columbia')]

for state in us_state_to_abbrev:
    data_IBR=get_region_data(word= KEY_WORD,
             start_year= START_YEAR,
             start_mon= START_MON,
             stop_year= STOP_YEAR,
             stop_mon= STOP_MON,
             geo= 'US-'+us_state_to_abbrev[state],
             resolution='CITY',
             wait_time = 4.0)
    df_IBR=pd.concat([df_IBR,data_IBR])
    #interest over time
    data_IOT=get_daily_data(word= KEY_WORD,
                 start_year= START_YEAR,
                 start_mon= START_MON,
                 stop_year= STOP_YEAR,
                 stop_mon= STOP_MON,
                 geo= 'US-'+us_state_to_abbrev[state],
                 verbose = False,
                 wait_time = 4.0)
    data_IOT.columns=[state+'_unscale',state+'_monthly','isPartial','scale',state+'_value']
    data_IOT=data_IOT[[state+'_unscale',state+'_monthly','scale',state+'_value']]
    df_IOT=pd.merge(df_IOT, data_IOT, left_index=True, right_index=True)





