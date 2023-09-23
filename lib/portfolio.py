import logging
import numpy as np
import pandas as pd

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

    def __init__(self, weightage_approach, total_fund, instruments):

        self.number_of_instruments = len(instruments['cusip'].unique())
        self.portfolio = instruments.copy()
        self.weightage_approach = weightage_approach
        self.total_fund = total_fund

    def create_portfolio(self,):
        if self.weightage_approach == 'equal_weight':
            weights = np.divide(np.ones(self.number_of_instruments), self.number_of_instruments)
        elif self.weightage_approach == 'random_weight':
            rands = np.random.rand(5)
            weights = np.divide(rands, rands.sum())

        self.portfolio['weight'] = weights
        self.portfolio['market_value'] = weights * self.total_fund





