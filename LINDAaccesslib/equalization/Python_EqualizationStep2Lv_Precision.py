import numpy as np

DISC = 15
N_PIXELS = 160


def get_otp_dac_pos(noise_full_scan, min_threshold, count_cut_high, count_cut_low):
    """
    Finds optimum values of discriminator for each IFEED value in every pixel based upon the counts chart.

    :param noise_full_scan: Matrix containing characterization data with all parameters in the following ranges: [DISC][PIXELS][DAC_VALUES]. (ndarray)
    :param min_threshold: Minimum value of counts above noise level. (uint)
    :param count_cut_high: High cut to determine the optimum dac postion. (uint)
    :param count_cut_low: Low cut to determine the optimum dac postion. (uint)
    :return: ndarray. (ndarray)
    """

    noise_full_scan = np.array(noise_full_scan)
    threshold_dac_counts_mx = np.empty((len(noise_full_scan), len(noise_full_scan[0])))

    if not noise_full_scan.any():
        return 0

    else:
        for pix in range(len(noise_full_scan[0])):
            mask = noise_full_scan[DISC][pix][0:] >= min_threshold
            if not np.all(mask is False):
                try:
                    relative_threshold_pos = np.argmax(np.flip(noise_full_scan[DISC][pix]) > min_threshold)
                    threshold_pos = len(noise_full_scan[DISC][pix]) - relative_threshold_pos
                    threshold_dac_counts_mx[DISC][pix] = threshold_pos

                except (ValueError, IndexError):
                    threshold_dac_counts_mx[DISC][pix] = -1
            else:
                threshold_dac_counts_mx[DISC][pix] = -1

        # Determining the optimum dac position
        arr = np.array(threshold_dac_counts_mx[DISC])
        arr = arr[arr != -1]
        median = np.median(arr)
        data_cut_high = median + count_cut_high
        data_cut_low = median - count_cut_low
        mask = np.logical_or(arr >= data_cut_high, arr <= data_cut_low)
        arr = np.where(mask, np.nan, arr)
        opt_dac_pos = int(np.nanmean(arr))

        return opt_dac_pos


def step2(noise_full_scan, dac_scan, min_threshold, count_factor_noise, opt_dac_pos):
    """
    Finds optimum values of discriminator for each IFEED value in every pixel based upon the counts chart.

    :param noise_full_scan: Matrix containing characterization data with all parameters in the following ranges: [DISC][PIXELS][DAC_VALUES]. (ndarray)
    :param dac_scan: Array containing DAC values in each acq [dac_val] discriminator in each pixel. (ndarray)
    :param min_threshold: Minimum value of counts above noise level. (uint)
    :param count_factor_noise: Count factor noise. (uint)
    :param opt_dac_pos: Optimum dac position. (uint)
    :return: Matrix containing the optimum values of discriminator for each IFEED value in each pixel [PIX]. (ndarray)
    """

    disc_values_max = np.array(noise_full_scan)
    dac_scan_array = np.array(dac_scan)
    opt_dac_count = dac_scan_array[opt_dac_pos]
    threshold_dac_counts_mx = np.empty((len(disc_values_max), len(disc_values_max[0])))
    noise_width_analysis = np.zeros(N_PIXELS)

    if not disc_values_max.any():
        return np.int32(np.full(160, -1))

    else:
        for DISC in range(len(disc_values_max)):
            for pix in range(len(disc_values_max[0])):
                mask = disc_values_max[DISC][pix][0:] >= min_threshold
                if not np.all(mask is False):
                    try:
                        relative_threshold_pos = np.argmax(np.flip(disc_values_max[DISC][pix]) > min_threshold)
                        threshold_pos = len(disc_values_max[DISC][pix]) - relative_threshold_pos
                        threshold_dac_counts_mx[DISC][pix] = dac_scan_array[threshold_pos]

                        # Noise width analysis
                        if DISC == 15:
                            noise_width_analysis[pix] = threshold_pos

                    except (ValueError, IndexError):
                        threshold_dac_counts_mx[DISC][pix] = -1
                else:
                    threshold_dac_counts_mx[DISC][pix] = -1

        # Mask pixels with noise with outlayers
        arr = np.array(noise_width_analysis)
        median = np.median(arr)
        data_cut_high = median + count_factor_noise
        mask_pixels = arr >= data_cut_high
        print(f"Pixels mask in noise count: {np.sum(mask_pixels)}")

        # Check for each IFEED the best DISC value in each pixel.
        threshold_dac_counts_mx_tp = threshold_dac_counts_mx.transpose((1, 0))  # [pix][DISC].
        opt_disc_val_array = np.empty((N_PIXELS,))  # Pixel DISC optimum empty array.

        for pix in range(len(threshold_dac_counts_mx_tp)):
            opt_disc_val_array[pix] = (np.abs(threshold_dac_counts_mx_tp[pix] - opt_dac_count)).argmin()

            if opt_dac_count < threshold_dac_counts_mx_tp[pix][0] or opt_dac_count > threshold_dac_counts_mx_tp[pix][
                len(threshold_dac_counts_mx_tp[0]) - 1]:
                opt_disc_val_array[pix] = -1

        print(f"Pixels mask in out values count: {np.sum(opt_disc_val_array == -1)}")
        # Mask pixels noise out of distribution
        opt_disc_val_array = np.where(mask_pixels, -1, opt_disc_val_array)

        return np.int32(opt_disc_val_array)
