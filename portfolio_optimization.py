import argparse
import os
import pandas as pd

parser = argparse.ArgumentParser(description='Portfolio Optimization Beta')
parser.add_argument("-f", '--file_path', type=str, default=r'./output')

args = parser.parse_args()


def combine_csv_files(folder_path):
    dataframes = []

    # Get a list of CSV files in the provided folder that start with 'risk_summary'
    csv_files = [f for f in os.listdir(folder_path) if f.startswith('risk_summary') and f.endswith('.csv')]

    # Load each CSV, add a source column, and append to the list
    for file in csv_files:
        full_path = os.path.join(folder_path, file)
        try:
            df = pd.read_csv(full_path)
            config_name = file.replace('.csv', '').split('_')[-1]  # Extracting configuration name
            df['Source'] = config_name
            dataframes.append(df)
        except Exception as e:
            print(f"Error processing {file}. Error: {e}")

    # Combine all dataframes
    combined_data = pd.concat(dataframes, axis=0, ignore_index=True)

    return combined_data


def find_optimized_portfolio(folder_path,  risk_metric = "var",
                             scenario_approach = "historical",
                             model_selection = "full_revaluation^ytm",
                             model_parameter = "var_type^10^95"):
    # Load combined data from the folder
    combined_data = combine_csv_files(folder_path)

    # Filtering the rows based on the given criteria
    filtered_data = combined_data[
        (combined_data["Risk Metric"] == risk_metric) &
        (combined_data["Scenario Approach"] == scenario_approach) &
        (combined_data["Model Selection"] == model_selection) &
        (combined_data["Model Parameter"] == model_parameter)
        ]

    # Finding the row with the smallest 'pnl'
    min_pnl_row = filtered_data[filtered_data['pnl'] == filtered_data['pnl'].min()]
    min_pnl_source = min_pnl_row['Source'].iloc[0] if not min_pnl_row.empty else None

    return min_pnl_source

print('The optimized portfolio setup is', find_optimized_portfolio(args.file_path))
