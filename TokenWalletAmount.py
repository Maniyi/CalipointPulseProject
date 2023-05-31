# Importing necessary libraries
import streamlit as st
import requests
import json

# Set the layout of the Streamlit application
st.set_page_config(layout="wide")
# Display a title for the application in HTML format
st.markdown("<h1 style='text-align: center; color: white;'>PulseChain Token Info</h1>",
            unsafe_allow_html=True)

# Define a function to get token information for a given address
# The function is cached to prevent multiple calls for the same address


@st.cache_data
def get_token_info(address):
    # API endpoint
    url = "https://scan.pulsechain.com/api"
    # Parameters for the API call
    params = {
        "module": "account",
        "action": "tokenlist",
        "address": address
    }
    headers = {
        "accept": "application/json"
    }

    # Try to send the request
    try:
        response = requests.get(url, params=params, headers=headers)
    except requests.exceptions.RequestException as e:
        # If an error occurs during the request, show it in Streamlit and return empty results
        st.error("Exception occurred: {}".format(e))
        return [], 0

    # Initialize results
    result = []
    total_balance_usd = 0
    # Check if the response status is successful
    if response.status_code == 200:
        # Extract the JSON data from the response
        data = response.json()
        # Get the tokens from the data
        tokens = data.get("result")
        # If there are no tokens, the address is invalid
        if tokens is None:
            st.error("Please, enter a valid address.")
            return [], 0
        # Process each token
        for token in tokens:
            # Extract the token properties
            token_name = token["name"]
            token_symbol = token["symbol"]
            token_contract_address = token["contractAddress"]
            # Try to convert the decimals property to an integer
            try:
                token_decimals = int(token["decimals"])
            except ValueError:
                # If it's not possible, use a default value of 1
                token_decimals = 1

            # Try to get the balance of the token
            try:
                balance = get_token_balance(token_contract_address, address)
                if balance is not None:
                    # Convert the balance to the correct decimal scale
                    balance = int(balance) / (10 ** token_decimals)
                    # Get the price of the token in USD
                    price_usd = get_price_usd(token_contract_address)
                    if price_usd is not None:
                        # Compute the balance in USD and add it to the total
                        balance_usd = balance * float(price_usd)
                        total_balance_usd += balance_usd

                    # Add the token information to the results
                    result.append(
                        {
                            'Name': token_name,
                            'Symbol': token_symbol,
                            'Contract Address': token_contract_address,
                            'Decimals': token_decimals,
                            'Balance': balance,
                            'Balance USD': balance_usd if price_usd is not None else 'Price not available',
                        }
                    )
            except Exception as e:
                # If an error occurs while processing a token, show it in Streamlit and continue with the next token
                st.error("Exception occurred: {}".format(e))
                continue

    else:
        # If the response status is not successful, show an error in Streamlit
        st.error(f"Error occurred. Status code: {response.status_code}")

    # Return the results and the total balance in USD (rounded to 2 decimal places)
    return result, round(total_balance_usd, 2)


# Define a function to get the balance of a token for a given address
def get_token_balance(contractAddressHash, addressHash):
    # API endpoint
    base_url = "https://scan.pulsechain.com/api"
    # Parameters for the API call
    params = {
        'module': 'account',
        'action': 'tokenbalance',
        'contractaddress': contractAddressHash,
        'address': addressHash,
    }

    # Try to send the request
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            # If the response is successful, return the balance from the data
            data = response.json()
            return data.get('result')
        else:
            # If the response is not successful, return None
            return None
    except requests.exceptions.RequestException as e:
        # If an error occurs during the request, show it in Streamlit
        st.error("Exception occurred: {}".format(e))
        return None


# Define a function to get the price of a token in USD
def get_price_usd(token_addresses):
    # API endpoint
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_addresses}"

    # Try to send the request
    try:
        response = requests.get(url)
        data = json.loads(response.text)
        # Extract the price in USD from the data, if it exists
        if data and 'pairs' in data and data['pairs']:
            if 'priceUsd' in data['pairs'][0]:
                return data['pairs'][0]['priceUsd']

        # If the price in USD does not exist, return None
        return None
    except requests.exceptions.RequestException as e:
        # If an error occurs during the request, show it in Streamlit
        st.error("Exception occurred: {}".format(e))
        return None


# Create a text input in Streamlit for the wallet address
wallet_address = st.text_input("Enter your wallet address")

# If a wallet address is entered, get the token information and display it in Streamlit
if wallet_address:
    tokens, total_balance_usd = get_token_info(wallet_address)
    # Display the tokens in a DataFrame
    st.dataframe(tokens)
    # Display the total balance in USD in HTML format
    st.markdown(
        f'<h2 style="text-align: center; color: white;">Total balance in USD: <span style="color: green;">${total_balance_usd}</span></h2>', unsafe_allow_html=True)
