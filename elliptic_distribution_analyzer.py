from collections import defaultdict
import py_ecc.optimized_bn128.optimized_pairing as pairing
import conversion_utility
import examine_trans_logs

dist = defaultdict(int)

number_of_points = int(1E6)

current_point = pairing.G1


def analyze_distribution(point, dist):
    # chop up point
    string = "{0:x}".format(point)
    data = string.zfill(64)
    for j in range(0, len(data), 2):
        byte = data[j:j + 2]
        dist[byte] += 1


def next_point(current_point):
    #return pairing.add(current_point, pairing.G1)
    return pairing.multiply(current_point, 3)


for i in range(number_of_points):
    point_x, point_y = conversion_utility.split_g1_points(current_point)
    analyze_distribution(point_x, dist)
    analyze_distribution(point_y, dist)
    current_point = next_point(current_point)
    if i % (number_of_points//10) == 0:
        print("Got to: ", i)

total_values = 0
for k, v in sorted(dist.items(), key=lambda p: p[1], reverse=True):
    print(k, v)
    total_values += v


print(dist['00']/total_values)