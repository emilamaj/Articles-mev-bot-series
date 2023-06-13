# %%
# The following script reads the event PairCreacted from the Uniswap V2 Factory contract and prints the list of all pairs created on the Uniswap V2 protocol.
# Imports
from web3 import Web3

# Connect to a local node
NODE_URI = 'https://mainnet.infura.io/v3/0ce674ab414048f580429a5bca905096'
w3 = Web3(Web3.HTTPProvider(NODE_URI))
w3local = Web3(Web3.HTTPProvider('http://localhost:8545'))

# Define the contract address
# Uniswap V2 factory contract address
# contract_address = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
# SushiSwap factory contract address
contract_address = '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac'

# Define the contract ABI
factory_abi = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "token0",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "token1",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "pair",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "PairCreated",
        "type": "event"
    }
]

# Instantiate the contract
factory_contract = w3.eth.contract(address=contract_address, abi=factory_abi)

# Get events from the contract
events = factory_contract.events.PairCreated().create_filter(fromBlock='0x0', toBlock='latest').get_all_entries()
print(f'Found {len(events)} events')

# %%
# Implement a function that overcomes the 10k elements limitation of infura.
def getPairEvents(contract, fromBlock, toBlock):
    # This function tries to fetch all the events between fromBlock and toBlock
    # If more than 10k events are found, the function recursively fetches the events in smaller time intervals until all the events are fetched.
    # The function returns a list of all the events fetched.
    # When the 10k limit is reached, get_all_entries() throws an error.
    
    if toBlock == 'latest':
        toBlockPrime = w3.eth.blockNumber
    else:
        toBlockPrime = toBlock

    fetchCount = 0
    
    # Then, recursively fetch events in smaller time intervals
    def getEventsRecursive(contract, _from, _to):
        try:
            events = contract.events.PairCreated().create_filter(fromBlock=_from, toBlock=_to).get_all_entries()
            print("Found ", len(events), " events between blocks ", _from, " and ", _to)
            nonlocal fetchCount 
            fetchCount += len(events)
            return events
        except ValueError:
            print("Too many events found between blocks ", _from, " and ", _to)
            midBlock = (_from + _to) // 2
            return getEventsRecursive(contract, _from, midBlock) + getEventsRecursive(contract, midBlock + 1, _to)
    
    return getEventsRecursive(contract, fromBlock, toBlockPrime)
    

# %%
# Run the recursive getPairevents() function
# events = getPairEvents(factory_contract, 0, w3.eth.blockNumber)
# print(f'Found {len(events)} events')


# %%
# Convert the events to a list of dictionaries
pairDataList = [{'token0': e['args']['token0'],
    'token1': e['args']['token1'],
    'pair': e['args']['pair']} for e in events]
print(f"Here is event #0: {pairDataList[0]}")


# %%
# The following parts compile and upload the contract code to a local node to experiment without paying gas fees. Later however, we will use the contract already deployed on the mainnet.
# Be careful as the code will use the abi of the compiled contract, which will be different from the abi of the deployed contract if you make changes to it.
contractContent = """
//SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8;

pragma experimental ABIEncoderV2;

interface IUniswapV2Pair {
    function token0() external view returns (address);
    function token1() external view returns (address);
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

// Batch query contract
contract UniswapFlashQuery {
    function getReservesByPairs(IUniswapV2Pair[] calldata _pairs) external view returns (uint256[3][] memory) {
        uint256[3][] memory result = new uint256[3][](_pairs.length);
        for (uint i = 0; i < _pairs.length; i++) {
            (result[i][0], result[i][1], result[i][2]) = _pairs[i].getReserves();
        }
        return result;
    }
    function getReservesByPairsYul(IUniswapV2Pair[] calldata _pairs) external view returns (bytes32[] memory) {
        bytes32[] memory result = new bytes32[](_pairs.length * 3);

        assembly {
            let size := 0x60 // Size of the return data (reserve0, reserve1, blockTimestampLast)
            let callData := mload(0x40) // Allocate memory for the function selector
            mstore(callData, 0x0902f1ac00000000000000000000000000000000000000000000000000000000) // 4-byte function selector of the getReserves() function
            
            // Update the free memory pointer
            mstore(0x40, add(callData, 0x04))
            
            // let pairsCount := shr(0xe0, calldataload(sub(_pairs.offset, 0x20))) // Get the length of the _pairs array
            let pairsCount := _pairs.length

            for { let i := 0 } lt(i, pairsCount) { i := add(i, 1) } {
                // Load the pair address from the calldata
                let pair := calldataload(add(_pairs.offset, mul(i, 0x20)))
                    
                // Call the getReserves() function with preallocated memory for function selector
                let success := staticcall(gas(), pair, callData, 0x04, add(add(result, 0x20),mul(i, size)), size)
                if iszero(success) {
                    revert(0x00, 0x00)
                }
            }

            // Update the free memory pointer
            mstore(0x40, add(mload(0x40), mul(pairsCount, size)))
        }

        return result;
    }
}
"""

# %%
import solcx
version = "0.8.0"
filename = "UniswapFlashQuery.sol"
Output = "ir"

compiled_sol = solcx.compile_standard(
    {
        "language": "Solidity",
        "sources": {filename: {"content": contractContent}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap",Output]}
            }
        },
    },
    solc_version=version,
)

