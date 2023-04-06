import pandas as pd
from cost_of_capital_func import *
import uvicorn
from fastapi import FastAPI

app = FastAPI()


region_list = [
    'North America',
    'Europe',
    'Japan',
    'Asia Pacific ex Japan',
    'Developed ex US',
    'Developed Markets',
    'Global'
]

@app.get("/regions")
def get_regions():
    return region_list

@app.get("/analyze")
def analyze(region: str, ticker: str):

    if region not in region_list:
        return {"error": "Invalid region selected. Please select a valid region from the list."}

    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french"
    factor_path, momentum_path = get_factor_links(region)

    factors_df = download_zip(url, factor_path)
    factors_df = clean_data(factors_df)

    momentum_df = download_zip(url, momentum_path)
    momentum_df = clean_data(momentum_df)

    merged_df = merge_factors_and_momentum(factors_df, momentum_df)

    start_date = factors_df['Date'].min()
    end_date = factors_df['Date'].max()
    hist_prices_df = download_historical_prices(ticker, start_date, end_date)
    if hist_prices_df.empty:
        return {"error": "Invalid ticker symbol. Please enter a valid ticker symbol."}

    merged_df = merged_df.merge(hist_prices_df, on='Date')
    merged_df['RI-RF'] = merged_df['RI'] - merged_df['RF']

    model, Alpha, Beta_Mkt, Beta_SMB, Beta_HML, Rf = run_regression(merged_df)

    result = {}
    result["Alpha"] = Alpha
    result["Beta_Mkt"] = Beta_Mkt
    result["Beta_SMB"] = Beta_SMB
    result["Beta_HML"] = Beta_HML
    result["Rf"] = Rf

    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)