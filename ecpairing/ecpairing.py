from cytoolz import (
    curry,
    pipe,
)

from ecpairing import constants
from ecpairing.exceptions import (
    ValidationError,
    VMError,
)
from ecpairing.padding import (
    pad32,
)
from py_ecc import (
    optimized_bn128 as bn128,
)

ZERO = (bn128.FQ2.one(), bn128.FQ2.one(), bn128.FQ2.zero())
EXPONENT = bn128.FQ12.one()


def ecpairing(computation):
    if len(computation.msg.data) % 192:
        # data length must be an exact multiple of 192
        raise VMError("Invalid ECPAIRING parameters")

    num_points = len(computation.msg.data) // 192
    gas_fee = constants.GAS_ECPAIRING_BASE + num_points * constants.GAS_ECPAIRING_PER_POINT

    computation.gas_meter.consume_gas(gas_fee, reason='ECPAIRING Precompile')

    try:
        result = _ecpairing(computation.msg.data)
    except ValidationError:
        raise VMError("Invalid ECPAIRING parameters")

    if result is True:
        computation.output = pad32(b'\x01')
    elif result is False:
        computation.output = pad32(b'\x00')
    else:
        raise Exception("Invariant: unreachable code path")
    return computation


def _ecpairing(data):
    exponent = bn128.FQ12.one()

    processing_pipeline = (
        _process_point(data[start_idx:start_idx + 192])
        for start_idx
        in range(0, len(data), 192)
    )
    exponent = pipe(bn128.FQ12.one(), *processing_pipeline)

    result = bn128.final_exponentiate(exponent) == bn128.FQ12.one()
    return result


@curry
def _process_point(data_buffer, exponent):
    # changed from _extract_point(data_buffer)
    x1, y1, x2_i, x2_r, y2_i, y2_r = _extract_point(data_buffer)
    p1 = validate_point(x1, y1)

    for v in (x2_i, x2_r, y2_i, y2_r):
        if v >= bn128.field_modulus:
            raise ValidationError("value greater than field modulus")

    fq2_x = bn128.FQ2([x2_r, x2_i])
    fq2_y = bn128.FQ2([y2_r, y2_i])

    if (fq2_x, fq2_y) != (bn128.FQ2.zero(), bn128.FQ2.zero()):
        p2 = (fq2_x, fq2_y, bn128.FQ2.one())
        if not bn128.is_on_curve(p2, bn128.b2):
            raise ValidationError("point is not on curve")
    else:
        p2 = ZERO

    if bn128.multiply(p2, bn128.curve_order)[-1] != bn128.FQ2.zero():
        raise ValidationError("TODO: what case is this?????")

    return exponent * bn128.pairing(p2, p1, final_exponentiate=False)


def _extract_point(data_slice):
    x1_bytes = data_slice[:32]
    y1_bytes = data_slice[32:64]
    x2_i_bytes = data_slice[64:96]
    x2_r_bytes = data_slice[96:128]
    y2_i_bytes = data_slice[128:160]
    y2_r_bytes = data_slice[160:192]

    x1 = big_endian_to_int(x1_bytes)
    y1 = big_endian_to_int(y1_bytes)
    x2_i = big_endian_to_int(x2_i_bytes)
    x2_r = big_endian_to_int(x2_r_bytes)
    y2_i = big_endian_to_int(y2_i_bytes)
    y2_r = big_endian_to_int(y2_r_bytes)

    return x1, y1, x2_i, x2_r, y2_i, y2_r


# insert methods that should have been imported


def validate_point(x, y):
    FQ = bn128.FQ

    #if x >= bn128.field_modulus:
    #    raise ValidationError("Point x value is greater than field modulus")
    #elif y >= bn128.field_modulus:
    #    raise ValidationError("Point y value is greater than field modulus")

    if (x, y) != (0, 0):
        p1 = (FQ(x), FQ(y), FQ(1))
        if not bn128.is_on_curve(p1, bn128.b):
            raise ValidationError("Point is not on the curve")
    else:
        p1 = (FQ(1), FQ(1), FQ(0))

    return p1


def big_endian_to_int(value):
    return int.from_bytes(value, byteorder='big')


@curry
def _process_point_noconv(pointg1, pointg2, exponent):
    # pointg2 is stored as x2,x1,y2,y1
    # changed from _extract_point(data_buffer)
    print("PointG1: ", pointg1)
    print("PointG2: ", "[", pointg2[0].coeffs[1], ",", pointg2[0].coeffs[0], "]",
          pointg2[1].coeffs[1], ",", pointg2[1].coeffs[0], "]")
    x, y = pointg1
    p1 = validate_point(x, y)

    fq2_x, fq2_y = pointg2
    if (fq2_x, fq2_y) != (bn128.FQ2.zero(), bn128.FQ2.zero()):
        p2 = (fq2_x, fq2_y, bn128.FQ2.one())
        if not bn128.is_on_curve(p2, bn128.b2):
            raise ValidationError("point is not on curve")
    else:
        p2 = ZERO

    if bn128.multiply(p2, bn128.curve_order)[-1] != bn128.FQ2.zero():
        raise ValidationError("TODO: what case is this?????")
    pair = bn128.pairing(p2, p1, final_exponentiate=False)
    print("a pairing: ", pair)
    return exponent * pair


# assume data contains list of points (G1,G2,G1,G2 ...)
def ecpairing_noconv(data):
    exponent = bn128.FQ12.one()

    processing_pipeline = (
        _process_point_noconv(data[start_idx], data[start_idx+1])
        for start_idx
        in range(0, len(data), 2)
    )
    exponent = pipe(bn128.FQ12.one(), *processing_pipeline)
    inter_result = bn128.final_exponentiate(exponent)
    print("end result: ", inter_result)
    result = inter_result == bn128.FQ12.one()
    return result
