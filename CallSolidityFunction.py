# slowPairing only uses X,Y points instead of X,Y,Z points, which we need here
import py_ecc.bn128.bn128_pairing as slowPairing
from py_ecc.bn128.bn128_pairing import FQ2, FQ
from web3 import Web3, HTTPProvider, IPCProvider
from solc import compile_files
from math import floor
import time
import eth_utils
from ExamineTransLogs import examineTransLogs

# There is no cost or delay for reading the state of the blockchain, as this is held on our node
# port 8545 for geth
# port 7545 for ganache/testrpc - simulated ethereum blockchain
web3 = Web3(HTTPProvider('http://localhost:7545'))

# address generates exception: 0xB529f14AA8096f943177c09Ca294Ad66d2E08b1f
# address doesn't: 0x4eee4559bd589b1cdfc419f0eed2ff9cbd47f439
contractAddr = eth_utils.to_checksum_address('0x8CdaF0CD259887258Bc13a92C0a6dA92698644C0')



# need contract code to know what methods can be addressed in contract on blockchain
compiled = compile_files(["solidity_test_pairing_code.sol"], "--optimized")
compiledCode = compiled['solidity_test_pairing_code.sol:pairing_check']
contract_instance = web3.eth.contract(contractAddr, abi=compiledCode['abi'])

# ORDERING of POINTS:
# Points from python pairing library in G2 are formatted as follows:
# [X2,X1][Y2,Y1], with the second set of coordinates (as used by solidity library), presented first in the ordering
# FQ2 constructor: [g2_2_x, g2_1_x] [g2_2_y, g2_1_y]    -- Gah why
# Solidity pairing library uses: [X1, X2] [Y1, Y2]

# Everything I write will be formatted as [X1,X2][Y1,Y2].
#   Except when the points are pulled from python library, they then have to be reformatted


# Takes a point or points in G1 or G2 and distributes it over arrays so they can be used by smartcontract
# arrays ordered for G2: g2_1_x, g2_1_y, g2_2_x, g2_2_y because then can do both G1 and G2 with same method
#   Still assumes input points are [g2_2_x, g2_1_x] [g2_2_y, g2_1_y]
def split_points(points, arrayX_1, arrayY_1, arrayX_2=None, arrayY_2=None):
    if isinstance(points, tuple):  # single points
        if isinstance(points[0], int) or isinstance(points[0], FQ):  # point in G1
            assert(len(points) == 2)
            arrayX_1.append(points[0])
            arrayY_1.append(points[1])
        elif isinstance(points[0], list):
            assert(len(points[0]) == 2)
            arrayX_1.append(points[0][1])
            arrayX_2.append(points[0][0])
            arrayY_1.append(points[1][1])
            arrayY_2.append(points[1][0])
        else:
            raise TypeError("Expected either a point in G1 or G2")
    if isinstance(points, list): # multiple points
        for val in points:
            split_points(val, arrayX_1, arrayY_1, arrayX_2, arrayY_2)


def pairing(g2_point, g1_point):
    if g1_point != (0,0):   # if g1 not point at infinity
        return slowPairing.pairing(g2_point, g1_point)
    else:  # makes point at infinity easier to deal with between python/ethereum
        return slowPairing.pairing(g2_point, None)


def is_on_curve(point,b):
    if point != (0,0):
        return slowPairing.is_on_curve(point,b)
    elif b == slowPairing.b: # point at infinity compatiblity python/ethereum
        return True;
    else: # tried (0,0) in not G1
        return False;


