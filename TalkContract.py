from ethjsonrpc import EthJsonRpc

# There is no cost or delay for reading the state of the blockchain, as this is held on our node
c = EthJsonRpc('127.0.0.1', 8545)

contractAddr = '0x788d82eaab8e7e591c9f8d6d52dff56959f9ca97'

results = c.call(contractAddr, 'testPairing()', [], ['string'])
print("The message reads: '"+results[0]+"'")