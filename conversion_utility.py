from py_ecc.optimized_bn128.optimized_pairing import normalize


# ORDERING of POINTS:
# Points from python pairing library in G2 are formatted as follows:
# [X_r,X_i][Y_r,Y_i], with the second set of coordinates (as used by solidity library), presented first in the ordering
# FQ2 constructor: [g2_x_r, g2_x_i] [g2_y_r, g2_y_i]
# Solidity pairing library uses: [X_i, X_r] [Y_i, Y_r]

# Everything I write will be formatted as [X_i,X_r][Y_i,Y_r].
# Where the imaginary component is listed first in the tuple and then the real component.
#   Except when the points are pulled from python library, they then have to be reformatted

# Takes a point or list of points in G1 and returns X,Y integers split up so they can be put in arrays
# Converts the ordering of the points from the underlying library ordering to solidity ordering (see above)
# assumes points have been normalized
def split_g1_points(points):
    if isinstance(points, list):
        x = [x.n for (x, y) in points]
        y = [y.n for (x, y) in points]
        return x, y
    if isinstance(points, tuple):
        if len(points) == 3:
            return split_g1_points(normalize(points))
        elif len(points) == 2:
            # Cast to int
            x, y = points
            return x.n, y.n
        else:
            raise TypeError("Expected point in G1")


# Takes a point or points in G2 and returns them split over x1, x2, y1, y2 as integers
def split_g2_points(points):
    if isinstance(points, list):
        xi = [x.coeffs[1] for (x, y) in points]
        xr = [x.coeffs[0] for (x, y) in points]
        yi = [y.coeffs[1] for (x, y) in points]
        yr = [y.coeffs[0] for (x, y) in points]
        # reordering points to our used representation
        return xi, xr, yi, yr
    if isinstance(points, tuple):
        if len(points) == 3:  # point still has x,y,z values from optimized library
            return split_g2_points(normalize(points))
        elif len(points) == 2:
            x, y = points
            # Reordering points to our representation
            return x.coeffs[1], x.coeffs[0], y.coeffs[1], y.coeffs[0]
        else:
            raise TypeError('Expected point in G2')
