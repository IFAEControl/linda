import numpy as np

N_PIXELS = 160


def step1(tp_full_scan, dac_scan, min_threshold, pct_high, pct_low, std_optimum_factor=3, opt_gain=None):
    """
    Finds optimum values of IFEED for every pixel based upon the counts chart.

    :param tp_full_scan: Matrix containing characterization data with the parameters in the following ranges: [IFEED][PIXELS][DAC_VALUES]. (ndarray)
    :param dac_scan: Array containing DAC positions from the the DAC's characterization. (ndarray)
    :param min_threshold: Minimum value of counts above noise level. (uint)
    :param pct_high: If the iffed gain is higher than the pct + opt_gain, mask this pixel. (uint)
    :param pct_low: If the iffed gain is lower than the pct + opt_gain, mask this pixel. (uint)
    :param std_optimum_factor: It is not used. (float)
    :param opt_gain: Optimum gain for every chip. (uint)
    :return: Array containing best IFEED value for each pixel in case of not fitting the value will be -1.
    """

    full_test_pulse_mx = np.array(tp_full_scan)
    scan_dac_array = np.array(dac_scan)
    pulse_width_mx = np.empty((len(full_test_pulse_mx), N_PIXELS))

    if not full_test_pulse_mx.any():
        return np.int32(np.full(160, -1))

    else:
        for IFEED in range(len(full_test_pulse_mx)):
            for pos in range(len(full_test_pulse_mx[0])):
                mask = full_test_pulse_mx[IFEED][pos] > min_threshold
                if not np.all(mask is False):
                    try:
                        min_pos = np.argmax(full_test_pulse_mx[IFEED][pos] > min_threshold)
                        relative_max_pos = np.argmax(np.flip(full_test_pulse_mx[IFEED][pos]) > min_threshold)
                        max_pos = len(full_test_pulse_mx[IFEED][pos]) - relative_max_pos
                        pulse_width_mx[IFEED][pos] = scan_dac_array[max_pos] - scan_dac_array[min_pos]
                    except (ValueError, IndexError):
                        pulse_width_mx[IFEED][pos] = -1
                else:
                    pulse_width_mx[IFEED][pos] = -1

        pixel_p_wop = np.empty(len(full_test_pulse_mx))  # Pixel PULSE WIDTH optimum, gain optimum.

        for IFEED in range(len(pulse_width_mx)):
            try:
                arr = np.array(pulse_width_mx[IFEED])
                arr = arr[arr != -1]
                median = np.median(arr)
                std = np.std(arr)
                data_cut_high = median + (std_optimum_factor * std)
                data_cut_low = median - (std_optimum_factor * std)
                mask = np.logical_or(arr >= data_cut_high, arr <= data_cut_low)
                arr = np.where(mask, np.nan, arr)
                pixel_p_wop[IFEED] = np.nanmean(arr)

            except IndexError:
                "If in the pulse with calculate there is and error '-1',"
                "the gain optimum calculation will have an error too."
                pass

        if not opt_gain:
            mean_pixel_p_wop = np.mean(pixel_p_wop)  # Check the best IFEED per pixel comparing with the optimum gain.
        else:
            mean_pixel_p_wop = opt_gain

        trans_pulse_width_mx = pulse_width_mx.transpose(1, 0)
        pixel_ifeed_array = np.empty(N_PIXELS)  # Best IFEED in each pixel.

        for pix in range(len(pixel_ifeed_array)):
            iffed_pos = (np.abs(trans_pulse_width_mx[pix] - mean_pixel_p_wop)).argmin()
            pixel_ifeed_array[pix] = iffed_pos

            if trans_pulse_width_mx[pix][iffed_pos] > mean_pixel_p_wop + ((pct_high / mean_pixel_p_wop) * 100) or \
                    trans_pulse_width_mx[pix][iffed_pos] < mean_pixel_p_wop - ((pct_low / mean_pixel_p_wop) * 100):
                pixel_ifeed_array[pix] = -1

        return np.int32(pixel_ifeed_array)


def get_opt_gain_step1(tp_full_scan, dac_scan, min_threshold, std_optimum_factor=3):
    """
    Gets the optimum gain value.

    :param tp_full_scan: Test pulse full scan. (ndarray)
    :param dac_scan: Dac position to be analyzed. (uint)
    :param min_threshold: Minimum value of counts above noise level. (uint)
    :param std_optimum_factor: It is not used. (float)
    :return: (ndarray).
    """
    full_test_pulse_mx = np.array(tp_full_scan)
    scan_dac_array = np.array(dac_scan)
    pulse_width_mx = np.empty((len(full_test_pulse_mx), N_PIXELS))

    if not full_test_pulse_mx.any():
        return 0

    else:
        for IFEED in range(len(full_test_pulse_mx)):
            for pos in range(len(full_test_pulse_mx[0])):
                mask = full_test_pulse_mx[IFEED][pos] > min_threshold
                if not np.all(mask is False):
                    try:
                        min_pos = np.argmax(full_test_pulse_mx[IFEED][pos] > min_threshold)
                        relative_max_pos = np.argmax(np.flip(full_test_pulse_mx[IFEED][pos]) > min_threshold)
                        max_pos = len(full_test_pulse_mx[IFEED][pos]) - relative_max_pos
                        pulse_width_mx[IFEED][pos] = scan_dac_array[max_pos] - scan_dac_array[min_pos]
                    except (ValueError, IndexError):
                        pulse_width_mx[IFEED][pos] = -1
                else:
                    pulse_width_mx[IFEED][pos] = -1

        pixel_p_wop = np.empty(len(full_test_pulse_mx))  # Pixel PULSE WIDTH optimum, gain optimum.

        for IFEED in range(len(pulse_width_mx)):
            try:
                arr = np.array(pulse_width_mx[IFEED])
                arr = arr[arr != -1]
                median = np.median(arr)
                std = np.std(arr)
                data_cut_high = median + (std_optimum_factor * std)
                data_cut_low = median - (std_optimum_factor * std)
                mask = np.logical_or(arr >= data_cut_high, arr <= data_cut_low)
                arr = np.where(mask, np.nan, arr)
                pixel_p_wop[IFEED] = np.nanmean(arr)
            except IndexError:
                "If in the pulse with calcule there is and error '-1', the gain optimum calcule will have an error too."
                pass

        return np.mean(pixel_p_wop)
