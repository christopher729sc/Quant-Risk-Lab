import pandas as pd


class VaR:

    def __init__(self, data: pd.DataFrame):
        self.data = data
        # self.df_var = {}

    def calculate_var(self, pnl_col, n_day: int, var_percentile: float):

        if n_day == 1:
            _data = self.data.copy()
            _data['%s_day_pnl' % n_day] = _data[pnl_col].copy()
        else:
            _data = self.data.copy()
            _data['%s_day_pnl' % n_day] = _data[pnl_col].diff(10)
            pnl_col = '%s_day_pnl' % n_day

        var_value = _data[pnl_col].quantile(1 - var_percentile)
        closest_value_to_var = _data.loc[(_data[pnl_col] - var_value).abs().idxmin(), pnl_col]
        pnl_vector = _data.loc[_data[pnl_col] == closest_value_to_var].copy()
        pnl_vector['var_value'] = var_value
        pnl_vector.reset_index(inplace=True)
        pnl_vector['var_type'] = f'{n_day}-Day {int(var_percentile * 100)}% VaR'
        pnl_vector.set_index('var_type', inplace=True)
        return pnl_vector


