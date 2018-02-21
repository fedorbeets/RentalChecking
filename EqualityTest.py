import py_ecc.optimized_bn128.optimized_pairing as pairing
from py_ecc.optimized_bn128.optimized_pairing import multiply, add
import random
import math
from multiprocessing import Pool
from functools import reduce
import operator
# import cProfile

# Picking key_space as all numbers 0...pairing.curve_order, which seems like a suitably large number.
key_space = pairing.curve_order
MESSAGE_SPACE = 32  # Don't make 1 due to log function


# Takes as input the length of the vector to be tested: n and
# security parameter.
# Outputs the rule generator key RK
# and check keys CK 1 through CK n . Public parameters part of the library
def setup(n, alpha=0, gamma=0, beta=0):  # optional rng determination for testing purposes NOT CRYPTOGRAPHICALLY SAFE
    rand = random.SystemRandom()
    pool = Pool()

    # 3 random values, master secret keys for token generation, checking keys
    # alphas, gammas have a list of random values
    # betas has a list of a list of random values
    alphas, gammas, betas, msks, chck_keys = [[] for _ in range(5)]

    # rng setup
    if alpha != 0:  # if random number pregiven
        assert(gamma != 0 and beta != 0)
        alphas = alpha
        gammas = gamma
        betas = beta
    else:
        for _ in range(n):
            alphas.append(rand.randint(1, pairing.curve_order))
            gammas.append(rand.randint(1, pairing.curve_order))
            # Key space amount of random numbers
            beta_x = []
            for __ in range(int(math.ceil(math.log(MESSAGE_SPACE, 2)))):
                beta_x.append(rand.randint(1, pairing.curve_order))
            betas.append(beta_x)

    result = pool.starmap(single_setup, zip(alphas, gammas, betas))
    msks, chck_keys = list(zip(*result))

    return msks, chck_keys


def single_setup(alpha=0, gamma=0, beta=0):
    msk, chck = {}, {}  # a part of the master secret key, single checking key

    msk['alpha_multiplied'] = multiply(pairing.G2, alpha)  # alpha_x * G2
    msk['beta'] = beta
    msk['gamma_multiplied'] = multiply(pairing.G2, gamma)  # gamma_x * G2

    chck['alpha_g1'] = multiply(pairing.G1, alpha)
    chck['beta'] = beta
    chck['gamma_x'] = gamma
    return msk, chck


# Takes a list of master keys and a list of rule requirements and outputs an encrypted token that
# check results are to be matched against
# msks - from setup
# rule - list of n numbers in "message space"
# n - length of rule vector
def gen_token(msks, rule, n, u=0):
    assert(len(rule) == n)
    rand = random.SystemRandom()
    pool = Pool()

    if u != 0:  # rng predetermination
        us = u
    else:
        us = [rand.randint(1, pairing.curve_order) for _ in range(n)]

    result = pool.starmap(single_token_fun, zip(msks, rule, us))
    mini_tokens, u_multiplieds = list(zip(*result))
    total = reduce(add, u_multiplieds)  # add all u values together

    return mini_tokens, total


def single_token_fun(msk, rule, u):
    single_token = {'u_multiplied': multiply(pairing.G2, u)}

    exponent = (prp(msk['beta'], rule) * u) % pairing.curve_order
    single_token['alpha_mul_g2_mul_prp'] = multiply(msk['alpha_multiplied'], exponent)
    return single_token, multiply(msk['gamma_multiplied'], u)


# chck_key - 1 of the check keys from setup
# identifier - a number used identically amongst all encrypts in the EqualityTest
# message - the number to be encrypted
def encrypt(chck_key, identifier, message, r=0):
    ct_i = {}  # an encryption check result
    rand = random.SystemRandom()
    r_x = rand.randint(1, pairing.curve_order)
    if r != 0:
        r_x = r

    # todo: is multiplication in Z_p just normal multiplication mod p?
    ct_i['hash_ident'] = elliptic_hash(identifier)
    ct_i['r_x_mul'] = multiply(pairing.G1, r_x)
    exponent = (prp(chck_key['beta'], message) * r_x) % pairing.curve_order
    g1_exponentiated = multiply(chck_key['alpha_g1'], exponent)
    ident_hash_mul_message = multiply(ct_i['hash_ident'], chck_key['gamma_x'])
    ct_i['g1_mul_prp_add_ident_hash'] = add(g1_exponentiated, ident_hash_mul_message)
    return ct_i


# off chain test function
def test(token, n, *arg):
    assert len(arg) == n
    pool = Pool()
    left_arguments = []

    # create iterable from the arguments, so that starmap can be used
    for x in range(n):
        left_arguments.append([token[0][x]['u_multiplied'], arg[x]['g1_mul_prp_add_ident_hash']])

    # pairings where g2 = G2^u  and g1 = G1^alpha*prp(beta,x)*r * hash(id)^gamma
    g2_u_g1_prp = pool.starmap(pairing.pairing, left_arguments)  # do all pairings at the same time
    check_total = reduce(operator.mul, g2_u_g1_prp)  # multiply pairings together

    right_arguments = []
    for x in range(n):
        # pairing with g2 = G2^alpha*prp(beta,y)*u  and g1 = G1^r
        right_arguments.append([token[0][x]['alpha_mul_g2_mul_prp'], arg[x]['r_x_mul']])

    # The pairing where g2 = mulsum(G2^gamma*u) and g1 = hash(ID)
    right_arguments.append([token[1], arg[0]['hash_ident']])
    g2_alpha_g1_r = pool.starmap(pairing.pairing, right_arguments)
    token_total = reduce(operator.mul, g2_alpha_g1_r)

    # to print values for blockchain function:
    # print("thingie: ", pairing.normalize( ---location--- ))
    return check_total == token_total


# pseudo-random permutation function
def prp(b: list, x: int) -> int:
    output = 1
    assert len(b) <= MESSAGE_SPACE
    # could be optimized to go to range min(math.ceil(math.log(x, 2))), 1)
    for i in range(len(b)):  # prf starts at 1, 0th is pairing.multiply(g1,alpha_i)
        bit_i = ((x >> i) & 1)
        if bit_i:
            output = (b[i] * output) % pairing.curve_order
    return output


# stub implementation, needs to be a one way function that returns an element on the G1 curve
# todo: secure implementation of actual one way function
def elliptic_hash(number: int) -> tuple:
    modded_number = number % pairing.curve_order
    return multiply(pairing.G1, modded_number)


def test_routine():
    print("Setup")
    master_keys, check_keys = setup(5)
    print("GenToken")
    test_token = gen_token(master_keys, [3, 3, 3, 3, 3], 5)
    print("encrypt checks")
    identifier = 5
    check1 = encrypt(check_keys[0], identifier, 3)
    check2 = encrypt(check_keys[1], identifier, 3)
    check3 = encrypt(check_keys[2], identifier, 3)
    check4 = encrypt(check_keys[3], identifier, 3)
    check5 = encrypt(check_keys[4], identifier, 3)
    print("Check")
    result = test(test_token, 5, check1, check2, check3, check4, check5)
    print("Token = check:    ", result)


if __name__ == "__main__":
    test_routine()
    # add e.g. sort='cumulative' to sort the output
    # cProfile.run('test_routine()', sort='cumulative')
