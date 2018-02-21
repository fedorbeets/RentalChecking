import random
import EqualityTest
import py_ecc.optimized_bn128 as fast_pairing
import time
from web3 import Web3, HTTPProvider
from solc import compile_files
from DeployContract import deploy_contract
from TestNormalSolidityContract import split_g1_points,split_g2_points
from ExamineTransLogs import gas_usage
from statistics import mean
from math import floor

for n in [1, 2, 3, 4, 5, 10, 15, 20]:
    # generate token
    # Generate values from EqualityTest
    master_keys, check_keys = EqualityTest.setup(n)
    test_token = EqualityTest.gen_token(master_keys, [3 for _ in range(n)], n)

    listG2 = []

    for x in range(n):
        listG2.append(test_token[0][x]['u_multiplied'])
        assert fast_pairing.is_on_curve(test_token[0][x]['u_multiplied'], fast_pairing.b2)

    for x in range(n):
        listG2.append(test_token[0][x]['alpha_mul_g2_mul_prp'])
        assert fast_pairing.is_on_curve(test_token[0][x]['alpha_mul_g2_mul_prp'], fast_pairing.b2)

    listG2.append(test_token[1])

    listG2 = list(map(fast_pairing.normalize, listG2))
    g2_x_i, g2_x_r, g2_y_i, g2_y_r = split_g2_points(listG2)

    args = [g2_x_i, g2_x_r, g2_y_i, g2_y_r]
    # Deploy contract
    # port 8545 for geth
    # port 7545 for ganache/testrpc - simulated ethereum blockchain
    web3 = Web3(HTTPProvider('http://localhost:7545'))
    contract_file = "store_token_equality_test.sol"
    contract_name = "store_token_equality_test.sol:pairing_check_token_stored"

    # todo: contract deployment cost is not constant but have not averaged it over multiple runs yet
    (contractAddr, contract_trans) = deploy_contract(contract_file,
                                   contract_name, web3, args, True)
    gas_use_deploy = gas_usage(contract_trans, web3)
    print("Gas used to deploy n=", n, "contract: ", gas_use_deploy)

    compiled = compile_files([contract_file], "--optimized")
    compiledCode = compiled[contract_name]
    contract_instance = web3.eth.contract(contractAddr, abi=compiledCode['abi'])


    # test contract gas usage
    repetitions = 5
    gas_used = []
    for i in range(repetitions):
        # generate g1 points
        rand = random.SystemRandom()
        identifier = rand.randint(1, fast_pairing.curve_order)
        checks = [EqualityTest.encrypt(check_keys[x], identifier, 3) for x in range(n)]
        listG1 = []

        for x in range(n):
            listG1.append(checks[x]['g1_mul_prp_add_ident_hash'])

        for x in range(n):
            listG1.append(checks[x]['r_x_mul'])

        listG1.append(checks[0]['hash_ident'])

        # Invert points
        for x in range(len(listG1)):
            if x >= (len(listG1) // 2):
                listG1[x] = fast_pairing.neg(listG1[x])

        listG1 = list(map(fast_pairing.normalize, listG1))
        g1points_x, g1points_y = split_g1_points(listG1)
        tx_hash = contract_instance.transact({'from': web3.eth.accounts[0], 'gas': 4000000}).test_equality(
            g1points_x, g1points_y)

        while web3.eth.getTransaction(tx_hash)['blockNumber'] is None:
            time.sleep(1)
        transaction_addr = web3.eth.getTransaction(tx_hash)['hash']
        gas_used.append(gas_usage(transaction_addr.hex(), web3))

    print("Average gas usage n=", n, " is: ", floor(mean(gas_used)))