# Test values for n=3 parties
#g1toRX = [(4503322228978077916651710446042370109107355802721800704639343137502100212473, 6132642251294427119375180147349983541569387941788025780665104001559216576968), (19250379796230621580717331452463663345896564525276976787683504932365879146125, 3443367600620863376043399521793996098303772283604389115449400372124847261983), (13397190861361930130708828780039873280089568817446975144850978951308113982899, 3696580789169156927429821910380058532911671864362101595128123040227975159321)]
#g1toAlpha = [(10076202152297490686204017674658616195706856331923113611424582186251671204174, 5332583658353911387952875219880585170702835693592572334525184064653452913461), (2558564656686107921807343647838149321424071993952499564439014691219101534500, 11111814337745261702647154871514534702182623302987054308693876555940128148837),  (3116785268345430093691724307330138853549768272668021550726998366627612282075, 7192650871514092392312872864766077799154829053450471500423035183341534721817)]
#hashID = (10744596414106452074759370245733544594153395043370666422502510773307029471145, 848677436511517736191562425154572367705380862894644942948681172815252343932)
#g2toU = [([20954117799226682825035885491234530437475518021362091509513177301640194298072, 4540444681147253467785307942530223364530218361853237193970751657229138047649], [21508930868448350162258892668132814424284302804699005394342512102884055673846, 11631839690097995216017572651900167465857396346217730511548857041925508482915]),  ([20954117799226682825035885491234530437475518021362091509513177301640194298072, 4540444681147253467785307942530223364530218361853237193970751657229138047649], [21508930868448350162258892668132814424284302804699005394342512102884055673846, 11631839690097995216017572651900167465857396346217730511548857041925508482915]), ([20954117799226682825035885491234530437475518021362091509513177301640194298072, 4540444681147253467785307942530223364530218361853237193970751657229138047649], [21508930868448350162258892668132814424284302804699005394342512102884055673846, 11631839690097995216017572651900167465857396346217730511548857041925508482915])  ]
#g2toalpha = [([16254737008305706031004429264063885572618336716292470244842285039341668886874, 3045295354179676677849867948999926981809716450107785272685219528794174444834], [10847281460042142598816270676372539992803021388916026621484136992759522018115, 3687031281311398245656729489850260357742732581131462810186398483442070052844])  , ([16254737008305706031004429264063885572618336716292470244842285039341668886874, 3045295354179676677849867948999926981809716450107785272685219528794174444834], [10847281460042142598816270676372539992803021388916026621484136992759522018115, 3687031281311398245656729489850260357742732581131462810186398483442070052844]) ,   ([16254737008305706031004429264063885572618336716292470244842285039341668886874, 3045295354179676677849867948999926981809716450107785272685219528794174444834], [10847281460042142598816270676372539992803021388916026621484136992759522018115, 3687031281311398245656729489850260357742732581131462810186398483442070052844]) ]
#total = ([16254737008305706031004429264063885572618336716292470244842285039341668886874, 3045295354179676677849867948999926981809716450107785272685219528794174444834], [10847281460042142598816270676372539992803021388916026621484136992759522018115, 3687031281311398245656729489850260357742732581131462810186398483442070052844])

g1toAlpha = [(10076202152297490686204017674658616195706856331923113611424582186251671204174, 5332583658353911387952875219880585170702835693592572334525184064653452913461)]
g2toU = [([20954117799226682825035885491234530437475518021362091509513177301640194298072, 4540444681147253467785307942530223364530218361853237193970751657229138047649], [21508930868448350162258892668132814424284302804699005394342512102884055673846, 11631839690097995216017572651900167465857396346217730511548857041925508482915])  ]
g1toRX = [(4503322228978077916651710446042370109107355802721800704639343137502100212473, 6132642251294427119375180147349983541569387941788025780665104001559216576968)]
g2toalpha = [([16254737008305706031004429264063885572618336716292470244842285039341668886874, 3045295354179676677849867948999926981809716450107785272685219528794174444834], [10847281460042142598816270676372539992803021388916026621484136992759522018115, 3687031281311398245656729489850260357742732581131462810186398483442070052844]) ]
#hashID = (10744596414106452074759370245733544594153395043370666422502510773307029471145, 848677436511517736191562425154572367705380862894644942948681172815252343932)
# total = ([14502447760486387799059318541209757040844770937862468921929310682431317530875, 2443430939986969712743682923434644543094899517010817087050769422599268135103], [11721331165636005533649329538372312212753336165656329339895621434122061690013, 4704672529862198727079301732358554332963871698433558481208245291096060730807])

# g1toAlpha = (1, 2)
# g1toRX = (1, 21888242871839275222246405745257275088696311157297823662689037894645226208581)

# g1toAlpha = (0, 0)
# g1toRX = (0,0)

# G2 and neg(G2)
#g2toU = ([10857046999023057135944570762232829481370756359578518086990519993285655852781, 11559732032986387107991004021392285783925812861821192530917403151452391805634], [8495653923123431417604973247489272438418190587263600148770280649306958101930, 4082367875863433681332203403145435568316851327593401208105741076214120093531])
#g2toalpha = ([10857046999023057135944570762232829481370756359578518086990519993285655852781, 11559732032986387107991004021392285783925812861821192530917403151452391805634], [13392588948715843804641432497768002650278120570034223513918757245338268106653, 17805874995975841540914202342111839520379459829704422454583296818431106115052])
# hashID = (0, 0)

# g2toU = ([0, 0], [0, 0])
# g2toalpha = ([0, 0], [0, 0])

print(slowPairing.multiply(slowPairing.G2, 0))
# ethereum gives True if both all G1 elements are (0,0) (point at infinity), OR all G2 elements are ([0, 0], [0, 0])
# python gives True in ethereum cases and also if pairings sum to [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


#hashID = (1, 2)
#total = ([1, 0], [1, 0])
# Does this pairing work out with python?
# A: yes it does, it gives [1,0...,0]

g1points_x = []
g1points_y = []
g2_x_1 = []
g2_x_2 = []
g2_y_1 = []
g2_y_2 = []

