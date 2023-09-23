import argparse
import configparser
import logging

# Loading personal lib and utils
import lib.database as db
import lib.portfolio as pf
import lib.utils as ut

# Set up logging config
logging.basicConfig(format='%(message)s', level=logging.INFO)


def get_argument():
    """
    Parse command-line arguments.
    :return: argument object
    """
    parser = argparse.ArgumentParser(description='Quantitative Risk Lab for Portfolio Management')
    parser.add_argument("-c", '--config_path', type=str, default='./config/config.ini')
    parser.add_argument("-i", '--if_initialize_db', type=str, default='Y')
    parser.add_argument("-p", "--run_purpose",
                        type=str,
                        choices=["all", "risk_analytics", "data_acquisition_storage"],
                        default="data_acquisition_storage",
                        help="Purpose of the run")
    return parser.parse_args()


def read_config(config_path):
    """
    Read and parse the configuration file.
    :param config_path: Path to the configuration file.
    :return: ConfigParser object
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_path)
    except FileNotFoundError:
        logging.error(f"Config file not found at {config_path}")
        raise
    return config


def initialize_database(config,
                        db_name: str,
                        yield_curve_raw_data: str,
                        yield_curve_table_name: str) -> None:
    """
    Initialize the SQLite database with data from a downloaded yield curve data based on the provided configuration.
    The source: https://home.treasury.gov/

    :param yield_curve_table_name: Name of the yield curve table in the database
    :param yield_curve_raw_data: Path to the CSV file containing the data
    :param db_name:Name of the SQLite database file
    :param config: A dictionary containing configuration details for database initialization.
    :return: None
    """

    # Initialize the database and write data to it
    initial_db = db.SQLiteInitialSetup(db_name, yield_curve_raw_data, yield_curve_table_name)
    initial_db.write_data_to_db()

    # Close the database connection
    initial_db.close()


def main():
    """
    Main function of the Quant-Risk-Lab.
    :return: None
    """

    args = get_argument()
    config = read_config(args.config_path)

    # Printing version info
    as_of_date = config['RUN_SETUP']['as_of_date']
    logging.info("As of Date: %s", as_of_date)
    logging.info("Current version: %s", config['VERSION_INFO']['version_id'])

    ####################################################################################################################
    # The code below is the solution to provide solution to
    # 1. Data Acquisition and Storage:
    # 1.1 Select 3-5 fixed income instruments of your choosing that are accessible via a public API.
    #     (No need to get overly complicated here. Use data that is readily available.)
    # 1.2 Retrieve daily yield data for the past 2 years for your selected instruments
    #     and save it to a SQL Express database.
    # 1.3 Create a stored procedure in SQL that, when called,
    #     retrieves this yield data for the chosen instruments over a given date range.
    ####################################################################################################################
    # Solution to Question 1.1:
    instrument_acquisition_approach = config['PORTFOLIO']['instrument_acquisition_approach']
    instrument_data_path = config['PORTFOLIO']['instrument_data_path'].replace('YYYYMMDD', as_of_date.replace('-', ''))

    logging.info("\n Solution to Question 1.1.")
    logging.info("Data acquisition solution: %s",
                 instrument_acquisition_approach)
    logging.info("Data Location %s",
                 instrument_data_path)

    instruments = pf.InstrumentAcquisitionManager(instrument_acquisition_approach).get_instruments(instrument_data_path)
    logging.info("Sample Instruments: \n %s",
                 instruments)

    # Solution to question 1.2:
    logging.info("\n Solution to Question 1.2.")
    # Extract necessary configurations from the config dictionary for database management topic
    db_name = config['DATABASE']['database_name']
    yield_curve_raw_data = config['MARKET_DATA']['yield_curve_raw_data']
    yield_curve_table_name = config['DATABASE']['yield_curve_table_name']

    # If database initialization is needed
    if args.if_initialize_db == 'Y':
        logging.info('Initiate yield curve table setup given fist time run, \n'
                     'SQLite Database location is %s, \n'
                     'Yield data are stored in table %s',
                     db_name, yield_curve_table_name)
        initialize_database(config, db_name, yield_curve_raw_data, yield_curve_table_name)
    else:
        pass

    # Solution to question 1.3:
    logging.info("\n Solution to Question 1.3.")
    # Note: I am not able to run stored procedure for testing purpose. SQL Express installation is not successful
    #       Will switch to SQL Express and build stored procedure if the local config is successful

    if args.run_purpose in ["data_acquisition_storage"]:

        logging.info("Current Run Purpose is for: %s",
                     args.run_purpose)

        # Get start date and end date from yield curve database
        yield_curve_instrument = config['YIELD_FETCHER']['yield_curve_instrument']
        yield_curve_history_start_end_dates = config['YIELD_FETCHER']['yield_curve_history_start_end_dates'].split("|")
        yield_curve_output = config['MARKET_DATA']['yield_curve_output']

        # Fetch yield curve data based on the need
        try:
            yield_curve_fetcher = db.SQLiteYieldCurveFetcher(db_name, yield_curve_table_name)
            df = yield_curve_fetcher.fetch_data_for_dates(yield_curve_instrument,
                                                          yield_curve_history_start_end_dates[0],
                                                          yield_curve_history_start_end_dates[1])
            logging.info("Yield data from %s are retrieved for %s \n %s",
                         yield_curve_history_start_end_dates, yield_curve_instrument, df)

            df.to_csv(yield_curve_output)
            logging.info("Retrieved yield data is saved under %s",
                         yield_curve_output)
            yield_curve_fetcher.close()

        except (NameError, AttributeError) as e:
            logging.error(f'{e}: The database failed to initialize.'
                          'Ensure that the database file is present and accessible')

    # Enhancement 1 TODO Add insert functionality to add updated yield curve to database (SQLite)

    ####################################################################################################################
    # The code below is the solution to provide solution to
    # 2. Portfolio Simulation:
    # 2.1 Create a portfolio of the selected fixed income instruments with an arbitrary weightage.
    # 2.2 Calculate the daily yield changes (delta yield) for this portfolio.
    ####################################################################################################################
    # Enhancement before starting Q2 - Perform interpolation on yield curve for as of date
    try:
        yield_curve_fetcher = db.SQLiteYieldCurveFetcher(db_name, yield_curve_table_name)
        df_yc = yield_curve_fetcher.fetch_data_for_dates('US Treasury', as_of_date, as_of_date)
        yield_curve_fetcher.close()

    except (NameError, AttributeError) as e:
        logging.error(f'{e}: Fail to fetch yield data for %s', as_of_date)

    df_interpolated = ut.interpolate_yield_curve(df_yc['tenor'], df_yc['yield_to_maturity'])

    # Solution to 2.1 Create a portfolio of the selected fixed income instruments with an arbitrary weightage.
    logging.info("\n Solution to Question 2.1.")
    weightage_approach = config['PORTFOLIO']['weightage_approach']
    total_fund = float(config['PORTFOLIO']['total_fund'])
    portfolio_manager = pf.PortfolioManager(weightage_approach, total_fund, instruments)
    portfolio_manager.create_portfolio()
    logging.info("Portfolio Snapshot with total initial fund of %s: \n %s",
                 total_fund,
                 portfolio_manager.portfolio[['symbol','cusip','weight','market_value']])

    # Solution to 2.2 Calculate the daily yield changes

if __name__ == "__main__":
    main()
