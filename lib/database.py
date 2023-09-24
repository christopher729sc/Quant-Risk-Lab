import logging
import pandas as pd
import sqlite3

"""
Data Source: U.S. Department of the Treasury
Description:
This dataset provides daily treasury yield curve rates from the U.S. Department of the Treasury. 
The U.S. Department of the Treasury publishes these rates at approximately 3:30 PM each trading day. 
Users can select specific dates to retrieve historical rates, 
providing valuable insights into how yield curves have shifted over time.

Link:
https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve

Further solution using API
https://fiscaldata.treasury.gov/api-documentation/#how-to-access-our-api
"""


# SQLite approach
class SQLiteInitialSetup:
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


class SQLiteYieldCurveFetcher:
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

    def fetch_data_for_dates(self, instrument: str, start_date: str, end_date: str) -> pd.DataFrame:
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
        WHERE instrument = ? and date BETWEEN ? AND ? 
        """
        try:
            df = pd.read_sql_query(query, self.conn, params=(instrument, start_date, end_date))
            return df.set_index('date')
        except {KeyError, TypeError, ValueError} as e:
            logging.warning(f'{e} Fetching data from database failed. The data does not exist')

    def close(self):
        """
        Close the database connection to free up resources.
        """
        self.conn.close()


# TODO Build the functionality to update yield curve on daily basis
class YieldCurveRefresher:
    pass


# TODO SQL Express approach
# Code prototype can be as below

class SQLServerExpressConnector:

    # Sample Usage:
    # connector = SQLServerExpressConnector('YOUR_SERVER_NAME', 'YOUR_DATABASE_NAME', 'YOUR_USERNAME', 'YOUR_PASSWORD')
    # connector.connect()
    # rows = connector.execute_query("SELECT * FROM YourTableName")
    # for row in rows:
    #     print(row)
    # connector.close()

    def __init__(self, server, database, username, password):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.conn = None

    def connect(self):
        """
        Establish a connection to SQL Server Express.
        """
        conn_str = (f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                    f'SERVER={self.server};'
                    f'DATABASE={self.database};'
                    f'UID={self.username};PWD={self.password}')
        # self.conn = pyodbc.connect(conn_str)
        print('Setup Successful', conn_str)

    def execute_query(self, query):
        """
        Execute an SQL query and return the results.
        """
        if self.conn is None:
            raise ValueError("Connection not established. Please connect first.")

        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def close(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
