import py_ecc.optimized_bn128.optimized_pairing as pairing
from py_ecc.optimized_bn128.optimized_pairing import multiply, add
from py_ecc.optimized_bn128.optimized_pairing import normalize1
import random
import math

# Picking key_space as all numbers 0...pairing.curve_order, which seems like a suitably large number.
key_space = pairing.curve_order
MESSAGE_SPACE = 32  # Don't make 1 due to log function


# Takes as input the length of the vector to be tested: n and
# security parameter.
# Outputs the rule generator key RK
# and check keys CK 1 through CK n . Public parameters part of the library
def setup(n, alpha=0, gamma=0, beta=0):  # optional rng determination for testing purposes NOT CRYPTOGRAPHICALLY SAFE
    rand = random.SystemRandom()
    msks = []       # master secret key for token generation
    chck_keys = []  # checking keys
    for _ in range(n):
        single_msk = {}  # a part of the master secret key
        single_chck = {}  # a single checking key
        # generate random numbers of Zp*
        alpha_x = rand.randint(1, pairing.curve_order)
        if alpha != 0:  # if random number pregiven
            alpha_x = alpha
        gamma_x = rand.randint(1, pairing.curve_order)
        if gamma != 0:
            gamma_x = gamma
        # Key space amount of random numbers
        beta_x = []
        for __ in range(math.ceil(math.log(MESSAGE_SPACE, 2))):
            beta_x.append(rand.randint(1, pairing.curve_order))
        if beta != 0:  # if random number has been given
            beta_x = beta

        single_msk['alpha_multiplied'] = multiply(pairing.G2, alpha_x)  # alpha_x * G2
        single_msk['beta'] = beta_x
        single_msk['gamma_multiplied'] = multiply(pairing.G2, gamma_x)  # gamma_x * G2
        msks.append(single_msk)

        single_chck['alpha_g1'] = multiply(pairing.G1, alpha_x)
        single_chck['beta'] = beta_x
        single_chck['gamma_x'] = gamma_x
        chck_keys.append(single_chck)
    return msks, chck_keys


# Takes a list of master keys and a list of rule requirements and outputs an encrypted token that
# check results are to be matched against
# msks - from setup
# rule - list of n numbers in "message space"
# n - length of rule vector
def gen_token(msks, rule, n, u=0):
    rand = random.SystemRandom()
    # identity element for addition
    total = (pairing.FQ2.zero(), pairing.FQ2.zero(), pairing.FQ2.zero())
    mini_tokens = []
    for x in range(n):
        single_token = {}  # the values of a token for a single x
        u_x = rand.randint(1, pairing.curve_order)
        if u != 0:  # if random number has been given, use it
            u_x = u

        single_token['u_multiplied'] = multiply(pairing.G2, u_x)

        exponent = (prp(msks[x]['beta'], rule[x]) * u_x) % pairing.curve_order
        single_token['alpha_mul_g2_mul_prp'] = multiply(msks[x]['alpha_multiplied'], exponent)
        mini_tokens.append(single_token)
        total = add(total, multiply(msks[x]['gamma_multiplied'], u_x))
    return mini_tokens, total


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
    # pairing with complicated element in g1
    check_total = pairing.FQ12.one()
    for x in range(n):
        paired = pairing.pairing(token[0][x]['u_multiplied'], arg[x]['g1_mul_prp_add_ident_hash'])
        check_total = check_total * paired

    # pairing with complicated element in g2
    token_total = pairing.FQ12.one()
    for x in range(n):
        paired = pairing.pairing(token[0][x]['alpha_mul_g2_mul_prp'], arg[x]['r_x_mul'])
        token_total = token_total * paired
    token_total = token_total * pairing.pairing(token[1], arg[0]['hash_ident'])

    return check_total == token_total


# pseudo-random permutation function
def prp(b: list, x: int) -> int:
    output = 1
    assert len(b) <= MESSAGE_SPACE
    # todo: starting at 0, because I go from 0..n-1 instead of 1..n
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
    master_keys, check_keys = setup(3, alpha=2, gamma=2, beta=[3, 4])
    print("GenToken")
    # note: rng for u is re-used in every rule-loop, that is not realistic for system
    test_token = gen_token(master_keys, [1, 1, 1], 3, u=5)
    print("encrypt checks")
    identify = 5
    check1 = encrypt(check_keys[0], identify, 1, r=6)
    check2 = encrypt(check_keys[1], identify, 1, r=4708642907422499050704862076428092405590089492351158641052908492133734418081)
    check3 = encrypt(check_keys[2], identify, 1, r=10465556228797287385848073339865451232298354941118980474002801677313279097215)
    print("Check")
    result = test(test_token, 3, check1, check2, check3)
    print("Token = check:    ", result)
    # assert(result)  # big cheer if otherwise


test_routine()


# print("pretest")
# pairing(P, Q+R) = pairing(P,Q) * pairing(P,R) - correct
