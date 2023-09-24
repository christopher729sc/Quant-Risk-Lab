import datetime as dt
import logging
import numpy as np
import pandas as pd

# Customized Utilities
from lib.utils import *
from lib.pricer import *

logging.basicConfig(format='%(message)s', level=logging.INFO)

"""
NOTE:
I have hard time finding a free public API available that provides comprehensive data for fixed income instruments.
Given these constraints, I am replying on manually downloaded data sources.

Current source is FINRA: https://www.finra.org/finra-data/fixed-income
Treasury bond: https://www.treasurydirect.gov/instit/annceresult/press/preanre/2023/A_20230802_1.pdf
The FINRA API document is as: https://developer.finra.org/docs#getting_started

More API services include
Eikon, Bloomberg, FRED,  FINRA
"""


class InstrumentAcquisitionManager:
    """
    A manager class to handle the acquisition of financial instruments.

    Attributes:
        instrument_acquisition_approach (str): The approach/method for acquiring instruments.
        instruments (pd.DataFrame): A dataframe storing the acquired instruments' details.

    Methods:
        get_instruments(instrument_data_path: str) -> pd.DataFrame:
            Acquires financial instruments based on the specified acquisition approach and the given data path.
    """

    def __init__(self, instrument_acquisition_approach='Download'):
        """
        Initializes the InstrumentAcquisitionManager with the specified approach.
        """
        self.instrument_acquisition_approach = instrument_acquisition_approach
        self.instruments = pd.DataFrame()

    def get_instruments(self, instrument_data_path: str) -> pd.DataFrame:
        """
        Acquires financial instruments based on the acquisition approach and provided data path.

        :param instrument_data_path: The path to the CSV file or API endpoint to acquire instruments.
        :return: pd.DataFrame: A dataframe containing details of the acquired instruments.
        """

        if self.instrument_acquisition_approach == 'Download':
            self.instruments = pd.read_csv(instrument_data_path).drop(columns=['source_url'])
            return self.instruments
        else:
            logging.warning("API Functionality is under construction")
            pass  # TODO Implement API functionality once the certificate or license is available


