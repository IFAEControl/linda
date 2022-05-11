import numpy as np


def range_split_IFEED(pixel_ifeed_array):
    """
    Modifies IFEED values, creates range matrix and mask matrix.

    :param pixel_ifeed_array: Pixel ifeed ndarray. (ndarray)
    :return: (ndarray, ndarray, ndarray)
    """
    # 0 a 22
    # 0 a 14 -> +1 -> 1 a 15 => IFEEDRANGE = False
    # 15 a 22 --> -7 --> 8 a 15 => IFEEDRANGE = True
    range_ = np.logical_and(pixel_ifeed_array >= 15, pixel_ifeed_array != -1)
    range2_ = np.logical_and(pixel_ifeed_array < 15, pixel_ifeed_array != -1)
    masked = pixel_ifeed_array == - 1
    pixel_ifeed_array = np.where(masked, 15, pixel_ifeed_array)
    pixel_ifeed_array = np.where(range2_, pixel_ifeed_array + 1, pixel_ifeed_array)
    pixel_ifeed_array = np.where(range_, pixel_ifeed_array - 7, pixel_ifeed_array)
    return pixel_ifeed_array, range_, masked


def range_split_DISC(pixel_ifeed_array):
    """
    Modifies DISC values, creates range matrix and mask matrix.

    :param pixel_ifeed_array: Pixel ifeed ndarray. (ndarray)
    :return: (ndarray, ndarray, ndarray)
    """
    range_ = np.logical_and(pixel_ifeed_array >= 16, pixel_ifeed_array != -1)
    range2_ = np.logical_and(pixel_ifeed_array <= 15, pixel_ifeed_array != -1)

    masked = pixel_ifeed_array == - 1
    pixel_ifeed_array = np.where(masked, 0, pixel_ifeed_array)
    pixel_ifeed_array = np.where(range2_, pixel_ifeed_array, pixel_ifeed_array)
    pixel_ifeed_array = np.where(range_, 31 - pixel_ifeed_array, pixel_ifeed_array)

    return pixel_ifeed_array, range_, masked
