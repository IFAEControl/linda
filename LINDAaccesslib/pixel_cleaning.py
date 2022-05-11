"""
    **Contains the logic for pixel cleaning.**
"""
import pandas as pd
import numpy as np


def clean_pixels(pixel_reg, acq_file_path, std_high, std_low, dac_x):
    """
    This function masks the pixels out of the selected range.

    :param pixel_reg: Pixel register data. (ndarray)
    :param acq_file_path: Absolute adquisition file path. (str)
    :param std_high: Counts cut high. (uint)
    :param std_low: Counts cut low. (uint)
    :param dac_x: Dac position to be analyzed. (uint)
    :return: Error. (uint)
    """
    acq = pd.read_csv(acq_file_path, header=None).values

    if acq.shape != (8, 600):
        return np.zeros(shape=(44, 30, 8, 20)), 1

    # Generating mask for bad pixels
    arr = acq[acq != 0]
    data_cut_high = std_high
    data_cut_low = std_low
    mask = np.logical_or(acq > data_cut_high, acq < data_cut_low)

    # Merging mask with old values
    excel_position_track = [34, 30, 26, 22, 18, 14]

    mask = mask.reshape((8, 30, 20))
    mask = mask.transpose((1, 0, 2))
    pixel_reg = np.array(pixel_reg)
    dac_x_mask = pixel_reg[excel_position_track[dac_x]]
    or_mask = np.logical_or(dac_x_mask, mask)
    pixel_reg[excel_position_track[dac_x]] = or_mask

    return pixel_reg, 0
