# slowPairing only uses X,Y points instead of X,Y,Z points, which we need here
import py_ecc.bn128.bn128_pairing as slow_pairing
from py_ecc.bn128.bn128_pairing import FQ2, FQ
from py_ecc.optimized_bn128.optimized_pairing import normalize
import py_ecc.optimized_bn128.optimized_pairing as fast_pairing
from web3 import Web3, HTTPProvider, IPCProvider
from solc import compile_files
from math import floor
import time
import eth_utils
from ExamineTransLogs import examineTransLogs
import EqualityTest
import ecpairing.ecpairing as whitebox
import random

# There is no cost or delay for reading the state of the blockchain, as this is held on our node
# port 8545 for geth
# port 7545 for ganache/testrpc - simulated ethereum blockchain
web3 = Web3(HTTPProvider('http://localhost:7545'))

# address no pairings: 0x2C2B9C9a4a25e24B174f26114e8926a9f2128FE4
# address with pairing: 0xFB88dE099e13c3ED21F80a7a1E49f8CAEcF10df6
contractAddr = eth_utils.to_checksum_address('0xF328c11c4dF88d18FcBd30ad38d8B4714F4b33bF')

# need contract code to know what methods can be addressed in contract on blockchain
compiled = compile_files(["solidity_test_pairing_code.sol"], "--optimized")
compiledCode = compiled['solidity_test_pairing_code.sol:pairing_check']
contract_instance = web3.eth.contract(contractAddr, abi=compiledCode['abi'])


# ORDERING of POINTS:
# Points from python pairing library in G2 are formatted as follows:
# [X_r,X_i][Y_r,Y_i], with the second set of coordinates (as used by solidity library), presented first in the ordering
# FQ2 constructor: [g2_x_r, g2_x_i] [g2_y_r, g2_y_i]
# Solidity pairing library uses: [X_i, X_r] [Y_i, Y_r]

# Everything I write will be formatted as [X_i,X_r][Y_i,Y_r].
# Where the imaginary component is listed first in the tuple and then the real component.
#   Except when the points are pulled from python library, they then have to be reformatted

# Takes a point or list of points in G1 and returns X,Y integers split up so they can be put in arrays
# Converts the ordering of the points from the underlying library ordering to solidity ordering (see above)
# assumes points have been normalized
def split_g1_points(points):
    if isinstance(points, list):
        x = [x.n for (x, y) in points]
        y = [y.n for (x, y) in points]
        return x, y
    if isinstance(points, tuple):
        if len(points) == 3:
            return split_g1_points(normalize(points))
        elif len(points) == 2:
            # Cast to int
            x, y = points
            return x.n, y.n
        else:
            raise TypeError("Expected point in G1")


# Takes a point or points in G2 and returns them split over x1, x2, y1, y2 as integers
def split_g2_points(points):
    if isinstance(points, list):
        xi = [x.coeffs[1] for (x, y) in points]
        xr = [x.coeffs[0] for (x, y) in points]
        yi = [y.coeffs[1] for (x, y) in points]
        yr = [y.coeffs[0] for (x, y) in points]
        # reordering points to our used representation
        return xi, xr, yi, yr
    if isinstance(points, tuple):
        if len(points) == 3:  # point still has x,y,z values from optimized library
            return split_g2_points(normalize(points))
        elif len(points) == 2:
            x, y = points
            # Reordering points to our representation
            return x.coeffs[1], x.coeffs[0], y.coeffs[1], y.coeffs[0]
        else:
            raise TypeError('Expected point in G2')


if __name__ == "__main__":
    # ethereum gives True if both all G1 elements are (0,0) (point at infinity), OR all G2 elements are ([0, 0], [0, 0])
    # python gives True in ethereum cases and also if pairings sum to [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    # hashID = (1, 2)
    # total = ([1, 0], [1, 0])
    # Does this pairing work out with python?
    # A: yes it does, it gives [1,0...,0]

    if True:
        # Generate values from EqualityTest
        n = 1
        master_keys, check_keys = EqualityTest.setup(n)
        test_token = EqualityTest.gen_token(master_keys, [3 for _ in range(n)], n)

        identifier = 5
        checks = [EqualityTest.encrypt(check_keys[x], identifier, 3) for x in range(n)]
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
        print("Created", (n*2)+1, "pairs of points")

    if False:
        G1 = fast_pairing.G1
        G2 = fast_pairing.G2
        G1_1 = fast_pairing.multiply(G1, 5 % fast_pairing.curve_order)
        G1_2 = fast_pairing.multiply(G1, 1 % fast_pairing.curve_order)
        #G1_3 = fast_pairing.multiply(G1, 1 % fast_pairing.curve_order)

        G2_1 = fast_pairing.multiply(G2, 1 % fast_pairing.curve_order)
        G2_2 = fast_pairing.multiply(G2, -5 % fast_pairing.curve_order)
        #G2_3 = fast_pairing.multiply(G2, -2 % fast_pairing.curve_order)

        listG1 = [G1_1, G1_2]
        listG2 = [G2_1, G2_2]

    # tests if all points on curve
    if True:
        for i in range(len(listG1)):
            assert (fast_pairing.is_on_curve(listG1[i], fast_pairing.b))
            assert (fast_pairing.is_on_curve(listG2[i], fast_pairing.b2))

    # solidity interface type conversion:
    # Convert points so they can be sent to blockchain
    listG1 = list(map(fast_pairing.normalize, listG1))
    listG2 = list(map(fast_pairing.normalize, listG2))

    g1points_x, g1points_y = split_g1_points(listG1)
    g2_x_i, g2_x_r, g2_y_i, g2_y_r = split_g2_points(listG2)

    # Call and print result of whitebox precompile
    if False:
        points_list = [None] * (len(listG1) + len(listG2))  # make empty list of correct size
        points_list[::2] = listG1
        points_list[1::2] = listG2
        result = whitebox.ecpairing_noconv(points_list)
        print("Pairing Precompile: ", result)

    print("g1x: ", g1points_x)
    print(len(g1points_x))
    print("g1y: ", g1points_y)
    print("g2xi: ", g2_x_i)
    print("g2xr: ", g2_x_r)
    print("g2yi: ", g2_y_i)
    print("g2yr: ", g2_y_r)
    # make transaction
    # method to be called comes after transact, as a python function call
    if True:
        print("Making transaction")
        tx_hash = contract_instance.transact({'from': web3.eth.accounts[0], 'gas': 4000000}).test_simple(
            g1points_x, g1points_y, g2_x_i, g2_x_r, g2_y_i, g2_y_r)

        #tx_hash = contract_instance.transact({'from': web3.eth.accounts[0], 'gas': 4000000}).testPairing2()

        # block until mined
        print("Waiting till transaction is mined")
        while web3.eth.getTransaction(tx_hash)['blockNumber'] is None:
            time.sleep(1)
        transaction_addr = web3.eth.getTransaction(tx_hash)['hash']
        print("Transaction address: ", transaction_addr.hex())
        examineTransLogs(contractAddr, transaction_addr.hex())

    if False:
        outputs = contract_instance.call({'from': web3.eth.accounts[0], 'gas': 4000000}).test_simple(
            g1points_x, g1points_y, g2_x_i, g2_x_r, g2_y_i, g2_y_r)
        #outputs = contract_instance.call({'from': web3.eth.accounts[0], 'gas': 4000000}).testPairing2()
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
    # There is a no difference between setting pairing_total to FQ12.one() first or assigning the variable only
    # in the first loop.
