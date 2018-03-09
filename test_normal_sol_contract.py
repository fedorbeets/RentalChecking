# slowPairing only uses X,Y points instead of X,Y,Z points, which we need here
import random
from statistics import mean

import py_ecc.bn128.bn128_pairing as slow_pairing
from py_ecc.bn128.bn128_pairing import FQ2, FQ
import py_ecc.optimized_bn128.optimized_pairing as fast_pairing
from web3 import Web3, HTTPProvider
from solc import compile_files
from math import floor
import time
from deploy_contract import deploy_contract
from examine_trans_logs import gas_usage, max_gas_usage
from conversion_utility import split_g2_points, split_g1_points
import equality_test

if __name__ == "__main__":
    # There is no cost or delay for reading the state of the blockchain, as this is held on our node
    # port 8545 for geth
    # port 7545 for ganache/testrpc - simulated ethereum blockchain
    web3 = Web3(HTTPProvider('http://localhost:7545'))

    contract_file = "solidity_test_pairing_code.sol"
    contract_name = "solidity_test_pairing_code.sol:pairing_check"

    (contractAddr, contract_trans) = deploy_contract(contract_file, contract_name, web3, verbose=False)
    print("Gas used to deploy contract: ", gas_usage(contract_trans, web3))
    # address no pairings: 0x2C2B9C9a4a25e24B174f26114e8926a9f2128FE4
    # address with pairing: 0xFB88dE099e13c3ED21F80a7a1E49f8CAEcF10df6

    # need contract code to know what methods can be addressed in contract on blockchain
    compiled = compile_files([contract_file], "--optimized")
    compiledCode = compiled[contract_name]
    contract_instance = web3.eth.contract(contractAddr, abi=compiledCode['abi'])

    verbose = False
    verbose_print = print if verbose else lambda *a, **k: None
    #  1, 2, 3, 4, 5, 10, 15, 20
    print("Number of checks, gas usage")
    for n in [1, 2, 3, 4, 5, 10, 15, 20]:
        # Generate values from EqualityTest
        master_keys, check_keys = equality_test.setup(n)
        rand = random.SystemRandom()
        token_accepts = [rand.randint(1, 30) for _ in range(n)]
        test_token = equality_test.gen_token(master_keys, token_accepts, n)

        identifier = 5
        checks = [equality_test.encrypt(check_keys[x], identifier, token_accepts[x]) for x in range(n)]
        listG1 = []
        listG2 = []

        for x in range(n):
            listG1.append(checks[x]['g1_mul_prp_add_ident_hash'])
            listG2.append(test_token[0][x]['u_multiplied'])
            assert fast_pairing.is_on_curve(test_token[0][x]['u_multiplied'], fast_pairing.b2)

        for x in range(n):
            listG1.append(checks[x]['r_x_mul'])
            listG2.append(test_token[0][x]['alpha_mul_g2_mul_prp'])
            assert fast_pairing.is_on_curve(test_token[0][x]['alpha_mul_g2_mul_prp'], fast_pairing.b2)

        listG1.append(checks[0]['hash_ident'])
        listG2.append(test_token[1])

        for x in range(len(listG1)):
            if x >= (len(listG1) // 2):
                listG1[x] = fast_pairing.neg(listG1[x])
        verbose_print("Created", (n * 2) + 1, "pairs of points")

        # solidity interface type conversion:
        # Convert points so they can be sent to blockchain
        listG1 = list(map(fast_pairing.normalize, listG1))
        listG2 = list(map(fast_pairing.normalize, listG2))

        g1points_x, g1points_y = split_g1_points(listG1)
        g2_x_i, g2_x_r, g2_y_i, g2_y_r = split_g2_points(listG2)

        # make transaction
        # method to be called comes after transact, as a python function call
        repetitions = 5
        gas_used = []
        gas_used_max = []
        for i in range(repetitions):
            verbose_print("Making transaction")
            tx_hash = contract_instance.transact({'from': web3.eth.accounts[0], 'gas': 5000000}).test_equality(
                g1points_x, g1points_y, g2_x_i, g2_x_r, g2_y_i, g2_y_r)

            # block until mined
            verbose_print("Waiting till transaction is mined")
            while web3.eth.getTransaction(tx_hash)['blockNumber'] is None:
                time.sleep(1)
            transaction_addr = web3.eth.getTransaction(tx_hash)['hash']
            verbose_print("Transaction address: ", transaction_addr.hex())
            # examine_trans_logs(contractAddr, transaction_addr.hex())
            gas_used.append(gas_usage(transaction_addr.hex(), web3))
            gas_used_max.append(max_gas_usage(transaction_addr.hex(), web3))
        print(n, " ,", floor(mean(gas_used)))
        print(n, " ,", floor(mean(gas_used_max)), "  maxed")

        if False:
            outputs = contract_instance.call({'from': web3.eth.accounts[0], 'gas': 4000000}).test_equality(
                g1points_x, g1points_y, g2_x_i, g2_x_r, g2_y_i, g2_y_r)
            print("Local sol call: ", outputs)

        # Do Pairing by pairing all points and then multiplying the results together
        if False:
            print("Pairing in python, total", len(g1points_x), "pairings")
            for x in range(len(g1points_x)):
                if x >= floor(len(g1points_x) / 2):  # negate second half of points/second part equation
                    g1_point = slow_pairing.neg((FQ(g1points_x[x]), FQ(g1points_y[x])))
                else:
                    g1_point = (FQ(g1points_x[x]), FQ(g1points_y[x]))
                g2_point = (FQ2([g2_x_r[x], g2_x_i[x]]), FQ2([g2_y_r[x], g2_y_i[x]]))
                pair = slow_pairing.pairing(g2_point, g1_point)
                try:  # make sure it's defined without starting with a slowPairing.FQ12.one()
                    pairing_total = pairing_total * pair
                except NameError:
                    pairing_total = pair
                print("Completed pairing ", x)
            print("Pairing tot py sum: ", pairing_total)
            pairing_total *= slow_pairing.FQ12.one()
