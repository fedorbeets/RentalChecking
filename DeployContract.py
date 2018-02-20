import sys, os, time
from solc import compile_source, compile_files, link_code
from web3 import Web3, HTTPProvider, IPCProvider
from web3.contract import ConciseContract


# Basic contract compiling process.
#   Requires that the creating account be unlocked.
#   Note that by default, the account will only be unlocked for 5 minutes (300s).
#   Specify a different duration in the geth personal.unlockAccount('acct','passwd',300) call, or 0 for no limit

#compiled = compile_source(source)  # if you have a source code in text
# --optimize-runs 20000 or 1 seems to do nothing
# contract_name should be in the file
# formatted like: file.sol , file.sol:name
def deploy_contract(file, contract_name, web3, args=None, verbose=True):
    compiled = compile_files([file], "--optimized ")  # compile from file
    compiledCode = compiled[contract_name]['bin']
    verboseprint = print if verbose else lambda *a, **k: None


    # Instantiate and deploy contract
    contract = web3.eth.contract(abi=compiled[contract_name]['abi'],
                                 bytecode=compiledCode)

    # Get transaction hash from deployed contract
    tx_hash = contract.deploy(transaction={'from': web3.eth.accounts[0], 'gas': 4000000}, args=args)
    verboseprint("Transaction hash: ", tx_hash.hex())


    # Get tx receipt to get contract address, wait till block is mined
    while web3.eth.getTransactionReceipt(tx_hash) is None:
        time.sleep(1)

    tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
    contract_address = tx_receipt['contractAddress']

    verboseprint("Contract address: ", contract_address)
    return contract_address, tx_hash.hex()


if __name__ == "__main__":
    web3 = Web3(HTTPProvider('http://localhost:8545'))
    deploy_contract("solidity_test_pairing_code.sol", 'solidity_test_pairing_code.sol:pairing_check', web3)
    # deploy_contract("store_token_equality_test.sol", "store_token_equality_test.sol:pairing_check_token_stored")
