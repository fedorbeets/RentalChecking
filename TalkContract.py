from web3 import Web3, HTTPProvider, IPCProvider
from solc import compile_files
from web3.contract import ConciseContract
import time
import eth_utils
# There is no cost or delay for reading the state of the blockchain, as this is held on our node
web3 = Web3(HTTPProvider('http://localhost:8545'))


# addresses have to be in EIP-55 checksum
contractAddr = eth_utils.to_checksum_address('0x7a1595e44b26f86e85d91a9b109c99577fce40a5')
# old contract without string argument: 0x788d82eaab8e7e591c9f8d6d52dff56959f9ca97



# need contract code to know what methods can be addressed in contract on blockchain
compiled = compile_files(["solidity_test_pairing_code.sol"], "--optimized")
compiledCode = compiled['solidity_test_pairing_code.sol:pairing_check']
contract_instance = web3.eth.contract(contractAddr, abi=compiledCode['abi'])

# make transaction
tx_hash = contract_instance.transact({'from': web3.eth.accounts[0], 'gas': 3000000}).testPairing("notUsed")

# block until mined
while web3.eth.getTransaction(tx_hash)['blockNumber'] is None:
    time.sleep(1)

transaction_addr = web3.eth.getTransaction(tx_hash)['hash']



# contract_instance.testPairing('dummy', transact={'from': web3.eth.accounts[0]})
# ye olde transaction
# transaction_addr = '0x16d5cf5a3657e4ca131e120d27ba412912d7b6828e5f68e1c06d319cfbc9e8ad'

#transaction_addr = '0x3ced7fd1fffe4064b0ee68acdd9e988b5a4b0b902e3b8ec687c1762bc856aff9'

log_entry0 = web3.eth.getTransactionReceipt(transaction_addr)['logs'][0]['data']
log_entry1 = web3.eth.getTransactionReceipt(transaction_addr)['logs'][1]['data']
log_entry2 = web3.eth.getTransactionReceipt(transaction_addr)['logs'][2]['data']
print("0: ", log_entry0)  # points event: uint, uint
# should contain: Pairing.mul(point1, 10); or "args":
#			"4444740815889402603535294170722302758225367627362056425101568584910268024244",
#			"10537263096529483164618820017164668921386457028564663708352735080900270541420"
print("1: ", log_entry1)  # pointsG2 event: uint, uint, uint, uint
print("2: ", log_entry2)  # result event: bool

first_uint = log_entry0[2:66]
print(first_uint)
second_uint = log_entry0[66:130]
print(second_uint)
print(web3.toInt(hexstr=first_uint))
print(web3.toInt(hexstr=second_uint))
# event_abi = compiledCode._find_matching_event_abi('Result')
# event_abi = [m for m in compiledCode['abi'] if m['name'] == 'Result'][0]



# Need to not use call, but send a transaction
