# Rental Checking

Python implementation to determine if 2 vectors are equal by using a conjunctive equality test.

We can translate rental requirements into one vector (token) and the actual properties of those requirements into a different vector (rule). Then we check the equality of the plaintext from the two encrypted vectors.
Now we can check if a rentee meets the requirements set out by a landlord, without the landlord learning the attributes of the rentee.

Math based largely on: Multi-client Predicate-only Encryption for Conjunctive Equality Tests by Kamp, Peter, Everts, Jonker, 2017.

The checking for equality happens on the Ethereum blockchain.
There are two versions of a contract for this included, a store version which stores the token upon creation and a flexible version which requires the inclusion of the token in every transaction.
These contracts have to be deployed, for which you preferably have a local instance of Geth or Ganache running your own Ethereum test network.
The test_x_sol_contract.py will run all of the contract deployment, token/check generation and testing on chain and report results.

examinetranslogs.py lets you look through transactions made to do testing, to get various properties for testing, debugging and performance evaluation.
analysetracetransaction.py also looks through an ethereum transaction to find which sources are using what amounts of gas, and compare this between different transactions.
The distribution analyser looks at the amount of '00' bytes relative to all other bytes in a large number of generated points on the elliptic curves, to see how frequent 0 bytes are.
 	

To run just the Setup, GenToken and EncryptCheck parts of algorithm and possibly an off-chain equality test, run the equalitytest class.
To run all of the contract deployment, and on-chain equality test run one of the testXsolcontract classes.