class PortfolioManager:

    def __init__(self, config, instruments):

        self.portfolio_yields = None
        self.portfolio_pnl = None
        self.config = config
        self.as_of_date = config['RUN_SETUP']['as_of_date']
        self.number_of_instruments = len(instruments['cusip'].unique())
        self.portfolio = instruments.copy()
        self.weightage_approach = config['PORTFOLIO']['weightage_approach']
        self.total_fund = float(config['PORTFOLIO']['total_fund'])

    def create_portfolio(self, ):
        if self.weightage_approach == 'equal_weight':
            weights = np.divide(np.ones(self.number_of_instruments), self.number_of_instruments)
        elif self.weightage_approach == 'random_weight':
            rands = np.random.rand(5)
            weights = np.divide(rands, rands.sum())

        self.portfolio['as_of_date'] = self.as_of_date
        self.portfolio['years_to_maturity'] = self.portfolio.apply(lambda x:
                                                                   calculate_years_to_maturity(self.as_of_date,
                                                                                               x['maturity_date']),
                                                                   axis=1)
        self.portfolio['weight'] = weights
        self.portfolio['market_value'] = weights * self.total_fund
        self.portfolio['quantity'] = self.portfolio['market_value'] / self.portfolio['last_price']

    def calculate_daily_yield_change(self, config: object, yield_curve_fetcher: object):

        inst_yield_curve_mapping = pre_process_mapping(config['MODEL']['instrument_yield_curve_mapping'].split('|'))
        start_date = config['PORTFOLIO']['daily_yield_change_start_date']

        # logging.info("Daily yield change from %s to %s", start_date, self.as_of_date)

        # Fetch yield curve info for the financial instrument
        _portfolios = []
        for cusip in self.portfolio['cusip']:

            instrument_dict = inst_yield_curve_mapping[cusip]
            try:
                yield_curve_name = instrument_dict['yield_curve_name']
                yield_curve = yield_curve_fetcher.fetch_data_for_dates(yield_curve_name, start_date, self.as_of_date)

                if yield_curve_name == 'US Treasury':
                    yield_curve = yield_curve.loc[yield_curve['tenor'] == instrument_dict['tenor']]

            except (TypeError, KeyError) as e:
                logging.warning(f"{e} Not able to locate the yield curve associated with the financial instrument")

            # logging.info('Fetching yield data for %s. The yield curve used is %s',
            #              cusip, yield_curve_name)

            yield_curve['cusip'] = cusip
            yield_curve = yield_curve.reset_index().merge(self.portfolio[['cusip',
                                                                          'issuer',
                                                                          'face_value',
                                                                          'coupon_rate',
                                                                          'coupon_frequency',
                                                                          'maturity_date',
                                                                          'quantity']],
                                                          left_on='cusip',
                                                          right_on='cusip',
                                                          how='left')

            yield_curve['years_to_maturity'] = yield_curve.apply(lambda x:
                                                                 calculate_years_to_maturity(x['date'],
                                                                                             x['maturity_date']),
                                                                 axis=1)

            # Start calculating bond price and derive market value
            yield_curve['calculated_price'] = yield_curve.apply(lambda x: bond_price_ytm(x), axis=1)
            yield_curve['market_value'] = yield_curve['calculated_price'] * yield_curve['quantity']
            yc_to_append = yield_curve[['date',
                                        'quantity',
                                        'market_value']].rename(columns={'quantity': '%s_quantity' % cusip,
                                                                         'market_value': '%s_market_value' % cusip})
            _portfolios.append(yc_to_append.set_index('date'))

        # Start to calculate portfolio value and return
        portfolio_yields = pd.concat(_portfolios, axis=1).dropna()
        portfolio_yields.sort_index(inplace=True)

        market_value_columns = [col for col in portfolio_yields.columns if col.endswith('_value')]

        # Compute the sum across these columns and store in 'portfolio value'
        portfolio_yields['portfolio_value'] = portfolio_yields[market_value_columns].sum(axis=1)
        portfolio_yields['daily_yield'] = portfolio_yields['portfolio_value'].pct_change()

        # Calculate pnl
        portfolio_pnl = portfolio_yields[[col for col in portfolio_yields.columns if col.endswith('_value')]].diff()
        portfolio_pnl.columns = [col.replace('_market_value','_daily_pnl').replace('_value','_daily_pnl')
                                 for col in portfolio_pnl.columns]
        print(portfolio_pnl.columns)

        # Assign it back to the portfolio
        self.portfolio_yields = portfolio_yields.sort_index(ascending=False)
        self.portfolio_pnl = portfolio_pnl.sort_index(ascending=False)

        return portfolio_yields.sort_index(ascending=False)

    def generate_portfolio_yield_report(self, data) -> str:
        """
        Generate a summary report of investment based on the provided file.

        :param data: portfolio yield data.
        :return: A formatted string containing the summary of the investment report.
        """
        data = data.copy().reset_index()

        # Create monthly data
        monthly_data = data[pd.to_datetime(data['date']).dt.day == 20].sort_values('date')
        monthly_data['monthly_yield'] = monthly_data['portfolio_value'].pct_change()
        monthly_data.sort_values('date', ascending=False)

        # Print important yield
        highest_yield = monthly_data['monthly_yield'].max()
        highest_yield_date = monthly_data[monthly_data['monthly_yield'] == highest_yield]['date'].iloc[0]
        lowest_yield = monthly_data['monthly_yield'].min()
        lowest_yield_date = monthly_data[monthly_data['monthly_yield'] == lowest_yield]['date'].iloc[0]
        end_portfolio_value = data['portfolio_value'].iloc[0]
        start_portfolio_value = data['portfolio_value'].iloc[-1]
        portfolio_appreciation = ((end_portfolio_value - start_portfolio_value) / start_portfolio_value) * 100

        # Create the formatted report
        report = f"""
        Portfolio Yield Summary Report:
        ------------------------
        Date Range: {data['date'].iloc[-1]} to {self.as_of_date}
        Highest Monthly Yield: {highest_yield * 100:.4f}% on {highest_yield_date}
        Lowest Monthly Yield: {lowest_yield * 100:.4f}% on {lowest_yield_date}
        Total Portfolio Value at the Start: ${start_portfolio_value:,.2f}
        Total Portfolio Value at the End: ${end_portfolio_value:,.2f}
        Portfolio Appreciation/Depreciation: {portfolio_appreciation:.2f}%
        ------------------------
        """
        logging.info('Summary report of portfolio yield %s \n',
                     report)

        return report
