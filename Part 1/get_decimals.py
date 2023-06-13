# This code fetches the decimals of the USD Tether (USDT) token on the Ethereum mainnet.
from web3 import Web3
import json

# Connect to a node. If using Infura, it should look like this:
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/<YOUR_INFURA_PROJECT_ID>'))

# Load the ABI of the ERC20 contract
with open('ERC20ABI.json', 'r') as f:
    ercABI = json.load(f)

# Create a contract object with the token address. Here we used USDT.
token = w3.eth.contract(address='0xdAC17F958D2ee523a2206206994597C13D831ec7', abi=ercABI)

# Call the decimals() function
decimals = token.functions.decimals().call()

# Print the decimals
print(decimals) # 6