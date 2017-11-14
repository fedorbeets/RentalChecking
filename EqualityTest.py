import py_ecc.optimized_bn128.optimized_pairing as pairing
from py_ecc.optimized_bn128.optimized_pairing import multiply
from py_ecc.optimized_bn128.optimized_pairing import add
import random
import math

# Picking key_space as all numbers 0...pairing.curve_order, which seems like a suitably large number.
key_space = pairing.curve_order
MESSAGE_SPACE = 32  # Don't make 1 due to log function
# TODO; rewrite with use of field_elements helper functions


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
        if u != 0:
            u_x = u

        single_token['u_multiplied'] = multiply(pairing.G2, u_x)

        exponent = (prp(msks[x]['beta'], rule[x]) * u_x) % pairing.curve_order
        # todo: if I have (x*y)*G2, then I have to do (x*y%P)*G2.  How to do this when you already have (y*G2)=alpha
        #   and you do x*alpha
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
    ident_hash_mul_message = multiply(ct_i['hash_ident'], message)
    ct_i['g1_mul_prp_add_ident_hash'] = add(g1_exponentiated, ident_hash_mul_message)
    return ct_i


# off chain test function
def test(token, n, *arg):
    assert len(arg) == n
    # pairing with complicated element in g1
    check_total = pairing.FQ12.zero()
    for x in range(n):
        paired = pairing.pairing(token[0][x]['u_multiplied'], arg[x]['g1_mul_prp_add_ident_hash'])
        check_total = check_total.__add__(paired)

    # pairing with complicated element in g2
    token_total = pairing.FQ12.zero()
    for x in range(n):
        paired = pairing.pairing(token[0][x]['alpha_mul_g2_mul_prp'], arg[x]['r_x_mul'])
        token_total = token_total.__add__(paired)
    token_total = token_total.__add__(pairing.pairing(token[1], arg[0]['hash_ident']))
    print(type(token_total))
    print(pairing.is_on_curve(token_total, pairing.b12))  # token_total is not on curve

    # debug code
    print("check_total: ", check_total)
    print("token_total: ", token_total)
    old_check_total = pairing.FQ12([16545322402642902403827778336215892099700673422841134395110721666425930651722, 21674761656022931628057531015405594355998963223510722524813195501089384702642, 579830756963587943926949281128225371002373912611062948305395561870915988482, 15311959507488387536999645997508864070728983536008834350091495356187288895669, 21868784207750285500789966411383458123283229821709461239486513907488209131612, 2557951812767345794546586497935135668794151235728750337422671087818929610574, 17473966680863633026932729883592107094006019689381098403121917783363653279463, 14901331443561525513157918825114834523419882075834080639612162148226804890485, 14613854520272564039958655784598244535415456308116984792117554052529004371578, 8723490429628783440793122058769807733413634591172714932615028401405267931255, 11393854498239631803884925965825717915037934904384340905107086220872641315598, 278485928455981470186124998891035321534122251227238192158423900824785413928])
    print("Check still same: ", check_total == old_check_total)
    old_token_total = pairing.FQ12([5085223409847033112576244704505548214947933269251862815176376655942131100429, 20583492038568578046796364956778307070428782128829269303736237702260122876522, 11052855374575774504398087388497019012051684616022016995917360853602629162985, 20365539177933253354138390586322189445176667794792189213530489032481327217720, 8033605651272592282192077611224677394517627893563509026583062490765112230171, 21672464374459474515073189552568308301928896416328846012201671555406659344495, 4948963855221082936706594210530220028377290310338178464056199346690040183775, 6108164392219739408618673376938547932332609850781300305046135154212546802216, 12972658886851434680277516705057298870935211359130360309504525879406966885512, 15918470823564105289793484053385562511418396068403565248396390126102752285692, 7554922427547579017649028561486850031016588137036706219186985428282907619755, 9232433908753067479558011070034885661389414201345604833468618954844772347775])
    print("Token still same: ", token_total == old_token_total)
    assert(check_total == old_check_total)  # give large interrupt
    assert(old_token_total == token_total)
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
    master_keys, check_keys = setup(3, alpha=5818522395588039412954343975486516393552931040546314349540429010151306842406, gamma=21840120018203973380108902518439383386874233938463983100663117878539342073142, beta=[3890197982989915386937907033641443907445334448819903817838634995005371367774, 3377819516658563406193266642509682086057438303973431508351607752416141484415, 2333351816756889978404747124105339972477692632310225610166271688093474752000, 15459408238979867368774029275963471432116994200517072275418098814358363696137, 7968386643605629209226046314496324623085975756046330478632427112169597133338])
    print("GenToken")
    # note: rng for u is re-used in every rule-loop, that is not realistic for system
    test_token = gen_token(master_keys, [1, 1, 1], 3, u=5084097986348390729269908090106955298740040842009692311344139206652509589974)
    print("encrypt checks")
    identify = 5
    check1 = encrypt(check_keys[0], identify, 1, r=13310361639518432155598778816999107675119185980518410883744747962400635549209)
    check2 = encrypt(check_keys[1], identify, 1, r=4708642907422499050704862076428092405590089492351158641052908492133734418081)
    check3 = encrypt(check_keys[2], identify, 1, r=10465556228797287385848073339865451232298354941118980474002801677313279097215)
    print("Check")
    result = test(test_token, 3, check1, check2, check3)
    print("Token = check:    ", result)
    assert(result is False)  # big cheer if otherwise


test_routine()


print("pretest")
# print(int("1000", 2))
# print(prp([2,2,2,3,2,2,2,2,2,2], 8))
