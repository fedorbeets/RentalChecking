import sys, os, time
from solc import compile_source, compile_files, link_code
from web3 import Web3, HTTPProvider, IPCProvider
from web3.contract import ConciseContract
#from eth_utils import add_0x_prefix



# Basic contract compiling process.
#   Requires that the creating account be unlocked.
#   Note that by default, the account will only be unlocked for 5 minutes (300s).
#   Specify a different duration in the geth personal.unlockAccount('acct','passwd',300) call, or 0 for no limit

#compiled = compile_source(source)  # if you have a source code in text
compiled = compile_files(["solidity_test_pairing_code.sol"], "--optimized")   # compile from file
compiledCode = compiled['solidity_test_pairing_code.sol:pairing_check']['bin']

# Initiate connection to ethereum node
#   Requires a node running with an RPC connection available at port 8545
web3 = Web3(HTTPProvider('http://localhost:7545'))


# Instantiate and deploy contract
contract = web3.eth.contract(abi=compiled['solidity_test_pairing_code.sol:pairing_check']['abi'], bytecode=compiledCode)


# Get transaction hash from deployed contract
tx_hash = contract.deploy(transaction={'from': web3.eth.accounts[0], 'gas': 3000000})

print("Transaction hash: ", tx_hash.hex())

# Get tx receipt to get contract address, wait till block is mined
while web3.eth.getTransactionReceipt(tx_hash) is None:
    time.sleep(1)

tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
CONTRACT_ADDRESS = tx_receipt['contractAddress']

print("Contract address: ", CONTRACT_ADDRESS)
