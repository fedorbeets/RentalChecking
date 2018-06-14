import copy
import json
import requests
import deploy_contract
import examine_trans_logs
from operator import itemgetter
from collections import defaultdict
from web3 import Web3, HTTPProvider


def gas_cost_opcodes(opcodes):
    sum_gas = 0
    for index, call in enumerate(opcodes):
        sum_gas += gas_opcode(index, opcodes)
    return sum_gas


# returns the gas cost of a opcode
def gas_opcode(index, opcodes):
    if index != len(opcodes) - 1:
        return opcodes[index]['gas'] - opcodes[index + 1]['gas']
    else:
        return opcodes[index]['gasCost']


def analyse_opcodes(opcodes):
    gas_by_op = defaultdict(int)
    op_times = defaultdict(int)
    for index, call in enumerate(opcodes):
        gas_by_op[call['op']] += gas_opcode(index, opcodes)
        op_times[call['op']] += 1
        #if call['op'] == 'MSTORE' or call['op'] == 'CALLDATACOPY':

    return gas_by_op, op_times
    # for k, v in sorted(gas_by_op.items(), key=itemgetter(1), reverse=True):
    #    print('{:>12} {}'.format(k, v))


def get_json(trans_hash):
    url = deploy_contract.URL
    payload = {"id": 1, "method": "debug_traceTransaction",
               "params": [trans_hash, {"disableMemory": False, "disableStack": False}]}
    headers = {"Content-Type: application/json"}
    r = requests.get(url, json=payload)
    return r.json()


def cost_of_transaction(trans_hash):
    # load up a file
    # std_path = "transaction_output.json"
    # json_string = open(std_path, "r").read()
    # json_dict = json.loads(r.json())
    opcodes = get_json(trans_hash)['result']['structLogs']

    # print("Real Gas cost: ", "{:,}".format(actual_gas))
    web3 = Web3(HTTPProvider(deploy_contract.URL))
    max_gas = examine_trans_logs.max_gas_usage(trans_hash, web3)
    # print("Maxed gas use:      ", "{:,}".format(max_gas))
    actual_gas = get_json(trans_hash)['result']['gas']
    adjustment = max_gas - actual_gas  # how much did we compensate
    print("Max gas adjustment: ", adjustment)
    zeros, non_zeros, zero_h, non_zero_h, store_version = examine_trans_logs.zeros_transaction(trans_hash, web3)
    # cost of input data in gas. txdatazero + txdatanonzero from yellowpaper
    # adjusted as if there were no null_bytes
    inputs_gas_cost = zeros * 4 + non_zeros * 68 + zero_h * 4 + non_zero_h * 68 + adjustment

    # constant cost to create any transaction
    cost_trans = 21000
    sum_gasses = cost_trans + inputs_gas_cost + gas_cost_opcodes(opcodes)
    print("Gass costs summed:  ", "{:,}".format(sum_gasses))


# Takes four transaction hashes, and shows how much difference there is in their opcodes, beyond what is expected by linear increase.
def compare_opcodes(one_hash, two_hash, three_hash, four_hash):
    ops1 = get_json(one_hash)['result']['structLogs']
    ops2 = get_json(two_hash)['result']['structLogs']
    ops3 = get_json(three_hash)['result']['structLogs']
    ops4 = get_json(four_hash)['result']['structLogs']

    gasses1, freq1 = analyse_opcodes(ops1)
    gasses2, freq2 = analyse_opcodes(ops2)
    gasses3, freq3 = analyse_opcodes(ops3)
    gasses4, freq4 = analyse_opcodes(ops4)

    subtracted1 = compare_two_ops(gasses1, gasses2)

    subtracted2 = compare_two_ops(gasses3, gasses4)

    diff_substractions = compare_two_ops(subtracted1, subtracted2)

    for k, v in sorted(diff_substractions.items(), key=itemgetter(1), reverse=True):
        print('{:>12} {}'.format(k, v))


# returns how many more opcodes of particular types are in the second transaction than the first. (as dict)
def compare_two_ops(set_one, set_two):

    subtracted1 = copy.deepcopy(set_one)
    for val in subtracted1:
        subtracted1[val] -= set_two[val]
    return subtracted1


def print_call(call):
    print('op:{:>12} pc:{:>4} gasCost:{:>3}  memsize:{:>2}'.format(call['op'], call['pc'], call['gasCost'], len(call['memory'])))
    print("Stack: ", call['stack'])
    print("Memory: ", call['memory'])

# One suggested way is to run for token lenghts 1,2,3,4 and compare the differences between those transactions
four = "dummy"
three = "dummy"
two = "dummy"
one = "dummy"

compare_two_ops(one, two)
compare_opcodes(one, two, three, four)
# analyse_opcodes(get_json(one)['result']['structLogs'])
