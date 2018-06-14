from collections import defaultdict
import py_ecc.optimized_bn128.optimized_pairing as pairing
import conversion_utility

dist = defaultdict(int)

number_of_points = int(1E5)

# No easy way to distinguish G1 or G2 points,
#   so you will have to comment out the code with G1 in it and uncomment the code with G2 to switch between the two

# current_point = pairing.G1
current_point = pairing.G2
# Seems to be around 0.0044 chance of 00 byte, or 1/225 for G1.


def analyze_distribution(point, dist):
    # chop up point
    string = "{0:x}".format(point)
    data = string.zfill(64)
    for j in range(0, len(data), 2):
        byte = data[j:j + 2]
        dist[byte] += 1


def next_point(point):
    # return pairing.add(point, pairing.G1)
    # return pairing.add(point, pairing.G2)
    return pairing.multiply(current_point, 3)



for i in range(number_of_points):
    # point_x, point_y = conversion_utility.split_g1_points(current_point)
    # analyze_distribution(point_x, dist)
    # analyze_distribution(point_y, dist)
    point_x1, point_x2, point_y1, point_y2 = conversion_utility.split_g2_points(current_point)
    analyze_distribution(point_x1, dist)
    analyze_distribution(point_x2, dist)
    analyze_distribution(point_y1, dist)
    analyze_distribution(point_y2, dist)
    current_point = next_point(current_point)
    if i % (number_of_points//10) == 0:
        print("Got to: ", i)

total_values = 0
for k, v in sorted(dist.items(), key=lambda p: p[1], reverse=True):
    print(k, v)
    total_values += v


print("Percent '00': ", dist['00']/total_values)
