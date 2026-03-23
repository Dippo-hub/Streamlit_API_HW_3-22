import pandas as pd
import streamlit as st
import requests
#Name= Nathan Silvey, ID= 0995
#Chosen API: Gecko Cryptocurrency API: https://api.coingecko.com/api/
link='https://api.coingecko.com/api/v3'
@st.cache_data
def get_currency_list():
    return requests.get(f'{link}/coins/list').json()
@st.cache_data
def get_market_data(id):
    try:
        response = requests.get(f'{link}/coins/{id}', params={'localization': 'false', 'tickers': 'false', 'market_data': 'true', 'sparkline': 'false'})
        if response.status_code != 200:
            st.error(f"API request failed with status {response.status_code} for {id}")
            return None
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Request error fetching market data for {id}: {e}")
        return None
    except ValueError as e:  # JSONDecodeError
        st.error(f"Invalid JSON response for {id}: {e}")
        return None

@st.cache_data
def get_price_history(id, days='365'):
    # CoinGecko public API allows max 365 days for historical market_chart data.
    try:
        response = requests.get(f'{link}/coins/{id}/market_chart', params={'vs_currency': 'usd', 'days': days})
        if response.status_code != 200:
            st.error(f"API request failed with status {response.status_code} for {id}")
            return pd.DataFrame()
        data = response.json()
        if 'error' in data:
            st.error(data['error'])
            return pd.DataFrame()
        prices = data.get('prices', [])
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df.set_index('date')
    except requests.exceptions.RequestException as e:
        st.error(f"Request error fetching price history for {id}: {e}")
        return pd.DataFrame()
    except ValueError as e:  # JSONDecodeError is a ValueError
        st.error(f"Invalid JSON response for {id}: {e}")
        return pd.DataFrame()

def dataframe_setup(currency):
    data = get_market_data(currency)
    if data and 'market_data' in data:
        return pd.DataFrame([{
            'name': data.get('name'),
            'current_price': data['market_data']['current_price'].get('usd'),
            'market_cap': data['market_data']['market_cap'].get('usd'),
            'total_volume': data['market_data']['total_volume'].get('usd')
        }])
    return pd.DataFrame()

currency_list=get_currency_list()

df_currency=pd.DataFrame(currency_list)

if 'name' not in df_currency.columns:
    st.error("Failed to load cryptocurrency list from API. Please check your internet connection or try again later.")
    st.stop()

if __name__ == '__main__':
   st.title('Cryptocurrency Prices')
   st.selectbox('Select a cryptocurrency', df_currency['name'], key='currency')
   selected_currency = st.session_state.currency
   st.slider('Select number of days for historical data', min_value=1, max_value=365, value=30, key='days')
   selected_days = st.session_state.days
   if selected_currency:
       selected_id = df_currency[df_currency['name'] == selected_currency]['id'].values[0]
       selected_data = get_market_data(selected_id)  # Fetch once
       working_df = dataframe_setup(selected_id)
       history_df = get_price_history(selected_id, days=selected_days)

       st.subheader(f"{selected_currency} Market Data")
       if not working_df.empty:
           current_price = working_df.at[0, 'current_price']
           st.metric(label='Current Price (USD)', value=f"${current_price:,.2f}")
           st.table(working_df[['name', 'current_price', 'market_cap', 'total_volume']])
       
       if not history_df.empty:
           st.subheader('Historical Price (USD)')
           st.line_chart(history_df['price'], use_container_width=True)
