from CallSolidityFunction import split_g1_points, split_g2_points
import py_ecc.bn128 as slow_pairing
import py_ecc.optimized_bn128 as fast_pairing
import ecpairing.ecpairing as whitebox
import EqualityTest


g1points_x = []
g1points_y = []
g2_x_1 = []
g2_x_2 = []
g2_y_1 = []
g2_y_2 = []

# point at infinity for solidity (slowPairing.FQ(0), slowPairing.FQ(0))
# G1_1 = (FQ(0), FQ(0))
# half = fast_pairing.curve_order // 2
# G1_1 = fast_pairing.multiply(fast_pairing.G1, 1)
# G1_2 = fast_pairing.multiply(fast_pairing.G1, -1 % fast_pairing.curve_order)
# G1_3 = fast_pairing.multiply(fast_pairing.G1, -1 % fast_pairing.curve_order)

# G2_1 = fast_pairing.multiply(fast_pairing.G2, 6)
# G2_2 = fast_pairing.multiply(fast_pairing.G2, 3)
# G2_3 = fast_pairing.multiply(fast_pairing.G2, 3)


# Generate values from EqualityTest
n = 5
master_keys, check_keys = EqualityTest.setup(n)
test_token = EqualityTest.gen_token(master_keys, [3 for _ in range(n)], n)

identifier = 5
checks = [EqualityTest.encrypt(check_keys[x], identifier, 3) for x in range(n)]

listG1 = []
listG2 = []
for x in range(n):
    listG1.append(checks[x]['g1_mul_prp_add_ident_hash'])
    listG2.append(test_token[0][x]['u_multiplied'])

for x in range(n):
    listG1.append(checks[x]['r_x_mul'])
    listG2.append(test_token[0][x]['alpha_mul_g2_mul_prp'])

listG1.append(checks[0]['hash_ident'])
listG2.append(test_token[1])

for x in range(len(listG1)):
    if x >= (len(listG1)//2):
        listG1[x] = fast_pairing.neg(listG1[x])

listG1 = list(map(fast_pairing.normalize, listG1))
listG2 = list(map(fast_pairing.normalize, listG2))

g1points_x, g1points_y = split_g1_points(listG1)

g2_x_1, g2_x_2, g2_y_1, g2_y_2 = split_g2_points(listG2)

points_list = [None] * (len(listG1) + len(listG2))  # make empty list of correct size
points_list[::2] = listG1
points_list[1::2] = listG2

result = whitebox.ecpairing_noconv(points_list)
print("Pairing Precompile: ", result)
