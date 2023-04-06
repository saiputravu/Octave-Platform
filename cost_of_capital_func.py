import requests
import pandas as pd
import io
import zipfile
import yfinance as yf
import statsmodels.api as sm
from bs4 import BeautifulSoup

def get_factor_links(region):
  
    factors_dict = {
        'Fama/French 5 Factors (2x3)': 'ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip',
        'Fama/French Developed 5 Factors': 'ftp/Developed_5_Factors_CSV.zip',
        'Fama/French Developed ex US 5 Factors': 'ftp/Developed_ex_US_5_Factors_CSV.zip',
        'Fama/French European 5 Factors': 'ftp/Europe_5_Factors_CSV.zip',
        'Fama/French Japanese 5 Factors': 'ftp/Japan_5_Factors_CSV.zip',
        'Fama/French Asia Pacific ex Japan 5 Factors': 'ftp/Asia_Pacific_ex_Japan_5_Factors_CSV.zip',
        'Fama/French North American 5 Factors': 'ftp/North_America_5_Factors_CSV.zip'
    }

    mom_dict = {
        'Momentum Factor (Mom)': 'ftp/F-F_Momentum_Factor_CSV.zip',
        'Developed Momentum Factor (Mom)': 'ftp/Developed_Mom_Factor_CSV.zip',
        'Developed ex US Momentum Factor (Mom)': 'ftp/Developed_ex_US_Mom_Factor_CSV.zip',
        'European Momentum Factor (Mom)': 'ftp/Europe_Mom_Factor_CSV.zip',
        'Japanese Momentum Factor (Mom)': 'ftp/Japan_Mom_Factor_CSV.zip',
        'Asia Pacific ex Japan Momentum Factor (Mom)': 'ftp/Asia_Pacific_ex_Japan_MOM_Factor_CSV.zip',
        'North American Momentum Factor (Mom)': 'ftp/North_America_Mom_Factor_CSV.zip'
    }

    region_dict = {
        'North America': ('Fama/French North American 5 Factors', 'North American Momentum Factor (Mom)'),
        'Europe': ('Fama/French European 5 Factors', 'European Momentum Factor (Mom)'),
        'Japan': ('Fama/French Japanese 5 Factors', 'Japanese Momentum Factor (Mom)'),
        'Asia Pacific ex Japan': ('Fama/French Asia Pacific ex Japan 5 Factors', 'Asia Pacific ex Japan Momentum Factor (Mom)'),
        'Developed ex US': ('Fama/French Developed ex US 5 Factors', 'Developed ex US Momentum Factor (Mom)'),
        'Developed Markets': ('Fama/French Developed 5 Factors', 'Developed Momentum Factor (Mom)'),
        'Global': ('Fama/French 5 Factors (2x3)', 'Momentum Factor (Mom)')
    }

    factor_name, momentum_name = region_dict[region]
    factor_url = factors_dict[factor_name]
    momentum_url = mom_dict[momentum_name]
    return factor_url, momentum_url


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
