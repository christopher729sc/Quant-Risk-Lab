import argparse
import configparser
import logging
import sys

# Loading personal lib and utils
import lib.database as db
import lib.portfolio as pf
import lib.utils as ut
import lib.risk_engine as reng
import lib.scenario as sm
from lib.pricer import *

# Set up logging config
logging.basicConfig(format='%(message)s', level=logging.INFO)


def get_argument():
    """
    Parse command-line arguments.
    :return: argument object
    """
    parser = argparse.ArgumentParser(description='Quantitative Risk Lab for Portfolio Management')
    parser.add_argument("-c", '--config_path', type=int, default=1)
    parser.add_argument("-i", '--if_initialize_db', type=str, default='Y')
    parser.add_argument("-p", "--run_purpose",
                        type=str,
                        choices=["all", "risk_analytics", "data_acquisition_storage"],
                        default="all",
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


def initialize_database(db_name: str,
                        yield_curve_raw_data: str,
                        yield_curve_table_name: str) -> None:
    """
    Initialize the SQLite database with data from a downloaded yield curve data based on the provided configuration.
    The source: https://home.treasury.gov/

    :param yield_curve_table_name: Name of the yield curve table in the database
    :param yield_curve_raw_data: Path to the CSV file containing the data
    :param db_name:Name of the SQLite database file
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
    config_id = 'config%s' % args.config_path
    config = read_config('./config/config%s.ini' % args.config_path)

    # Printing version info
    as_of_date = config['RUN_SETUP']['as_of_date']
    logging.info("As of Date: %s", as_of_date)
    logging.info("Running configuration based on config file: %s", args.config_path)
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
    logging.info("\n Solution to Question 1.1. \nData acquisition solution: %s \nData Location %s",
                 instrument_acquisition_approach, instrument_data_path)

    instruments = pf.InstrumentAcquisitionManager(instrument_acquisition_approach).get_instruments(instrument_data_path)
    logging.info("Sample Instruments: \n %s", instruments)

    # Solution to question 1.2:
    logging.info("\n Solution to Question 1.2.")
    # Extract necessary configurations from the config dictionary for database management topic
    db_name = config['DATABASE']['database_name']
    db_approach = config['DATABASE']['database_approach']
    yield_curve_raw_data = config['MARKET_DATA']['yield_curve_raw_data']
    yield_curve_table_name = config['DATABASE']['yield_curve_table_name']

    # If the application is run first, need to initialize the database using SQLite
    if args.if_initialize_db == 'Y':
        logging.info('Initiate yield curve table setup given fist time run, \n'
                     'Database Solution is %s, \n'
                     'SQLite Database location is %s, \n'
                     'Yield data are stored in table name: %s',
                     db_approach, db_name, yield_curve_table_name)
        initialize_database(db_name, yield_curve_raw_data, yield_curve_table_name)
    else:
        pass

    # Solution to question 1.3:
    logging.info("\n Solution to Question 1.3.")
    # Note: I am not able to run stored procedure for testing purpose. SQL Express installation is not successful
    #       Will switch to SQL Express and build stored procedure if the local config is successful

    if args.run_purpose in ["all", "data_acquisition_storage"]:

        logging.info("Current Run Purpose is for: %s", args.run_purpose)

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

        if args.run_purpose == "data_acquisition_storage":
            sys.exit()
        else:
            pass

    # Enhancement 1 TODO Add insert functionality to add updated yield curve to database (SQLite)

    ####################################################################################################################
    # The code below is the solution to provide solution to
    # 2. Portfolio Simulation:
    # 2.1 Create a portfolio of the selected fixed income instruments with an arbitrary weightage.
    # 2.2 Calculate the daily yield changes (delta yield) for this portfolio.
    ####################################################################################################################

    # Solution to 2.1 Create a portfolio of the selected fixed income instruments with an arbitrary weightage.
    logging.info("\n Solution to Question 2.1.")

    # Create portfolio using the assumption above
    portfolio_manager = pf.PortfolioManager(config, instruments)
    portfolio_manager.create_portfolio()
    logging.info("Portfolio Snapshot with total initial fund of %s: \n %s",
                 portfolio_manager.total_fund,
                 portfolio_manager.portfolio[['cusip', 'issuer', 'weight', 'quantity', 'market_value']])

    # Solution to 2.2 Calculate the daily yield changes of the portfolio
    logging.info("\n Solution to Question 2.2.")

    # Create DB connection to fetch yield curve to calculate portfolio value
    try:
        yield_curve_fetcher = db.SQLiteYieldCurveFetcher(db_name, yield_curve_table_name)
    except (NameError, AttributeError) as e:
        assert isinstance(as_of_date, object)
        logging.error(f'{e}: Fail to create connection fetching all portfolio instruments %s', as_of_date)
        yield_curve_fetcher = None

    # Create daily yield report
    res = portfolio_manager.calculate_daily_yield_change(config, yield_curve_fetcher)
    portfolio_manager.generate_portfolio_yield_report(res)
    ut.write_to_excel(start_date=config['PORTFOLIO']['daily_yield_change_start_date'],
                      as_of_date=as_of_date,
                      config=config,
                      report_name='portfolio_daily_yield_report',
                      config_id=config_id,
                      data=res)

    # Stretch to Q2 -> More important metrics
    # Enhancement - Perform interpolation on yield curve for as of date
    # Generate cashflow table for risk management purpose
    df_yc = yield_curve_fetcher.fetch_data_for_dates('US Treasury', as_of_date, as_of_date)
    # interpolated_yield = ut.interpolate_yield_curve(df_yc['tenor'], df_yc['yield_to_maturity'])

    cashflows_by_cusip = []
    for i in portfolio_manager.portfolio.index:
        df_cf = generate_cashflows(portfolio_manager.portfolio.iloc[i], df_yc)
        df_cf['cusip'] = portfolio_manager.portfolio.iloc[i]['cusip']
        df_cf['cashflow_amount'] = portfolio_manager.portfolio.iloc[i]['quantity'] * df_cf['cashflow']
        cashflows_by_cusip.append(df_cf)
        if i == 0:
            logging.info("\n Enhancement to Q2 \n Sample Cashflow Report: \n %s",
                         df_cf[['cashflow_date', 'cashflow_amount', 'corresponding_zero_rate']])
        else:
            pass

    # Write detailed cashflow report
    ut.write_to_excel(start_date=as_of_date,
                      as_of_date=as_of_date,
                      config=config,
                      report_name='cashflow_report',
                      data=pd.concat(cashflows_by_cusip),
                      config_id=config_id,
                      index_on_off=False)

    ####################################################################################################################
    # The code below is the solution to provide solution to
    # 4. DV01 Calculation:
    # 4.1 Compute the DV01 for each of your selected instruments for every day over the 2 years.

    # 3. VaR Calculation:
    # 3.1 Implement the Historical Simulation method to calculate the VaR for this portfolio.
    # 3.2 Calculate the 1-day VaR for the portfolio at both the 95% and 99% confidence levels.
    ####################################################################################################################

    # Solution to 4.1
    portfolio_manager.portfolio['last_yield'] = portfolio_manager.portfolio.apply(lambda x: calculate_ytm(x), axis=1)
    portfolio_manager.portfolio[['modified_duration',
                                 'dv01',
                                 'convexity',
                                 'cr01']] = portfolio_manager.portfolio.apply(lambda x: bond_duration(x), axis=1)

    logging.info("\n Solution to 4.1 \n Sample DV01 Report: \n %s",
                 portfolio_manager.portfolio[['as_of_date',
                                              'cusip',
                                              'issuer',
                                              'coupon_rate',
                                              'maturity_date',
                                              'market_value',
                                              'last_yield',
                                              'modified_duration',
                                              'dv01',
                                              'convexity',
                                              'cr01']])

    # Solution to 3.1 and 3.2
    # Enhancements include: Historical VaR with both Full Reval sensitivity based, Monte Carlo VaR
    logging.info("Solution to 3.1 and 3.2")

    # Set up for risk reporting
    risk_summary = {}
    risk_report = {}

    for r in [config['RISK_ENGINE'][key] for key in config['RISK_ENGINE'] if key.startswith('run_config_')]:

        risk_metric = r.split("|")[0]
        scenario_approach = r.split("|")[1]
        valuation_approach = r.split("|")[2].split("^")[0]
        pricing_model = r.split("|")[2].split("^")[1]
        loss_calculation_approach = r.split("|")[3].split("^")[0]
        if loss_calculation_approach in ['expected_shortfall', 'var_type']:
            n_day = int(r.split("|")[3].split("^")[1])
            m_percentile = int(r.split("|")[3].split("^")[2])
            # var_detail = "%s-day %s at %s percentile" % (r.split("|")[3].split("^")[1],
            #                                              loss_calculation_approach,
            #                                              r.split("|")[3].split("^")[2])
        else:
            n_day = None
            m_percentile = None

        # Start calculating risk metrics
        try:
            if risk_metric == 'var':
                risk_obj = reng.TailLoss(config,
                                         scenario_approach,
                                         valuation_approach,
                                         pricing_model,
                                         loss_calculation_approach,
                                         n_day,
                                         m_percentile,
                                         portfolio_manager.portfolio,
                                         yield_curve_fetcher,
                                         portfolio_manager.portfolio_pnl)
                risk_obj.calculate_pnl()
                total_loss, pnl_vector = risk_obj.calculate_loss('portfolio_daily_pnl')
                risk_summary[r] = total_loss
                risk_report[r] = pnl_vector

            if risk_metric == 'stress_testing':
                pass
                # risk_obj = reng.StressTesting()

            # logging.info("Running Risk Engine using Model Configuration as below \n"
            #              "Risk Metric: %s \n"
            #              "Scenario generation approach: %s \n"
            #              "Valuation approach: %s \n"
            #              "Pricing model: %s \n"
            #              "Loss calculation approach: %s \n%s \n"
            #              "Final Result = %s \n",
            #              risk_metric, scenario_approach, valuation_approach, pricing_model,
            #              loss_calculation_approach, var_detail, round(total_loss, 2))

        except (AttributeError, ValueError) as e:
            logging.error(f'Fail to run {r} due to {e} \n')

    df_risk_sum_report = pd.DataFrame.from_dict(risk_summary,
                                                orient='index',
                                                columns=['pnl']).reset_index().rename(columns={'index': 'Model Config'})

    ut.write_to_excel(as_of_date,
                      as_of_date,
                      config,
                      'scenario_loss_pnl_vector',
                      ut.convert_dict_to_dataframe(risk_report),
                      config_id=config_id)

    # Stretch to Q3 - Stress testing
    scenario_manager = sm.ScenarioManager()
    cashflows_all = pd.concat(cashflows_by_cusip)
    pf_all = []
    for c in portfolio_manager.portfolio['cusip'].unique():
        _pf = portfolio_manager.portfolio.loc[portfolio_manager.portfolio['cusip'] == c].copy()
        for scn in scenario_manager.scenarios.keys():
            _cf = cashflows_all.loc[cashflows_all['cusip'] == c].copy()
            _pf['%s price' % scn] = _pf.apply(lambda x: bond_price_zero_curve(scenario_manager.scenarios[scn], x, _cf),
                                              axis=1)
            _pf['stress_testing|%s|full_revaluation^zero_curve' % scn] = ((_pf['%s price' % scn]
                                                                          - _pf['last_price'])
                                                                          * _pf['quantity'])

        pf_all.append(_pf)
    portfolio_manager.portfolio = pd.concat(pf_all)
    _report_str = portfolio_manager.portfolio[['stress_testing|financial_crisis_2008|full_revaluation^zero_curve',
                                               'stress_testing|oil_crisis_1974|full_revaluation^zero_curve']].sum().\
        reset_index().rename(columns={'index': 'Model Config', 0: 'pnl'})

    df_final_report = round(pd.concat([df_risk_sum_report, _report_str]), 2)

    logging.info("High Level Risk Report \n %s",
                 ut.format_report(df_final_report))

    ut.write_to_excel(as_of_date,
                      as_of_date,
                      config,
                      'risk_summary_report',
                      ut.format_report(df_final_report),
                      config_id,
                      index_on_off=False)


if __name__ == "__main__":
    main()
