import pandas as pd
import sqlite3


class DatabaseInitialSetup:
    def __init__(self, db_name: str, yield_curve_raw_data: str, yield_curve_table_name: str):
        """
        Initialize the DatabaseInitialSetup with a connection to the SQLite database.

        Parameters:
        - db_name (str): Name of the SQLite database file.
        - yield_curve_raw_data (str): Path to the CSV file containing yield data.
        - yield_curve_table_name (str): Name of the table in the SQLite database where yield data will be saved.
        """

        self.conn = sqlite3.connect(db_name)  # Establish a connection to the SQLite database
        self.cursor = self.conn.cursor()  # Create a cursor object to interact with the SQLite database
        self.yield_curve_raw_data = yield_curve_raw_data  # Store the path to the CSV file
        self.yield_curve_table_name = yield_curve_table_name  # Store the table name

    def write_data_to_db(self):
        """
        Write data from the CSV file to the SQLite database table
        """
        # Load data from the specified CSV file into a DataFrame
        _df_yield_curve = pd.read_csv(self.yield_curve_raw_data)

        # Write the data from the DataFrame to the specified table in the SQLite database
        _df_yield_curve.to_sql(self.yield_curve_table_name,
                               self.conn,
                               if_exists="replace",
                               index=False)

    def close(self):
        """
        Close the database connection to free up resources.
        """
        self.conn.close()


class YieldCurveFetcher:
    def __init__(self, db_name: str, yield_curve_table_name: str):
        """
        Initialize the YieldCurveFetcher with a connection to the SQLite database.

        Parameters:
        - db_name (str): Name of the SQLite database file.
        - yield_curve_table_name (str): Name of the table in the database containing yield curve data.
        """
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.yield_curve_table_name = yield_curve_table_name

    def fetch_data_for_dates(self, start_date: str, end_date: str) -> list:
        """
        Fetch yield curve data for the specified date range.

        Parameters:
        - start_date (str): Start date in the format 'YYYY-MM-DD'.
        - end_date (str): End date in the format 'YYYY-MM-DD'.

        Returns:
        - list: List of rows containing the retrieved data.
        """
        query = f"""
        SELECT * FROM {self.yield_curve_table_name}
        WHERE date BETWEEN ? AND ?
        """

        df = pd.read_sql_query(query, self.conn, params=(start_date, end_date))
        return df.set_index('Date')

    def close(self):
        """
        Close the database connection to free up resources.
        """
        self.conn.close()
