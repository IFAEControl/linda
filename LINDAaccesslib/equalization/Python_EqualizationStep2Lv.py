import numpy as np

N_PIXELS = 160


def step2(noise_full_scan, dac_scan, min_threshold, pct_cut_high, pct_cut_low, factor_std_noise):
    """
    Finds optimum values of discriminator for each IFEED value in every pixel based upon the counts chart.

    :param noise_full_scan: Matrix containing characterization data with all parameters in the following ranges: [DISC][PIXELS][DAC_VALUES]. (ndarray)
    :param dac_scan: Array containing DAC positions from the DAC's characterization. (ndarray)
    :param min_threshold: Minimum value of counts above noise level. (uint)
    :param pct_cut_high: High cut to determine the optimum dac postion. (uint)
    :param pct_cut_low: Low cut to determine the optimum dac postion. (uint)
    :param factor_std_noise: Standard deviation factor to mask outlier pixels. (float)
    :return: Matrix containing the optimum values of discriminator for each IFEED value in each pixel [PIX]. (ndarray)
    """

    noise_scan_mx = np.array(noise_full_scan)
    dac_scan_array = np.array(dac_scan)
    medium_dac_pos_mx = np.empty((len(noise_scan_mx), len(noise_scan_mx[0])))
    noise_width_analysis = np.zeros(N_PIXELS)

    if not noise_scan_mx.any():
        return np.int32(np.full(160, -1)), -1

    else:
        c = 0
        for DISC in range(len(noise_scan_mx)):
            for pix in range(len(noise_scan_mx[0])):
                mask = noise_scan_mx[DISC][pix][0:] >= min_threshold
                if not np.all(mask is False):
                    try:
                        min_pos = np.argmax(noise_scan_mx[DISC][pix] > min_threshold)
                        relative_max_pos = np.argmax(np.flip(noise_scan_mx[DISC][pix]) > min_threshold)
                        max_pos = len(noise_scan_mx[DISC][pix]) - relative_max_pos
                        medium_dac_pos_mx[DISC][pix] = ((dac_scan_array[max_pos] - dac_scan_array[min_pos]) / 2) + \
                                                       dac_scan_array[min_pos]

                        # Noise width analysis
                        if DISC == 15:
                            c += 1
                            noise_width_analysis[pix] = (max_pos - min_pos)

                    except (ValueError, IndexError):
                        medium_dac_pos_mx[DISC][pix] = -1
                        c += 1
                else:
                    medium_dac_pos_mx[DISC][pix] = -1

        # Determining the optimum dac position
        arr = np.array(medium_dac_pos_mx[15])
        arr = arr[arr != -1]
        median = np.median(arr)
        data_cut_high = median + pct_cut_high
        data_cut_low = median - pct_cut_low
        mask = np.logical_or(arr >= data_cut_high, arr <= data_cut_low)
        arr = np.where(mask, np.nan, arr)
        opt_dac_pos = np.nanmean(arr)

        # Mask pixels with noise with outlayers
        arr = np.array(noise_width_analysis)
        median = np.median(arr)
        data_cut_high = median + factor_std_noise
        mask_pixels = arr >= data_cut_high

        # Check for each IFEED the best DISC value in each pixel.
        medium_dac_pos_mx_tp = medium_dac_pos_mx.transpose((1, 0))  # [pix][DISC].
        opt_disc_val_array = np.empty((N_PIXELS,))  # Pixel DISC optimum empty array.

        for pix in range(len(medium_dac_pos_mx_tp)):
            if opt_dac_pos < medium_dac_pos_mx_tp[pix][0] \
                    or opt_dac_pos > medium_dac_pos_mx_tp[pix][len(medium_dac_pos_mx_tp[0]) - 1]:
                opt_disc_val_array[pix] = -1
            else:
                opt_disc_val_array[pix] = (np.abs(medium_dac_pos_mx_tp[pix] - opt_dac_pos)).argmin()

        # Mask pixels noise out of distribution
        opt_disc_val_array = np.where(mask_pixels, -1, opt_disc_val_array)

        return np.int32(opt_disc_val_array), opt_dac_pos
