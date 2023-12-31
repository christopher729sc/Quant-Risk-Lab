import datetime as dt
import logging
import pandas as pd
import scipy as sp
import sys
from dateutil.relativedelta import relativedelta


def interpolate_yield_curve(time_to_maturity, rates, interpolate_method='slinear'):
    """
    Interpolates the yield curve based on the provided time to maturities and raw rates.

    Parameters:
    - time_to_maturity (list): List of original time to maturities.
    - raw_rates (list): List of original rates corresponding to the time to maturities.
    - interpolate_method (str): The interpolation method to use. Default is 'slinear'.

    Returns:
    - new_time_to_maturity (list): List of new time to maturities.
    - new_rates (list): Interpolated rates for the new time to maturities.
    """
    time_to_maturity = list(time_to_maturity)
    rates = list(rates)

    if len(time_to_maturity) != len(rates):
        raise ValueError("The lengths of time_to_maturity and raw_rates must be the same.")

    start = time_to_maturity[0]
    end = time_to_maturity[-1]
    increment = 1

    interpolated_time_to_maturity = [start + i * increment for i in range(int((end - start) / increment) + 1)]

    f = sp.interpolate.interp1d(x=time_to_maturity, y=rates, kind=interpolate_method)
    interpolated_rates = f(interpolated_time_to_maturity)

    return pd.DataFrame(data=interpolated_rates, index=interpolated_time_to_maturity, columns=["rate"])


def years_prior(as_of_date: str, years: int) -> str:
    """
    Returns the date 'years' years prior to the provided 'as_of_date'.

    :param as_of_date: The starting date in the format "YYYY-MM-DD".
    :param years: The number of years to go back.
    :return: The date 'years' years before 'as_of_date'.
    """

    as_of_date_dt = dt.datetime.strptime(as_of_date, "%Y-%m-%d")
    date_n_years_prior = as_of_date_dt - relativedelta(years=years)
    return date_n_years_prior.strftime("%Y-%m-%d")


def pre_process_mapping(data_list):
    result = {}
    for item in data_list:
        parts = item.split('^')
        if parts[1] == 'US Treasury':
            _tenor = int(parts[2])
        else:
            _tenor = parts[2]
        result[parts[0]] = {'yield_curve_name': parts[1], 'tenor': _tenor}

    return result


def calculate_years_to_maturity(as_of_date: str, maturity_date: str) -> float:
    """
    Calculates the years to maturity for each date in the given data.

    :param as_of_date: starting date in 'YYYY-MM-DD' format.
    :param maturity_date: The maturity date in 'YYYY-MM-DD' format.
    :return: maturities in years as float
    """
    try:
        as_of_date_dt = dt.datetime.strptime(as_of_date, '%Y-%m-%d').date()
        maturity_date_dt = dt.datetime.strptime(maturity_date, '%Y-%m-%d').date()

        # Calculate difference in days and then convert to years
        days_difference = (maturity_date_dt - as_of_date_dt).days
        years_to_maturity = days_difference / 365.25
        return years_to_maturity

    except ValueError:
        logging.error('Invalid date format')
        return 0


def write_to_excel(start_date: str,
                   as_of_date: str,
                   config,
                   report_name: str,
                   data: pd.DataFrame,
                   config_id: str,
                   index_on_off: bool = True) -> None:
    """
    Write the portfolio yields DataFrame to an Excel file based on the designated path from the config file.
    """

    try:
        output_path = config['REPORT'][report_name]
        output_path = output_path.replace('YYYYMMDD2', 'YYYYMMDD2_%s' % config_id)
        output_path = output_path.replace('YYYYMMDD1', start_date.replace('-', ''))
        output_path = output_path.replace('YYYYMMDD2', as_of_date.replace('-', ''))

        data.to_csv(output_path, index=index_on_off)
        logging.info(f"{report_name} successfully saved to {output_path}")

    except KeyError:
        logging.error("The report was not found in the config file.")
    except Exception as e:
        logging.error(f"Error saving report to Excel: {e}")


def convert_dict_to_dataframe(data_dict: dict) -> pd.DataFrame:
    """
    Combines data frames from a dictionary into a single data frame.

    :param data_dict: Dictionary containing model configurations as keys and corresponding data frames as values.
    :return: Combined data frame.
    """
    dfs = []
    for key, df in data_dict.items():
        if df is not None:
            df = df.copy()
            df['model_config'] = key
            dfs.append(df)

    combined_df = pd.concat(dfs)
    return combined_df


def format_report(data):
    # Split the 'Model Config' column into separate components
    data['Risk Metric'] = data['Model Config'].apply(lambda x: x.split('|')[0] if '|' in x else x)
    data['Scenario Approach'] = data['Model Config'].apply(lambda x: x.split('|')[1] if '|' in x else None)
    data['Model Selection'] = data['Model Config'].apply(
        lambda x: x.split('|')[2] if '|' in x and len(x.split('|')) > 2 else None)
    data['Model Parameter'] = data['Model Config'].apply(
        lambda x: x.split('|')[3] if '|' in x and len(x.split('|')) > 3 else None)

    # Reorder columns for the final display
    formatted_data = data[['Risk Metric', 'Scenario Approach', 'Model Selection', 'Model Parameter', 'pnl']]
    return formatted_data


class LoggerUtil(object):
    def __init__(self, output_path='./output/log/runlog.log', stream=sys.stdout):
        self.terminal = stream
        self.log = open(output_path, 'w')

    def write(self, msg):
        self.terminal.write(msg)
        self.log.write(msg)

    def flush(self):
        pass
