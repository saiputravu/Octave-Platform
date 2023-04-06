import requests
import pandas as pd
import io
import zipfile
import yfinance as yf
import statsmodels.api as sm
from bs4 import BeautifulSoup

def get_factor_links(region):
    region_dict = {
        'North America': (
            'ftp/North_America_5_Factors_CSV.zip',
            'ftp/North_America_Mom_Factor_CSV.zip'
        ),
        'Europe': (
            'ftp/Europe_5_Factors_CSV.zip',
            'ftp/Europe_Mom_Factor_CSV.zip'
        ),
        'Japan': (
            'ftp/Japan_5_Factors_CSV.zip',
            'ftp/Japan_Mom_Factor_CSV.zip'
        ),
        'Asia Pacific ex Japan': (
            'ftp/Asia_Pacific_ex_Japan_5_Factors_CSV.zip',
            'ftp/Asia_Pacific_ex_Japan_MOM_Factor_CSV.zip'
        ),
        'Developed ex US': (
            'ftp/Developed_ex_US_5_Factors_CSV.zip',
            'ftp/Developed_ex_US_Mom_Factor_CSV.zip'
        ),
        'Developed Markets': (
            'ftp/Developed_5_Factors_CSV.zip',
            'ftp/Developed_Mom_Factor_CSV.zip'
        ),
        'Global': (
            'ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip',
            'ftp/F-F_Momentum_Factor_CSV.zip'
        )
    }
    return region_dict[region]



def download_zip(url, file_path):
    response = requests.get(url + "/" + file_path)
    if response.status_code == 200:
        zipfile_in_memory = io.BytesIO(response.content)
        with zipfile.ZipFile(zipfile_in_memory, "r") as zip_ref:
            csv_filename = zip_ref.namelist()[0]
            with zip_ref.open(csv_filename) as csv_file:
                df = pd.read_csv(csv_file, skiprows=6)
    else:
        raise Exception("Failed to download the file")

    return df


def clean_data(df):
    index_to_drop = df[df.iloc[:, 0] == " Annual Factors: January-December"].index
    df = df.iloc[:index_to_drop[0]]
    df = df.rename(columns={'Unnamed: 0': 'Date'})
    df['Date'] = df['Date'].str.strip()
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m')
    date_threshold = df['Date'].max() - pd.DateOffset(months=60)
    df = df[df['Date'] >= date_threshold]
    return df


def download_historical_prices(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date - pd.DateOffset(months=1), end=end_date, interval="1mo")
    df['RI'] = df['Adj Close'].pct_change()
    df = df.reset_index()
    return df

def merge_factors_and_momentum(factors_df, momentum_df):
    merged_df = factors_df.merge(momentum_df, on='Date')
    df_columns = merged_df.columns.tolist()
    df_columns.remove('Date')
    merged_df[df_columns] = merged_df[df_columns].astype(float)
    merged_df.loc[:, merged_df.columns != 'Date'] /= 100

    return merged_df

def run_regression(merged_df):
    y = merged_df['RI-RF']
    X = sm.add_constant(merged_df[['Mkt-RF', 'SMB', 'HML']])
    model = sm.OLS(y, X).fit()
    Alpha = model.params[0]
    Beta_Mkt = model.params[1]
    Beta_SMB = model.params[2]
    Beta_HML = model.params[3]
    Rf = merged_df['RF'].mean()
    print(model.summary())

    return model, Alpha, Beta_Mkt, Beta_SMB, Beta_HML, Rf
