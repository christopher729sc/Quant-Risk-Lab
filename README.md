# Quant Risk Lab
The goal of this assignment is to assess your coding, problem-solving, and financial risk modeling abilities.

**Repository Link**: [https://github.com/christopher729sc/Quant-Risk-Lab](https://github.com/christopher729sc/Quant-Risk-Lab)

## Structure

- **Main Files**:
  - `risk_analytics.py`: The primary script for risk analytics.
  - `run.bat`: A batch script to facilitate easy execution.
  - `requirements.txt`: Lists the Python dependencies required.

- **Configuration**:
  - `config/`: Contains multiple `.ini` files to dictate various settings.

- **Data**:
  - `data/`: Input data files including `instrument/` and `market/`.

- **Libraries**:
  - `lib/`: Contains modeling, database, utility, and risk engine modules.

- **Output**:
  - `output/`: Contains results or reports.

## Setup

1. **Set Up a Virtual Environment**: It's recommended to use a virtual environments. Set up a virtual environment using `venv`:

   ```bash
   python -m venv venv_name
   ```

   Activate the virtual environment:

   - On Windows:

     ```bash
     .\venv_name\Scripts\activate
     ```

   - On macOS and Linux:

     ```bash
     source venv_name/bin/activate
     ```

2. Install the required Python packages under virtual environment:

   ```bash
   pip install -r requirements.txt
   ```

3. Adjust the configuration `.ini` files in the `config/` directory (No need to adjust for demo).


4. How to run:

    Option 1: Simple run for demo purpose

    ```bash
    python risk_analytics.py
    ```
    Option 2: Multiple runs including portfolio optimization
    
    start
   ```bash
   run.bat
   ```
   and then run:

   ```bash
   python portfolio_optimization.py
   ```
## Results Review
The result report can be found under output folder, including
1. Essential run results: output\log\runlog.log
2. Cashflow report: Scheduled cashflow for the portfolio 
3. Portfolio: including weights, market value, DV01, CR01, etc.
4. Portfolio daily yield report: Daily yield changes for this portfolio
5. Retrieved yield data: Retrieves this yield data for the chosen instruments over a given date range.
6. Risk summary report: Comprehensive risk report
7. PnL vector: Detailed PnL vector


## Features

- **Database Integration**: Supports SQLite with target state to switch to SQL Express.
- **Flexible Configuration**: Allows for dynamic risk metric calculations, scenario generations, bond pricing models, and more.
- **Reporting**: Generates various reports including portfolio daily yield, cashflow reports, PnL vectors, and risk summaries.

## Dependencies

- configparser
- numpy
- openpyxl
- pandas
- scipy



