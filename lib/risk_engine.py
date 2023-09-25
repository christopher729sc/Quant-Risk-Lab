# Customized Utilities
from lib.utils import *
from lib.pricer import *


class TailLoss:

    def __init__(self,
                 config,
                 scenario_approach,
                 valuation_approach,
                 pricing_model,
                 loss_calculation_approach,
                 n_day,
                 m_percentile,
                 portfolio,
                 yield_curve_fetcher,
                 pnl_vectors):

        self.config = config
        self.as_of_date = config['RUN_SETUP']['as_of_date']
        self.scenario_approach = scenario_approach
        self.valuation_approach = valuation_approach
        self.pricing_model = pricing_model
        self.loss_calculation_approach = loss_calculation_approach
        self.n_day = n_day
        self.m_percentile = m_percentile / 100.
        self.pnl_vectors = pnl_vectors
        self.portfolio = portfolio
        self.yield_curve_fetcher = yield_curve_fetcher

        # PNL Override
        if valuation_approach == 'sensitivity_approximation':
            self.pnl_vectors = None

    def get_yield_curve(self):

        inst_yield_curve_mapping = pre_process_mapping(self.config['RISK_ENGINE']
                                                       ['instrument_yield_curve_mapping'].split('|'))
        start_date = self.config['PORTFOLIO']['daily_yield_change_start_date']

        # logging.info("Daily yield change from %s to %s", start_date, self.as_of_date)

        # Fetch yield curve info for the financial instrument
        _yield_curves = []
        for cusip in self.portfolio['cusip']:

            instrument_dict = inst_yield_curve_mapping[cusip]
            try:
                yield_curve_name = instrument_dict['yield_curve_name']
                yield_curve = self.yield_curve_fetcher.fetch_data_for_dates(yield_curve_name,
                                                                            start_date,
                                                                            self.as_of_date)

                if yield_curve_name == 'US Treasury':
                    yield_curve = yield_curve.loc[yield_curve['tenor'] == instrument_dict['tenor']]

                _new_col_name = (yield_curve.loc[self.as_of_date]['instrument'] + "-"
                                 + str(yield_curve.loc[self.as_of_date]['tenor']))

                yield_curve.rename(columns={'yield_to_maturity': _new_col_name}, inplace=True)
                _yield_curves.append(yield_curve[_new_col_name])

            except (TypeError, KeyError) as e:
                logging.warning(f"{e} Not able to locate the yield curve associated with the financial instrument")

        return pd.concat(_yield_curves, axis=1).dropna()

    def monte_carlo_simulation(self):

        yields = self.get_yield_curve()
        portfolio = self.portfolio
        yields.columns = portfolio['cusip']
        yield_changes = yields.pct_change(self.n_day).dropna()

        cov = yield_changes.cov()
        number_of_paths = int(self.config['RISK_ENGINE']['number_of_paths'])
        rand_vector = pd.DataFrame(np.random.multivariate_normal(yield_changes.mean(), cov, number_of_paths))
        simulated_yield_change = rand_vector.multiply(yields.loc[self.as_of_date].values, axis=1)
        return simulated_yield_change

    def calculate_pnl(self):
        yields = self.get_yield_curve()
        portfolio = self.portfolio
        yields.columns = portfolio['cusip']
        yield_changes = yields.diff(self.n_day)

        if self.scenario_approach == 'monte_carlo':
            yield_changes = self.monte_carlo_simulation()
        else:
            pass

        pnl_vectors = yield_changes.multiply(portfolio['dv01'].values,
                                             axis=1).multiply(portfolio['quantity'].values,
                                                              axis=1) * 10000
        pnl_vectors['portfolio_daily_pnl'] = pnl_vectors.sum(axis=1)

        if self.valuation_approach == 'sensitivity_approximation':
            self.pnl_vectors = pnl_vectors
        else:
            pass

    def calculate_loss(self, pnl_col='portfolio_daily_pnl'):

        if self.n_day == 1:
            _data = self.pnl_vectors.copy()
            _data['%s_day_pnl' % self.n_day] = _data[pnl_col].copy()
        else:
            _data = self.pnl_vectors.copy()
            _data['%s_day_pnl' % self.n_day] = _data[pnl_col].diff(10)
            pnl_col = '%s_day_pnl' % self.n_day

        # Start VaR calculation
        var_value = _data[pnl_col].quantile(1 - self.m_percentile)
        closest_value_to_var = _data.loc[(_data[pnl_col] - var_value).abs().idxmin(), pnl_col]
        pnl_vector = _data.loc[_data[pnl_col] == closest_value_to_var].copy()
        pnl_vector['%s loss' % self.loss_calculation_approach] = var_value
        pnl_vector.reset_index(inplace=True)
        pnl_vector['model_config'] = (f'{self.n_day}-Day {int(self.m_percentile * 100)}% '
                                      f'{self.loss_calculation_approach}')
        pnl_vector.set_index('model_config', inplace=True)

        if self.loss_calculation_approach == 'var_type':
            return var_value, pnl_vector

        elif self.loss_calculation_approach == 'expected_shortfall':
            selected_values = _data[_data[pnl_col] <= closest_value_to_var]
            expected_shortfall_value = selected_values[pnl_col].mean()
            return expected_shortfall_value, pnl_vector


class StressTesting:

    def __init__(self):
        pass
