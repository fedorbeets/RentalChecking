from web3 import Web3, HTTPProvider
from solc import compile_files
from math import floor
import eth_utils

def examine_trans_logs(transaction_addr):
    print("Transaction logs:")
    # port 8545 for geth
    # port 7545 for ganache/testrpc - simulated ethereum blockchain
    web3 = Web3(HTTPProvider('http://localhost:7545'))

    # Transaction to be examined
    # You must change this to examine a different transaction
    # One entry in the 'logs' array per event
    # multiple uint's are encoded as follows: discard the first 2 hex chars (the 0x), then 64 hex chars consequetively per uint.
    # decode: web3.toInt(hexstr=log_entry0[2:66]
    trans_receipt = web3.eth.getTransactionReceipt(transaction_addr)
    trans = web3.eth.getTransaction(transaction_addr)
    input_bits = trans['input']
    zero_bytes = 0
    non_zero_bytes = 0
    for i in range(2, len(trans['input']), 8):
        if input_bits[i:i+8] == '00000000':
            zero_bytes += 1
        else:
            non_zero_bytes += 1
    print("Input zero bytes: ", zero_bytes)
    print("Input non-zero bytes: ", non_zero_bytes)
    print(" Success:   ", trans_receipt['status'])
    print(" Gas usage: ", trans_receipt['cumulativeGasUsed'])
    print(trans)

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
        elif (lengthy - 2) / 64 % 2 == 0:  # Points in G1
            print(" G1 Point", x)
            for j in range(floor((lengthy - 2) / 64)):
                number = web3.toInt(hexstr=data[2 + (64 * j):2 + (64 * (j + 1))])
                print("       uint", j, ": ", number)
        else:  # don't know data type, just print bytes
            print(" data: ", trans_receipt['logs'][x]['data'])


# returns the gas usage of a transaction
def gas_usage(transaction_addr, web3):
    trans_receipt = web3.eth.getTransactionReceipt(transaction_addr)
    return trans_receipt['cumulativeGasUsed']

# Code not to be called upon import
if __name__ == "__main__":
    examine_trans_logs(0x772c58a7393d821786792be884dbb50a78fd5dca10d84d60ede35a96ec87f70b)
