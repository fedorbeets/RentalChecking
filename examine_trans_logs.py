from web3 import Web3, HTTPProvider
from math import floor
from deploy_contract import deploy_contract, URL

STEPSIZE = 64  # 32 bytes


def examine_trans_logs(trans_hash):
    print("Transaction logs:")
    web3 = Web3(HTTPProvider(URL))

    # Transaction to be examined
    # You must change this to examine a different transaction
    # One entry in the 'logs' array per event
    # multiple uint's are encoded as follows: discard the first 2 hex chars (the 0x),
    # then 64 hex chars consequetively per uint.
    # decode: web3.toInt(hexstr=log_entry0[2:66]
    trans_receipt = web3.eth.getTransactionReceipt(trans_hash)

    zeros, non_zeros, zero_h, non_zero_h = zeros_transaction(trans_hash, web3)

    print("Input zero bytes: ", zeros)
    print("Input non-zero bytes: ", non_zeros)
    print("Input zero bytes header: ", zero_h)
    print("Input non-zero bytes header: ", non_zero_h)
    print(" Success:   ", trans_receipt['status'])
    print(" Gas usage: ", trans_receipt['cumulativeGasUsed'])
    print(web3.eth.getTransaction(trans_hash))

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
def gas_usage(trans_hash, web3):
    trans_receipt = web3.eth.getTransactionReceipt(trans_hash)
    return trans_receipt['cumulativeGasUsed']


# returns the gas usage as if the transaction had no zero bytes
# ignores zero bytes in function selector or pointers to data location or how long the data is
def max_gas_usage(trans_hash, web3):
    trans_receipt = web3.eth.getTransactionReceipt(trans_hash)
    trans = web3.eth.getTransaction(trans_hash)
    zero_h, non_zero_h, zero_cont, non_zero_cont, store_version = zeros_transaction(trans_hash, web3)
    normal_gas = trans_receipt['cumulativeGasUsed']

    # zero byte costs 4 gas/byte to input
    # non-zero byte costs 68 gas/byte to input
    # difference in cost between zero and non-zero byte for input is 64 gas.
    gas_diff_zero = 68 - 4

    # expect 4 non-zero bytes in function selector, common to both headers
    # expect 2 non-zero bytes per parameter (in the length offsets). 2 parameters for store version, 6 for non_store.
    # established through running transactions of different token lengths and looking at average bytes in header
    if store_version:
        difference = 6 - non_zero_h
    else:
        difference = difference = 14 - non_zero_h
    header_adjustment = difference * gas_diff_zero

    return normal_gas + (zero_cont * gas_diff_zero) + header_adjustment


# returns the number of zero bytes, non-zero bytes in the data.
def count_bytes(data):
    zeros = 0
    for i in range(0, len(data), 2):
        byte = data[i:i + 2]
        if byte == "00":
            zeros += 1
    return zeros, (len(data) / 2) - zeros


# returns the number of zero bytes, non-zero bytes for the header and the points of a test
# also returns if store version of contract or non-store
def zeros_transaction(trans_hash, web3):
    trans = web3.eth.getTransaction(trans_hash)

    data = trans['input']
    # strip off 0x
    data = data[2:len(data)]
    tots_zero, tots_non_zero = count_bytes(data)
    function_selector = data[0:8]
    data = data[8:]
    header, rest, store_version = split_header(data)

    zero_fun, non_zero_fun = count_bytes(function_selector)
    zero_h, non_zero_h = count_bytes(header)
    zero_h += zero_fun
    non_zero_h += non_zero_fun
    zero_cont, non_zero_cont = count_bytes(rest)

    assert zero_h + zero_cont == tots_zero
    assert non_zero_h + non_zero_cont == tots_non_zero
    return zero_h, non_zero_h, zero_cont, non_zero_cont, store_version


# takes equality_test transaction that has been stripped upto including function selector
# returns the data split into a header part and a body part. The body part containing the points and length indicators
def split_header(data):
    # guess if store or non-store contract
    store = store_version(data)

    if not store_version:
        header = data[0: 6 * STEPSIZE]
        rest = data[6 * STEPSIZE:]
    if store_version:
        header = data[0: 2 * STEPSIZE]
        rest = data[2 * STEPSIZE:]
    return header, rest, store


# takes equality_test transaction that has been stripped upto including function selector
# returns whether the token was already stored or is in input data
def store_version(data):
    # guess if normal transaction or one where token is stored
    chunk2 = data[2 * STEPSIZE: 3 * STEPSIZE]
    chunk2int = int(chunk2, 16)
    store = False
    # if store version then only 2 arrays of uints, and the third chunk should be a length indicator
    # a length indicator is just the TokenLength*2+1. If it's still a data offset then it's always divisble by 32
    # thus length indicator is uneven, and data offset is even
    if chunk2int % 2 == 1:
        store = True
    return store


# takes equality_test transaction that has been stripped upto including function selector
def token_length(trans_hash, web3):
    trans = web3.eth.getTransaction(trans_hash)

    data = trans['input']
    # strip off 0x
    data = data[2:len(data)]
    tots_zero, tots_non_zero = count_bytes(data)
    function_selector = data[0:8]
    data = data[8:]
    store = store_version(data)
    print(store)
    if store:
        chunk2 = data[2 * STEPSIZE: 3 * STEPSIZE]
        chunk2int = int(chunk2, 16)
        token_len = (chunk2int-1) // 2
    else:
        chunk6 = data[6 * STEPSIZE: 7 * STEPSIZE]
        chunk6int = int(chunk6, 16)
        token_len = (chunk6int-1) // 2
    return token_len


# Code not to be called upon import
if __name__ == "__main__":
    # examine_trans_logs(0x2f2719bebc83f8f49630f189e10a09fe3a5224cb4c0b87f7c051adcdd1b606bf)
    web3 = Web3(HTTPProvider(URL))
    trans_hash = "0xfb4aaf60ce3421dc447111dfadc9569fb42bfd2cc78c1e5a3a14cc56f7731205"
    print(token_length(trans_hash, web3))
