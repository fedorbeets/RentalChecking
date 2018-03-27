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


def compare_opcodes(one_hash, two_hash, three_hash, four_hash):
    ops1 = get_json(one_hash)['result']['structLogs']
    ops2 = get_json(two_hash)['result']['structLogs']
    ops3 = get_json(three_hash)['result']['structLogs']
    ops4 = get_json(four_hash)['result']['structLogs']

    #cost_of_transaction(one_hash)
    #cost_of_transaction(two_hash)
    #cost_of_transaction(three_hash)
    #cost_of_transaction(four_hash)
    gasses1, freq1 = analyse_opcodes(ops1)
    gasses2, freq2 = analyse_opcodes(ops2)
    gasses3, freq3 = analyse_opcodes(ops3)
    gasses4, freq4 = analyse_opcodes(ops4)

    subtracted1 = compare_two_ops(gasses1, gasses2)

    subtracted2 = compare_two_ops(gasses3, gasses4)

    diff_substractions = compare_two_ops(subtracted1, subtracted2)

    for k, v in sorted(diff_substractions.items(), key=itemgetter(1), reverse=True):
        print('{:>12} {}'.format(k, v))
    #print("diff between 2 and 3")
    #for ke, ve in sorted(freq1.items(), key=itemgetter(1), reverse=True):
    #    print('{:>12} {}'.format(ke, ve))


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

# load from geth rpc api
twelve = "0x46659bd44922e6d35f3cfe9e8fa2d8067f1328520c7a13c479f1c7cf05851d1e"
eleven = "0xee0358c6f0495da2ea700c0b227660237dc08c01cc9ff6b861670484c77df00e"

nine = "0xeb5e781dc6c77fb3c5b8a77d6c4d696681b701118afb97f4fb5c3d8a8fd98160"
eight = "0x6eb50163480b592a1ed266511510a5f15ca88a0c8ab928b68bca43f56921ef61"
seven = "0x0e8a371fb8c8df42fdb9413040115b9bbd58750bd01c7ba7c15f0219a5694eac"
six = "0xbfc2f9a6056208770264497194c5cccd4c086f5e1e8a2efbb659208671c0ad75"
five = "0xf58d82aaef2519e05b668cfdca3cc5e19b416f59e6d588c59fc3ec4eb519d989"
four = "0x227e0737d01ec1d1db7273550b1e84b8ea2573703fa3d78804f22edab2f69777"
three = "0x0a7eb1c6b4f3558a80aa5591f79f90ef7537e80de7d3ff30bc0e3a4cff7bf915"
two = "0xbe22216a9e21156ff9943cde7647592f5f60bd4bd08808ebc0ca7b953ce0b074"
one = "0x6ac9a4c09cbcd99581c4726e40dc1bfe40cb5cb364cef13687160adcb0cef4d9"

opcodes = get_json(three)['result']['structLogs']
#print(len(opcodes))
#print(opcodes[1487])
#print(opcodes[5]['memory'])
# analyse_opcodes(opcodes)
#compare_opcodes(three, four, five, six)
# analyse_opcodes(opcodes)

for index, call in enumerate(opcodes):
    if 970 < index < 990:
        print_call(call)
    #if call['op'] == 'CODECOPY':
    #    print_call(call)
    #    print(index)
