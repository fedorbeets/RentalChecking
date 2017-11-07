import py_ecc.optimized_bn128.optimized_pairing as pairing
import random

# Picking key_space as all numbers 0...pairing.curve_order, which seems like a suitably large number.
key_space = pairing.curve_order

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
        beta_x = rand.randint(1, key_space)
        # put elements on curve
        elliptic_alpha_x = pairing.multiply(pairing.G2, alpha_x)
        elliptic_gamma_x = pairing.multiply(pairing.G2, gamma_x)
        msks.append(dict(
            [('alpha_multiplied', elliptic_alpha_x), ('beta', beta_x), ('gamma_multiplied', elliptic_gamma_x)]))
        g1_alpha_x = pairing.multiply(pairing.G1, alpha_x)
        chck_keys.append(dict([('alpha_g1', g1_alpha_x), ('beta', beta_x), ('gamma', gamma_x)]))
    return msks, chck_keys


# Takes a list of master keys and a list of rule requirements and outputs an encrypted token that
# check results are to be matched against
# msks - from setup
# rule - list of n numbers in "message space"
# n - length of rule vector
def gen_token(msks, rule, n):
    rand = random.SystemRandom()
    total = 1
    mini_tokens = []
    for x in range(0, n):
        u_x = rand.randint(1, pairing.curve_order)
        u_x_multiplied = pairing.multiply(pairing.G2, u_x)
        exponent = u_x * prp(msks[x]['beta'], rule[x])
        eliptic_prp = pairing.multiply(msks[x]['alpha_multiplied'], exponent)
        assert isinstance(u_x, int)
        total *= pairing.multiply(msks['gamma_multiplied'], u_x)
        mini_tokens.append(dict([('u_multiplied', u_x_multiplied), ('prp_multiplied', eliptic_prp)]))
    return mini_tokens, total


# chck_key - 1 of the check keys from setup
# identifier - a number used identically amongst all encrypts in the EqualityTest
# message - the number to be encrypted
def encrypt(chck_key, identifier, message):
    rand = random.SystemRandom()
    r_x = rand.randint(1, pairing.curve_order)
    r_x_multiplied = pairing.multiply(pairing.G1, r_x)
    exponent = r_x * prp(chck_key['beta'], message)
    g1_exponentiated = pairing.multiply(chck_key['alpha_g1'], exponent)
    identifier_hashed_multiplied = pairing.multiply(elliptic_hash(identifier), message)
    # TODO: in this step they have to be added together, right?
    g1_and_hash_added = pairing.add(g1_exponentiated, identifier_hashed_multiplied)
    return dict([('hash_ident', elliptic_hash(identifier)), ('r_x_mul', r_x_multiplied),
                ('g1_hash_add', g1_and_hash_added)])


# off chain test function
def test(token, n, *arg):
    assert len(arg) == n
    # pairing with 'complicated token element'
    check_total = 1
    for x in range(0, n):
        paired = pairing.pairing(arg[x]['g1_hash_add'], token[0][x]['u_multiplied'])
        assert isinstance(paired, pairing.FQ12)
        check_total *= paired
    token_total = 1
    for x in range(0, n):
        paired = pairing.pairing(arg[x]['r_x_mul'], token[0][x]['prp_multiplied'])
        token_total *= paired
    # TODO; assuming only multiplying pairing(hash,token_total) once at end
    token_total *= pairing.pairing(arg[0]['hash_ident'], token[1])
    # TODO: assuming equality will check all individual exponents
    return check_total == token_total


# pseudo-random permutation function, stub implementation
# todo: make non-stub implementation
def prp(beta, y):
    return 5


# stub implementation, needs to be a one way function that returns an element on the G1 curve
# todo: secure implementation of actual one way function
def elliptic_hash(number: int) -> tuple:
    modded_number = number % pairing.curve_order
    return pairing.multiply(pairing.G1, modded_number)


setup = setup(3)
print(setup[0][0]['alpha_multiplied'])
#print(setup[1])
