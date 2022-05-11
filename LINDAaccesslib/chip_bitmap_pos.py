"""
    **Contains the logic for the chip_bitmap conversions.**
"""
import numpy as np

chip_bitmap_default = np.array([1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536,
                                131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432,
                                67108864, 134217728, 268435456, 536870912])


def convert(chip_bitmap, incr):
    """
    Converts chip bitmap value on the corresponds chip bitmap value for each chip.

    :param chip_bitmap:  Chips bitmap. (uint)
    :param incr: Chips increment. (uint)
    :return: (ndarry, ndarray)
    """
    binary_list = [int(c) for c in bin(chip_bitmap)[2:]]
    binary_list = np.flip(binary_list) > 0

    if len(binary_list) < 30:
        app = np.full((30 - len(binary_list),), False)
        binary_list = np.append(binary_list, app)

    out_list = chip_bitmap_default[binary_list]
    pos_list = np.uint32(np.log2(out_list))
    incr_arr = np.multiply(pos_list, incr)

    return out_list, incr_arr
