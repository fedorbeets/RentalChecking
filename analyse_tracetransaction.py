import json
import requests
import deploy_contract
import examine_trans_logs
from web3 import Web3, HTTPProvider





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


actual_gas = json_dict['result']['gas']
opcodes = json_dict['result']['structLogs']

print("Real Gas cost: ", "{:,}".format(actual_gas))
web3 = Web3(HTTPProvider(deploy_contract.URL))
max_gas = examine_trans_logs.max_gas_usage(trans_hash, web3)
print("Maxed gas use:       ", "{:,}".format(max_gas))
adjustment = max_gas - actual_gas
zeros, non_zeros, zero_h, non_zero_h = examine_trans_logs.zero_bytes_trans(trans_hash, web3)
inputs_gas_cost = zeros * 4 + non_zeros * 68 + zero_h * 4 + non_zero_h * 68
maxed_input_cost = inputs_gas_cost + adjustment

# we analyse gas costs in the case where there would be no zero bytes.
# TODO; redo zero counting code
data_input = web3.eth.getTransaction(trans_hash)['input']
data_input = data_input[2:len(data_input)]  # strip of 0x, which is no part of cost
zeros, non_zeros = examine_trans_logs.count_zero_bytes(data_input, 64)
print("My zeros, non zeros: ", zeros, " ", non_zeros)
input_cost = zeros * 4 + non_zeros * 68
print("My Input gas cost: ", input_cost)
git_zeros = count_zero_bytes(data_input)
git_non_zeros = count_non_zero_bytes(data_input)
print("Git zeros, non zeros: ", git_zeros, " ", git_non_zeros)
git_cost = git_zeros * 4 + git_non_zeros * 68


cost_trans = 21000
sum_gasses = 0
print("Gas accounted before opcodes: " "{:,}".format(sum_gasses))
for index, call in enumerate(opcodes):
    if index == 0:
        gas_to_opcodes = 5000000 - call['gas'] + adjustment
        print("Gas used before opcodes: ", "{:,}".format(gas_to_opcodes))
    if index != len(opcodes) - 1:
        gas_usage = call['gas'] - opcodes[index + 1]['gas']
        sum_gasses += gas_usage
    else:  # last call. Assume gasCost is correct.
        sum_gasses += call['gasCost']

print("Gass costs summed:    ", "{:,}".format(sum_gasses + cost_trans + maxed_input_cost))
print("Non adjusted gas cost: ", "{:,}".format(cost_trans + git_cost + sum_gasses))
# 68 over limit gas.
# Guessing this comes from 0x
# gas use as input - final used is correct.
# print("{:,}".format(5000000-3838169+adjustment))
