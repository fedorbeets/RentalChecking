import py_ecc.optimized_bn128.optimized_pairing as pairing
from py_ecc.optimized_bn128.optimized_pairing import multiply
from py_ecc.optimized_bn128.optimized_pairing import add
import random

# Picking key_space as all numbers 0...pairing.curve_order, which seems like a suitably large number.
key_space = pairing.curve_order
MESSAGE_SPACE = 32
# TODO; rewrite with use of field_elements helper functions


# Takes as input the length of the vector to be tested: n and
# security parameter.
# Outputs the rule generator key RK
# and check keys CK 1 through CK n . Public parameters part of the library
def setup(n):
    rand = random.SystemRandom()
    msks = []       # master secret key for token generation
    chck_keys = []  # checking keys
    for x in range(0, n):
        # random numbers of Zp
        alpha_x = rand.randint(1, pairing.curve_order)
        gamma_x = rand.randint(1, pairing.curve_order)
        # random number in key space
        beta_x = []
        for j in range(0, MESSAGE_SPACE):
            beta_x.append(rand.randint(1, key_space))
        # put elements on curve
        elliptic_alpha_x = multiply(pairing.G2, alpha_x)
        elliptic_gamma_x = multiply(pairing.G2, gamma_x)
        msks.append(dict(
            [('alpha_multiplied', elliptic_alpha_x), ('beta', beta_x), ('gamma_multiplied', elliptic_gamma_x)]))
        g1_alpha_x = multiply(pairing.G1, alpha_x)
        chck_keys.append(dict([('alpha_g1', g1_alpha_x), ('beta', beta_x), ('gamma', gamma_x)]))
    return msks, chck_keys


# Takes a list of master keys and a list of rule requirements and outputs an encrypted token that
# check results are to be matched against
# msks - from setup
# rule - list of n numbers in "message space"
# n - length of rule vector
def gen_token(msks, rule, n):
    rand = random.SystemRandom()
    # identity element for addition
    total = (pairing.FQ2.zero(), pairing.FQ2.zero(), pairing.FQ2.zero())
    mini_tokens = []
    for x in range(0, n):
        u_x = rand.randint(1, pairing.curve_order)
        u_x_multiplied = multiply(pairing.G2, u_x)
        exponent = u_x * prp(msks[x]['beta'], rule[x])
        elliptic_prp = multiply(msks[x]['alpha_multiplied'], exponent)
        assert isinstance(u_x, int)
        # todo: assume multiplication of elliptic curve elements (big sum-multiply pi symbol) means add all elements together
        total = add(total, multiply(msks[x]['gamma_multiplied'], u_x))
        mini_tokens.append(dict([('u_multiplied', u_x_multiplied), ('prp_multiplied', elliptic_prp)]))
    return mini_tokens, total


# chck_key - 1 of the check keys from setup
# identifier - a number used identically amongst all encrypts in the EqualityTest
# message - the number to be encrypted
def encrypt(chck_key, identifier, message):
    rand = random.SystemRandom()
    r_x = rand.randint(1, pairing.curve_order)
    r_x_multiplied = multiply(pairing.G1, r_x)
    exponent = r_x * prp(chck_key['beta'], message)
    g1_exponentiated = multiply(chck_key['alpha_g1'], exponent)
    identifier_hashed_multiplied = multiply(elliptic_hash(identifier), message)
    # TODO: in this step they have to be added together, right?
    g1_and_hash_added = add(g1_exponentiated, identifier_hashed_multiplied)
    return dict([('hash_ident', elliptic_hash(identifier)), ('r_x_mul', r_x_multiplied),
                ('g1_hash_add', g1_and_hash_added)])


# off chain test function
def test(token, n, *arg):
    assert len(arg) == n
    # pairing with complicated element in g1
    check_total = pairing.FQ12.zero()
    for x in range(0, n):
        paired = pairing.pairing(token[0][x]['u_multiplied'], arg[x]['g1_hash_add'])
        assert isinstance(paired, pairing.FQ12)
        check_total = check_total.__add__(paired)
    # pairing with complicated element in g2
    token_total = pairing.FQ12.zero()
    for x in range(0, n):
        paired = pairing.pairing(token[0][x]['prp_multiplied'], arg[x]['r_x_mul'])
        token_total = token_total.__add__(paired)
    # TODO; assuming only multiplying pairing(hash,token_total) once at end instead of every time in loop
    token_total = token_total.__add__(pairing.pairing(token[1], arg[0]['hash_ident']))
    # TODO: assuming equality will check all individual exponents
    print("check_total: ", check_total)
    print("token_total: ", token_total)
    return check_total == token_total


# pseudo-random permutation function, stub implementation
# todo: make non-stub implementation
def prp(b: list, x: int) -> int:
    output = 1
    assert len(b) <= MESSAGE_SPACE
    # todo: starting at 1 ignores first bit of message x, correct?
    for i in range(1, len(b)):  # prf starts at 1, 0th is pairing.multiply(g1,alpha_i)
        output *= pow(b[i], ((x >> i) & 1))  # only keep bit i
    return output


# stub implementation, needs to be a one way function that returns an element on the G1 curve
# todo: secure implementation of actual one way function
def elliptic_hash(number: int) -> tuple:
    modded_number = number % pairing.curve_order
    return multiply(pairing.G1, modded_number)


print("pretest")
print(prp([2,2,2,2,2,2,2,2,2,2], 3))


print("Setup")
master_keys, check_keys = setup(3)
print("GenToken")
test_token = gen_token(master_keys, [1, 1, 1], 3)
print("encrypt checks")
identify = 5
check1 = encrypt(check_keys[0], identify, 1)
check2 = encrypt(check_keys[1], identify, 1)
check3 = encrypt(check_keys[2], identify, 1)
print("Check")
result = test(test_token, 3, check1, check2, check3)
print(result)