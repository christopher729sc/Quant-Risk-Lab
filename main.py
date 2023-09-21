import argparse
import configparser
import logging
import lib.database as db
import lib.position as pos

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


def initialize_database(config: dict, db_name: str, yield_curve_raw_data: str, yield_curve_table_name: str) -> None:
    """
    Initialize the SQLite database with data from a downloaded yield curve data based on the provided configuration.
    The source: https://home.treasury.gov/

    :param yield_curve_table_name: Name of the yield curvetable in the database
    :param yield_curve_raw_data: Path to the CSV file containing the data
    :param db_name:Name of the SQLite database file
    :param config: A dictionary containing configuration details for database initialization.
    :return: None
    """

    # Initialize the database and write data to it
    initial_db = db.DatabaseInitialSetup(db_name, yield_curve_raw_data, yield_curve_table_name)
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
    logging.info("As of Date: %s", config['RUN_SETUP']['as_of_date'])
    logging.info("Current version: %s", config['VERSION_INFO']['version_id'])

    # Extract necessary configurations from the config dictionary
    db_name = config['DATABASE']['database_name']
    yield_curve_raw_data = config['MARKET_DATA']['yield_curve_raw_data']
    yield_curve_table_name = config['DATABASE']['yield_curve_table_name']
    yield_curve_history_start_end_dates = config['RUN_SETUP']['yield_curve_history_start_end_dates'].split("|")

    # If database initialization is needed
    if args.if_initialize_db == 'Y':
        logging.info('Initiate yield curve table setup given fist time run')
        initialize_database(config, db_name, yield_curve_raw_data, yield_curve_table_name)
    else:
        pass

    # Fetch yield curve data based on the need
    try:
        yield_curve_fetcher = db.YieldCurveFetcher(db_name, yield_curve_table_name)
        df = yield_curve_fetcher.fetch_data_for_dates(yield_curve_history_start_end_dates[0],
                                                      yield_curve_history_start_end_dates[1])
        print(df)
        yield_curve_fetcher.close()

    except (NameError, AttributeError) as e:
        logging.error(f'{e}: The database failed to initialize.'
                      'Ensure that the database file is present and accessible')


if __name__ == "__main__":
    main()
