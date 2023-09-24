import datetime as dt
import numpy as np
import pandas as pd
import scipy as sp
from dateutil.relativedelta import relativedelta, MO
from scipy.optimize import newton
from scipy.optimize import optimize


def calculate_ytm(instrument):
    """ Calculate modified duration of a bond """

    price = instrument['last_price']
    face_value = instrument['face_value']
    coupon_rate = instrument['coupon_rate']
    freq = int(instrument['coupon_frequency'])
    years_to_maturity = int(instrument['years_to_maturity'])

    def bond_price_diff(_ytm):
        """Difference between calculated bond price and actual bond price."""
        periods = years_to_maturity * freq
        coupon_payment = coupon_rate * face_value / freq
        present_value_of_coupons = sum([coupon_payment / (1 + _ytm / freq) ** t for t in range(1, periods + 1)])
        present_value_of_par = face_value / (1 + _ytm / freq) ** periods
        return price - (present_value_of_coupons + present_value_of_par)

    # Estimate YTM using Newton's method
    ytm = newton(bond_price_diff, coupon_rate, maxiter=1000)

    return ytm


# Specifically for Apple and Walmart
# Hopefully can resolve once I have good data source using API service

# Archived and one-time run only
# file_path = r"./data/market/037833BA7 Price History.csv"
# data = pd.read_csv(file_path)[['Date', 'Price']]
# data['Date'] = pd.to_datetime(data['Date'])
# maturity_date = pd.Timestamp('2045-02-09')
# data['Years_to_Maturity'] = (maturity_date - data['Date']).dt.days / 365.25
# data['Years_to_Maturity'] = data['Years_to_Maturity'].astype(int)
# data['ytm'] = data.apply(lambda x: calculate_ytm(100, x['Price'], 0.0345, x['Years_to_Maturity'], 2), axis=1)


def bond_price_ytm(instrument: pd.Series, yield_to_maturity_override='N/A') -> float:
    """
    Bond Valuation using YTM

    :param instrument: instrument information that has all relative info for pricing
    :param yield_to_maturity_override: ytm override
    :return: Bond price in float.
    """

    # Get contractual info
    coupon_rate = instrument['coupon_rate']
    face_value = instrument['face_value']
    freq = int(instrument['coupon_frequency'])
    years_to_maturity = instrument['years_to_maturity']

    if 'yield_to_maturity' not in instrument.index:
        yield_to_maturity = float(yield_to_maturity_override)
    else:
        yield_to_maturity = float(instrument['yield_to_maturity'])

    _coupon = coupon_rate * face_value / freq
    _yield_to_maturity = yield_to_maturity / freq
    _time_steps = int(years_to_maturity * freq)

    price = sum([_coupon / (1 + _yield_to_maturity) ** i for i in range(1, _time_steps + 1)]) + \
            face_value / (1 + _yield_to_maturity) ** _time_steps

    return price


def generate_cashflows(instrument, df_yc):
    # Get contractual info
    face_value = instrument['face_value']
    coupon_rate = instrument['coupon_rate']
    as_of_date = pd.to_datetime(instrument['as_of_date'])
    next_coupon_date = pd.to_datetime(instrument['next_coupon_date'])
    maturity_date = pd.to_datetime(instrument['maturity_date'])
    freq = int(instrument['coupon_frequency'])

    # Start to build cashflow report
    cashflows = []
    time_list = []
    date_list = []
    date_temp = next_coupon_date
    while maturity_date >= date_temp:
        cashflows.append(face_value * coupon_rate)
        time_list.append((date_temp - as_of_date) / dt.timedelta(365))
        date_list.append(date_temp)
        date_temp = (date_temp + relativedelta(months=int(12 / freq)))
    cashflows.append(face_value)
    date_list.append(maturity_date)
    time_list.append((maturity_date - as_of_date) / dt.timedelta(365))

    # Interpolation to get rates
    f = sp.interpolate.interp1d(x=df_yc['tenor'] / 12, y=df_yc['yield_to_maturity'], kind='slinear')
    r_list = list(f(time_list))

    return pd.DataFrame(data={'cashflow_date': date_list,
                              'cashflow': cashflows,
                              'cashflow_date_in_years': time_list,
                              'corresponding_zero_rate': r_list})


def bond_duration(instrument, dy=0.01):
    """ Calculate modified duration of a bond """

    price = instrument['last_price']
    face_value = instrument['face_value']
    coupon_rate = instrument['coupon_rate']
    freq = int(instrument['coupon_frequency'])
    years_to_maturity = int(instrument['years_to_maturity'])
    ytm = float(instrument['last_yield'])

    # Calculation duration
    ytm_minus = ytm - dy
    price_minus = bond_price_ytm(instrument, ytm_minus)
    ytm_plus = ytm + dy
    price_plus = bond_price_ytm(instrument, ytm_plus)

    modified_duration = (price_minus - price_plus) / (2 * price * dy)
    dv01 = modified_duration * 0.0001 * price
    convexity = (price_minus + price_plus - 2 * price) / (price * dy ** 2)

    return pd.Series([modified_duration, dv01, convexity],
                     index=['modified_duration', 'dv01', 'convexity'])



def bond_convexity(instrument, dy=0.01):
    """ Calculate convexity of a bond """

    price = instrument['last_price']
    face_value = instrument['face_value']
    coupon_rate = instrument['coupon_rate']
    freq = int(instrument['coupon_frequency'])
    years_to_maturity = int(instrument['years_to_maturity'])
    ytm = float(instrument['last_yield'])

    ytm_minus = ytm - dy
    price_minus = bond_price(par, T, ytm_minus, coup, freq)
    ytm_plus = ytm + dy
    price_plus = bond_price(par, T, ytm_plus, coup, freq)

    return convexity