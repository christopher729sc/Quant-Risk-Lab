import pandas as pd
import scipy as sp


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
