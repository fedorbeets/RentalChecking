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
    if index != len(opcodes) -1:
        return opcodes[index]['gas'] - opcodes[index + 1]['gas']
    else:
        return opcodes[index]['gasCost']


def analyse_opcodes(opcodes):
    gas_by_op = defaultdict(int)
    op_times = defaultdict(int)
    for index, call in enumerate(opcodes):
        gas_by_op[call['op']] += gas_opcode(index, opcodes)
        op_times[call['op']] += 1

    for k, v in sorted(gas_by_op.items(), key=itemgetter(1), reverse=True):
        print('{:>12} {}'.format(k, v))

# load from geth rpc api
trans_hash = "0x2f2719bebc83f8f49630f189e10a09fe3a5224cb4c0b87f7c051adcdd1b606bf"
url = deploy_contract.URL
payload = {"id": 1, "method": "debug_traceTransaction",
           "params": [trans_hash, {"disableMemory": True, "disableStack": True}]}
headers = {"Content-Type: application/json"}
r = requests.get(url, json=payload)
json_dict = r.json()
# load up a file
# std_path = "transaction_output.json"
# json_string = open(std_path, "r").read()
# json_dict = json.loads(r.json())

opcodes = json_dict['result']['structLogs']

# print("Real Gas cost: ", "{:,}".format(actual_gas))
web3 = Web3(HTTPProvider(deploy_contract.URL))
max_gas = examine_trans_logs.max_gas_usage(trans_hash, web3)
print("Maxed gas use:      ", "{:,}".format(max_gas))
actual_gas = json_dict['result']['gas']
adjustment = max_gas - actual_gas  # how much did we compensate
zeros, non_zeros, zero_h, non_zero_h, store_version = examine_trans_logs.zeros_transaction(trans_hash, web3)
# cost of input data in gas. txdatazero + txdatanonzero from yellowpaper
# adjusted as if there were no null_bytes
inputs_gas_cost = zeros * 4 + non_zeros * 68 + zero_h * 4 + non_zero_h * 68 + adjustment

# constant cost to create any transaction
cost_trans = 21000
sum_gasses = cost_trans + inputs_gas_cost + gas_cost_opcodes(opcodes)

print("Gass costs summed:  ", "{:,}".format(sum_gasses ))

analyse_opcodes(opcodes)