split_points(g1toAlpha, g1points_x, g1points_y)
split_points(g2toU, g2_x_1, g2_y_1, g2_x_2, g2_y_2)
split_points(g1toRX, g1points_x, g1points_y)
split_points(g2toalpha, g2_x_1, g2_y_1, g2_x_2, g2_y_2)
#split_points(hashID, g1points_x, g1points_y)
#split_points(total, g2_x_1, g2_y_1, g2_x_2, g2_y_2)

# additive identity G1 in python: slowPairing.multiply(slowPairing.one,0)  -- None
# additive identity G1 in solidity: Pairing.mul(Pairing.P1(), 0); -- (0,0)
# TODO; try to make the library give a correct output. What about pairing (0,0) and (0,0)
# TODO: pairing library says == 1 should give True. EIP 197 says == 0
# Debug code to test the exact same functionality as blockchain in python library
if False:
    check_total = slowPairing.FQ12.one()
    for x in range(len(g1toAlpha)):
        #
        # (FQ(g1toAlpha[x][0]), FQ(g1toAlpha[x][1])
        paired = pairing((FQ2(g2toU[x][0]), FQ2(g2toU[x][1])), (FQ(g1toAlpha[x][0]), FQ(g1toAlpha[x][1])))
        check_total = check_total * paired
        # print values so I can test blockchain function
        print("g2toU: ", g2toU[x])
        print("g1toalpha: ", g1toAlpha[x])

    # pairing with complicated element in g2
    token_total = slowPairing.FQ12.one()
    for x in range(len(g1toAlpha)):
        inverted_point = slowPairing.neg((FQ(g1toRX[x][0]), FQ(g1toRX[x][1])))
        # Inverted_point
        paired = pairing((FQ2(g2toalpha[x][0]), FQ2(g2toalpha[x][1])), inverted_point)
        token_total = token_total * paired
        print("g2toalpha: ", g2toalpha[x])
        print("g1toRX: ", inverted_point)

    invert_total = slowPairing.neg((FQ(hashID[0]), FQ(hashID[1])))
    total_python = (FQ2(total[0]), FQ2(total[1]))
    token_total = token_total * pairing(total_python, invert_total)

    print("Check total: ", check_total)
    print("InvToken total: ", token_total)
    print("Check * InvToken", check_total * token_total)


# Do Pairing by pairing all points and then multiplying the results together
if False:
    print("Pairing in python, total", len(g1points_x), "pairings")
    for x in range(len(g1points_x)):
        if x >= floor(len(g1points_x)/2):  # negate second half of points/second part equation
            g1_point = slowPairing.neg((FQ(g1points_x[x]), FQ(g1points_y[x])))
        else:
            g1_point = (FQ(g1points_x[x]), FQ(g1points_y[x]))
        g2_point = (FQ2([g2_x_2[x], g2_x_1[x]]), FQ2([g2_y_2[x], g2_y_1[x]]))
        pair = pairing(g2_point, g1_point)
        try:   # make sure it's defined without starting with a slowPairing.FQ12.one()
            pairing_total = pairing_total * pair
        except NameError:
            pairing_total = pair
        print("Completed pairing ", x)
    print("Pairing tot py sum: ", pairing_total)
    pairing_total *= slowPairing.FQ12.one()
# TODO; there is a no difference between setting pairing_total to FQ12.one() first or assigning the variable only
# in the first loop. (EXCEPT if you don't then assign the variable properly so it multiplies twice the first time, GAH)


#tests if all points on curve
if False:
    for i in range(len(g1points_x)):
        pointG1 = (slowPairing.FQ(g1points_x[i]), slowPairing.FQ(g1points_y[i]))
        assert(is_on_curve(pointG1, slowPairing.b))
        PointG2 = (slowPairing.FQ2([g2_x_2[i], g2_x_1[i]]), slowPairing.FQ2([g2_y_2[i], g2_y_1[i]]))
        assert(is_on_curve(PointG2, slowPairing.b2))

# make transaction
# method to be called comes after transact, as a python function call
if False:
    print("Making transaction")
    tx_hash = contract_instance.transact({'from': web3.eth.accounts[0], 'gas': 4000000}).test_simple(
      g1points_x, g1points_y, g2_x_1, g2_x_2, g2_y_1, g2_y_2)

    #tx_hash = contract_instance.transact({'from': web3.eth.accounts[0], 'gas': 4000000}).testPairing()

    # block until mined
    print("Waiting till transaction is mined")
    while web3.eth.getTransaction(tx_hash)['blockNumber'] is None:
        time.sleep(1)
    transaction_addr = web3.eth.getTransaction(tx_hash)['hash']
    print("Transaction address: ", transaction_addr.hex())
    examineTransLogs(contractAddr, transaction_addr.hex())



outputs = contract_instance.call({'from': web3.eth.accounts[0], 'gas': 4000000}).test_simple(
       g1points_x, g1points_y, g2_x_1, g2_x_2, g2_y_1, g2_y_2)
print(outputs)


