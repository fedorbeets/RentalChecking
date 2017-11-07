import py_ecc.optimized_bn128.optimized_pairing as pairing

# point = (1,2)
# (1,2) is on the curve
# curve is y**2 = x**3 + 3
# where b = 3

# print(py_ecc.bn128.bn128_curve.is_on_curve(point,3))

el_g2 = pairing.G2
#el_g2 = pairing.multiply(el_g2, 5)
print(pairing.normalize(el_g2))
print(pairing.is_on_curve(el_g2, pairing.b2))

el_g1 = pairing.G1
el_g1 = pairing.multiply(el_g1, 10)

print(pairing.normalize(el_g1))
print(pairing.is_on_curve(el_g1, pairing.b))

paired = pairing.pairing(el_g2,el_g1)

print(paired)
print(paired*paired)
print(type(paired))