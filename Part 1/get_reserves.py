# This code fetches the reserves of the WETH-USDT pair on Uniswap v2.

from web3 import Web3
import json

# Connect to a node. If using Infura, it should look like this:
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/<YOUR_INFURA_PROJECT_ID>'))

# Load the ABI of the UniswapV2Pair contract
with open('UniswapV2Pair.json', 'r') as f:
    pairABI = json.load(f)

# Create a contract object with the pair address.
weth_usdt_addr = '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852'
pair = w3.eth.contract(address=weth_usdt_addr, abi=pairABI)

# Call the getReserves() function
reserves = pair.functions.getReserves().call()

# Print the reserves: [res_weth, res_usdt, timestamp]
print(reserves) # [16955718197081157997253, 29720979785430, 1686648623]