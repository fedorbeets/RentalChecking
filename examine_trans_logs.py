from web3 import Web3, HTTPProvider
from math import floor


def examine_trans_logs(transaction_addr, store_token):
    print("Transaction logs:")
    # port 8545 for geth
    # port 7545 for ganache/testrpc - simulated ethereum blockchain
    web3 = Web3(HTTPProvider('http://localhost:7545'))

    # Transaction to be examined
    # You must change this to examine a different transaction
    # One entry in the 'logs' array per event
    # multiple uint's are encoded as follows: discard the first 2 hex chars (the 0x),
    # then 64 hex chars consequetively per uint.
    # decode: web3.toInt(hexstr=log_entry0[2:66]
    trans_receipt = web3.eth.getTransactionReceipt(transaction_addr)
    trans = web3.eth.getTransaction(transaction_addr)

    if store_token:
        zeros, non_zeros = zero_bytes_store(trans['input'])
    else:
        zeros, non_zeros = zero_bytes_normal(trans['input'])

    print("Input zero bytes: ", zeros)
    print("Input non-zero bytes: ", non_zeros)
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
def gas_usage(trans_addr, web3):
    trans_receipt = web3.eth.getTransactionReceipt(trans_addr)
    return trans_receipt['cumulativeGasUsed']


# returns the gas usage as if the transaction had no zero bytes
def max_gas_usage(trans_addr, web3):
    trans_receipt = web3.eth.getTransactionReceipt(trans_addr)
    trans = web3.eth.getTransaction(trans_addr)
    zeros, non_zeros = zero_bytes_normal(trans['input'])
    normal_gas = trans_receipt['cumulativeGasUsed']
    # zero byte costs 4 gas/byte to input
    # non-zero byte costs 68 gas/byte to input
    # difference in cost between zero and non-zero byte for input is 64 gas.
    return normal_gas + (zeros * 64)


# returns the number of zero bytes in the uint number input data, for the normal contract that sends the token each time
# ignores zero bytes in function selector or pointers to data location or how long the data is
def zero_bytes_normal(trans_input):
    # strip of 0x and function selector
    rest = trans_input[10:len(trans_input)]
    stepsize = 64  # 32 bytes

    # ignore data location indicators
    rest = rest[6 * stepsize: len(rest)]

    return count_zero_bytes(rest, stepsize)


# like zero_bytes_normal but then for transactions where token is stored
def zero_bytes_store(trans_input):
    # strip of 0x and function selector
    rest = trans_input[10:len(trans_input)]
    stepsize = 64  # 32 bytes
    # strip off data location indicators
    rest = rest[2 * stepsize: len(rest)]

    return count_zero_bytes(rest, stepsize)


def count_zero_bytes(argument_hex, stepsize):
    zeros_b = 0
    non_zero_b = 0
    # length of byte array in elements
    length_indicator = argument_hex[0:stepsize]
    for i in range(0, len(argument_hex) // stepsize):
        chunk = argument_hex[i * stepsize:(i + 1) * stepsize]
        if chunk == length_indicator:
            continue
        else:
            # check for 0 bytes, or 00 strings
            for j in range(0, 64, 2):
                if chunk[j:j + 2] == '00':
                    zeros_b += 1
                else:
                    non_zero_b += 1
    return zeros_b, non_zero_b


# Code not to be called upon import
if __name__ == "__main__":
    examine_trans_logs(0xc0319b577eb21ee30a70ce6e91a4293e485d78630b6e1420500f1e8fe2297280)
