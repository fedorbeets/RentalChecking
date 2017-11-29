import sys, os, time
from solc import compile_source, compile_files, link_code
from ethjsonrpc import EthJsonRpc
from eth_utils import add_0x_prefix

#print("Using environment in "+sys.prefix)
#print("Python version "+sys.version)

# Initiate connection to ethereum node
#   Requires a node running with an RPC connection available at port 8545
c = EthJsonRpc('127.0.0.1', 8545)
print(c.web3_clientVersion())
print(c.eth_blockNumber())


'''source = """
pragma solidity ^0.4.2;

contract Example {

    string s="Hello World!";

    function set_s(string new_s) {
        s = new_s;
    }

    function get_s() returns (string) {
        return s;
    }
}"""'''

# Basic contract compiling process.
#   Requires that the creating account be unlocked.
#   Note that by default, the account will only be unlocked for 5 minutes (300s).
#   Specify a different duration in the geth personal.unlockAccount('acct','passwd',300) call, or 0 for no limit

#compiled = compile_source(source)
compiled = compile_files(["solidity_test_pairing_code.sol"], "--optimized")
# compiled = compile_files(['Solidity/ethjsonrpc_tutorial.sol'])  #Note: Use this to compile from a file
#print(compiled['solidity_test_pairing_code.sol:pairing_check'])
compiledCode = compiled['solidity_test_pairing_code.sol:pairing_check']['bin']
compiledCode = '0x'+compiledCode  # This is a hack which makes the system work

# Put the contract in the pool for mining, with a gas reward for processing
contractTx = c.create_contract(c.eth_coinbase(), add_0x_prefix(compiledCode), gas=3500000)
print("Contract transaction id is "+contractTx)

print("Waiting for the contract to be mined into the blockchain...")
while c.eth_getTransactionReceipt(contractTx) is None:
        time.sleep(1)

contractAddr = c.get_contract_address(contractTx)
print("Contract address is "+contractAddr)