name = filename.split('.')[0]
res_bytecode = compiled_sol["contracts"][filename][name]["evm"]["bytecode"]["object"]
queryAbi = compiled_sol["contracts"][filename][name]["abi"]
# print(compiled_sol["contracts"][filename][name][Output])

# Export the bytecode
print(f"Bytecode: {res_bytecode[:100]}...")

# %%
# Upload the bytecode to the blockchain
def uploadContract(addr, privateKey, bytecode, abi, provider, chainId=1, gasPrice=50*10**9): 
    """Deploy the provided bytecode to the blockchain"""

    print(f"Uploading smart contract from addr: {addr[:8]}...")
    #convert this into a ethereum contract object
    _contract = provider.eth.contract(abi=abi, bytecode=bytecode)
    #Get the nonce
    nonce = provider.eth.get_transaction_count(addr)
    #Define tx data
    txdata = {"chainId": chainId, "gas": 5000000, "gasPrice": gasPrice, "nonce": nonce}
    #Build Transaction
    transaction = _contract.constructor().build_transaction(txdata)
    #Sign the transaction
    signed = provider.eth.account.sign_transaction(transaction, private_key=privateKey)
    #Send the transaction
    tx_hash = provider.eth.send_raw_transaction(signed.rawTransaction)

    #Check for receipt
    receipt = provider.eth.wait_for_transaction_receipt(tx_hash)
    print(f'Transaction status: {receipt["status"]}')
    print(f'Gas used by Tx: {receipt["gasUsed"]}')
    print(f'Contract uploaded at {receipt.contractAddress}')
    contract_address = receipt.contractAddress
    full_contract = provider.eth.contract(address=contract_address,abi=abi)

    return (full_contract, contract_address)

# Anvil
ACC_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ACC_ADDR = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

# # Ganache
# ACC_PK = "0x316d944ace887053df5243fce6fd7f9cb2e3d50e9446204647abec1afc480ada"
# ACC_ADDR = "0x69AEFc283fA06c713EBfa2DeE98A0D9826BF29BC"

#
# res_contract, queryContractAddress = uploadContract(ACC_ADDR, ACC_PK, res_bytecode, queryAbi, w3local)
# Address of the contract deployed by the author
queryContractAddress = "0x6c618c74235c70DF9F6AD47c6b5E9c8D3876432B"

# %%
# This code splits the request into chunks that are sent concurrently to the node.
import asyncio
from web3 import AsyncHTTPProvider
from web3.eth import AsyncEth
import time
# If you test this code in a Jupyter notebook, sligh modifications are needed like nest_asyncio.apply() (google for more info)
# [...]

# Create a function that takes a list of pair data, and returns a list of reserves for each pair
async def getReservesAsync(pairs, chunkSize=1000):
    # Create an async web3 provider instance
    w3Async = Web3(AsyncHTTPProvider(NODE_URI), modules={'eth': (AsyncEth)})

    # Create contract object
    queryContract = w3Async.eth.contract(address=queryContractAddress, abi=queryAbi)

    # Create a list of chunks of pair addresses
    chunks = [[pair["pair"] for pair in pairs[i:i + chunkSize]] for i in range(0, len(pairs), chunkSize)]

    # Gather all the async tasks
    tasks = [queryContract.functions.getReservesByPairs(pairs).call() for pairs in chunks]

    # Run the tasks in parallel
    results = await asyncio.gather(*tasks)

    # Flatten the results
    results = [item for sublist in results for item in sublist]
    return results

# Call the function
t0 = time.time()
reserves = asyncio.get_event_loop().run_until_complete(getReservesAsync(pairDataList))
print(f"Time taken: {time.time() - t0} seconds. Fetched {len(reserves)} reserves.")

# %%
# This code sends the request chunks to multiple nodes in parallel.

# Define a list of node URIs
NODE_URIS = [
    # Infura nodes
    "https://mainnet.infura.io/v3/<YOUR_INFURA_ID>",
    "https://mainnet.infura.io/v3/<YOUR_INFURA_ID>",
    "https://mainnet.infura.io/v3/<YOUR_INFURA_ID>",
    "https://mainnet.infura.io/v3/<YOUR_INFURA_ID>",
    "https://mainnet.infura.io/v3/<YOUR_INFURA_ID>",
    "https://mainnet.infura.io/v3/<YOUR_INFURA_ID>"
]
providerList = [Web3(AsyncHTTPProvider(uri), modules={'eth': (AsyncEth)}) for uri in NODE_URIS]

async def getReservesParallel(pairs, providers, chunkSize=1000):
    # Create the contract objects
    contracts = [provider.eth.contract(address=queryContractAddress, abi=queryAbi) for provider in providers]

    # Create a list of chunks of pair addresses
    chunks = [[pair["pair"] for pair in pairs[i:i + chunkSize]] for i in range(0, len(pairs), chunkSize)]

    # Assign each chunk to a provider in a round-robin fashion
    tasks = [contracts[i % len(contracts)].functions.getReservesByPairs(pairs).call() for i, pairs in enumerate(chunks)]

    # Run the tasks in parallel
    results = await asyncio.gather(*tasks)
    
    # Flatten the results
    results = [item for sublist in results for item in sublist]

    return results

# Call the function
t0 = time.time()
reserves = asyncio.get_event_loop().run_until_complete(getReservesParallel(pairDataList, providerList))
print(f"Time taken: {time.time() - t0} seconds. Fetched {len(reserves)} results")
