import datetime
from time import sleep
from datetime import date, timedelta
from functools import partial
import logging

import pandas as pd                        
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError

from .utils import get_last_date_of_month, convert_dates_to_timeframe

logging.basicConfig(filename="google_trends.log", level=logging.DEBUG)


class GoogleTrends:
    """Wrapper class for fetching/parsing Google Trends endpoints"""
    
    def _fetch_data(self, pytrends, build_payload, timeframe: str) -> pd.DataFrame:
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


    def _fetch_data_region(self, pytrends, build_payload,resolution:str, timeframe: str) -> pd.DataFrame:
        """Attempts to fecth data and retries in case of a ResponseError."""
        attempts, fetched = 0, False
        while not fetched:
            try:
                build_payload(timeframe=timeframe)
            except ResponseError as err:
                logging.warning(err)
                logging.info(f'Trying again in {60 + 5 * attempts} seconds.')
                sleep(60 + 5 * attempts)
                attempts += 1
                if attempts > 3:
                    logging.warning('Failed after 3 attemps, abort fetching.')
                    break
            else:
                fetched = True
        return pytrends.interest_by_region(resolution)

    def save_daily_data_date_range_to_csv(self, 
                    word: str,
                    start_date: str,
                    end_date: str,
                    geo: str = 'US',
                    verbose: bool = True,
                    wait_time: float = 5.0,
                    filename:str = './google_trends.csv'):
        """Save the daily data to csv"""
        
        start_dateime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        try:
            daily_data = self.get_daily_data(word, start_dateime.year, start_dateime.month, end_datetime.year, end_datetime.month, geo, verbose, wait_time)
            df = daily_data.loc[start_date:end_date]
            df.to_csv(filename)
        except Exception as e:
            logging.error(e)
        
    def get_daily_data(self,
                    word: str,
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
        monthly = self._fetch_data(pytrends, build_payload,
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
            results[current] = self._fetch_data(pytrends, build_payload, timeframe)
            current = last_date_of_month + timedelta(days=1)
            sleep(wait_time)  # don't go too fast or Google will send 429s

        daily = pd.concat(results.values()).drop(columns=['isPartial'])
        complete = daily.join(monthly, lsuffix='_unscaled', rsuffix='_monthly')

        # Scale daily data by monthly weights so the data is comparable
        complete[f'{word}_monthly'].ffill(inplace=True)  # fill NaN values
        complete['scale'] = complete[f'{word}_monthly'] / 100
        complete[word] = complete[f'{word}_unscaled'] * complete.scale

        return complete
    
    def get_region_data(self,
                 word: str,
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
        IBR = self._fetch_data_region(pytrends, build_payload,resolution,
                            convert_dates_to_timeframe(start_date, stop_date))
        sleep(wait_time)  # don't go too fast or Google will send 429s
        return IBR