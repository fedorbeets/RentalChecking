from web3 import Web3, HTTPProvider
from solc import compile_files
from math import floor
import eth_utils

def examineTransLogs(contractAddr, transaction_addr):
    print("Transaction logs:")
    # port 8545 for geth
    # port 7545 for ganache/testrpc - simulated ethereum blockchain
    web3 = Web3(HTTPProvider('http://localhost:7545'))

    # addresses have to be in EIP-55 checksum
    contractAddr = eth_utils.to_checksum_address(contractAddr)

    # need contract code to know what methods can be addressed in contract on blockchain
    compiled = compile_files(["solidity_test_pairing_code.sol"], "--optimized")
    compiledCode = compiled['solidity_test_pairing_code.sol:pairing_check']
    contract_instance = web3.eth.contract(contractAddr, abi=compiledCode['abi'])

    # Transaction to be examined
    # You must change this to examine a different transaction

    # One entry in the 'logs' array per event
    # multiple uint's are encoded as follows: discard the first 2 hex chars (the 0x), then 64 hex chars consequetively per uint.
    # decode: web3.toInt(hexstr=log_entry0[2:66]
    trans_receipt = web3.eth.getTransactionReceipt(transaction_addr)
    print(" Success: ", trans_receipt['status'])
    print(" Gas used: ", trans_receipt['cumulativeGasUsed'])

    for x in range(len(trans_receipt['logs'])):
        data = trans_receipt['logs'][x]['data']
        lengthy = len(data)
        # assume an event only either prints G1 or G2 points
        # check for G2 points, do this first otherwise both G1 and G2 points match
        if (lengthy - 2) / 64 % 4 == 0:
            print(" G2 point", x)
            for j in range(floor((lengthy - 2) / 64)):
                number = web3.toInt(hexstr=data[2 + (64 * j):2 + (64 * (j + 1))])
                print("        uint", j, ": ", number)
        elif (lengthy - 2) / 64 % 2 == 0:  # check for G1 points
            print(" G1 Point", x)
            for j in range(floor((lengthy - 2) / 64)):
                number = web3.toInt(hexstr=data[2 + (64 * j):2 + (64 * (j + 1))])
                print("       uint", j, ": ", number)
        else:  # don't know data type, just print bytes
            print(" data: ", trans_receipt['logs'][x]['data'])

# Code not to be called upon import
if __name__=="__main__":
    examineTransLogs('0x8CdaF0CD259887258Bc13a92C0a6dA92698644C0', 0xecb527d25b7fea92c37100a047c0070838c047934381656455bc597c46ebb02a)
