import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from cost_of_capital_func import *

# Your functions (get_factor_links, download_zip, clean_data, etc.) should be placed in a separate Python file
# and imported using the "from your_functions_module import *" line above.

region_dict = {
    'North America': ('Fama/French North American 5 Factors', 'North American Momentum Factor (Mom)'),
    'Europe': ('Fama/French European 5 Factors', 'European Momentum Factor (Mom)'),
    'Japan': ('Fama/French Japanese 5 Factors', 'Japanese Momentum Factor (Mom)'),
    'Asia Pacific ex Japan': ('Fama/French Asia Pacific ex Japan 5 Factors', 'Asia Pacific ex Japan Momentum Factor (Mom)'),
    'Developed ex US': ('Fama/French Developed ex US 5 Factors', 'Developed ex US Momentum Factor (Mom)'),
    'Developed Markets': ('Fama/French Developed 5 Factors', 'Developed Momentum Factor (Mom)'),
    'Global': ('Fama/French 5 Factors (2x3)', 'Momentum Factor (Mom)')
}

sns.set(style='darkgrid')

st.title('Stock Factor Analysis')

region = st.selectbox('Select a region:', list(region_dict.keys()))
ticker = st.text_input('Enter the stock ticker symbol:')

if st.button('Analyze'):
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
            st.error('Invalid ticker symbol. Please enter a valid ticker symbol.')
        else:    
            merged_df = merged_df.merge(hist_prices_df, on='Date')
            merged_df['RI-RF'] = merged_df['RI'] - merged_df['RF']

            model, Alpha, Beta_Mkt, Beta_SMB, Beta_HML, Rf = run_regression(merged_df)

            st.write(f"Alpha: {Alpha:.6f}")
            st.write(f"Beta Mkt: {Beta_Mkt:.6f}")
            st.write(f"Beta SMB: {Beta_SMB:.6f}")
            st.write(f"Beta HML: {Beta_HML:.6f}")
            st.write(f"Rf (Monthly): {Rf:.6f}")

            factors_to_plot = factors_df.copy()
            factors_to_plot.set_index('Date', inplace=True)
            factors_to_plot = factors_to_plot.apply(pd.to_numeric)

            plt.figure(figsize=(12, 6))
            plt.plot(factors_to_plot)
            plt.xlabel('Date')
            plt.ylabel('Returns')
            plt.title('Factor Returns Over Time')
            plt.legend(factors_to_plot.columns)
            st.pyplot(plt.gcf())
            plt.clf()

            momentum_to_plot = momentum_df.copy()
            momentum_to_plot.set_index('Date', inplace=True)
            momentum_to_plot = momentum_to_plot.apply(pd.to_numeric)

            plt.figure(figsize=(12, 6))
            plt.plot(momentum_to_plot)
            plt.xlabel('Date')
            plt.ylabel('Returns')
            plt.title('Momentum Returns Over Time')
            plt.legend(momentum_to_plot.columns)
            st.pyplot(plt.gcf())
            plt.clf()

            stock_returns_to_plot = hist_prices_df[['Date', 'RI']].copy()
            stock_returns_to_plot.set_index('Date', inplace=True)

            plt.figure(figsize=(12, 6))
            plt.plot(stock_returns_to_plot)
            plt.xlabel('Date')
            plt.ylabel('Returns')
            plt.title('Historical Stock Returns Over Time')
            st.pyplot(plt.gcf())
            plt.clf()

            merged_df['Fitted'] = model.predict(sm.add_constant(merged_df[['Mkt-RF', 'SMB', 'HML']]))

            plt.figure(figsize=(12, 6))
            plt.scatter(merged_df['Fitted'], merged_df['RI-RF'])
            plt.xlabel('Fitted Returns')
            plt.ylabel('Actual Returns')
            plt.title('Fitted vs. Actual Stock Returns')
            st.pyplot(plt.gcf())
            plt.clf()
        