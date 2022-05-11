import numpy as np
from LINDAaccesslib.doc_operations.doc_operations import ManageCsv


def calculate_optimum_dac(folder_path_dac_scan, min_threshold, shell):
    """
    From dac_scan folder get values and calculate gaussian average for each chip

    :param folder_path_dac_scan: Path where dacn scans are saved. (str)
    :param min_threshold: Minimum value of counts above noise level. (uint)
    :param shell: shell. (object)
    :return: Optimum center for each pixel. (ndarray)
    """
    gen_ds = ManageCsv(folder_path_dac_scan)
    csv_array_ds = gen_ds.csv_names_inside_folder()

    ds_csv_names = []
    chips_analized = []

    for chip in range(30):  # range(len(csv_array_stp1) - 1)
        try:
            index = [idx for idx, s in enumerate(csv_array_ds) if 'chip{}_'.format(chip) in s][0]
            ds_csv_names.append(csv_array_ds[index])
            chips_analized.append(chip)
        except IndexError:
            pass

    """DAC_optimum value for each chip"""
    pct = 95  # Percentage to generate cut high and low. If this number is lower there are more nan values.
    bell_center_opt_pos_chip = []
    for doc_name in ds_csv_names:
        # scan_init_val = int(find_between(doc_name, "x", "y"))
        # scan_incr = int(find_between(doc_name, "y", "z"))
        scan_init_val = 24
        scan_incr = 1
        ds_data_csv = gen_ds.extract_df_from_csv(doc_name)
        shell.info(f"Doc_name analized: {doc_name}, scan initail value: {scan_init_val}, scan increment: {scan_incr}")

        bell_center_px = []
        coog_count_mask = ds_data_csv > min_threshold
        if np.sum(coog_count_mask) < 50:
            shell.info(f"File: {doc_name}, most of the values are below min_threshold")
            bell_center_opt_pos_chip.append(0)
        else:
            for pixel in range(len(ds_data_csv)):
                data = ds_data_csv[pixel]
                try:
                    min_pos = np.argmax(data > min_threshold)
                    relative_max_pos = np.argmax(np.flip(data) > min_threshold)
                    max_pos = len(data) - relative_max_pos
                    bell_center_px.append(((max_pos - min_pos) / 2) + min_pos)

                except (ValueError, IndexError):
                    bell_center_px.append(-1)

            bell_center_px = np.array(bell_center_px)
            data_no_bad = np.where(bell_center_px < 1, np.nan, bell_center_px)  # Data with out masked pixels
            mean = np.nanmean(data_no_bad)
            cut_high = mean + ((pct * mean) / 100)
            cut_low = mean - ((pct * mean) / 100)
            data_outlayer = np.where(data_no_bad > cut_high, np.nan, data_no_bad)
            data_outlayer = np.where(data_outlayer < cut_low, np.nan, data_outlayer)
            relative_out = np.nanmean(data_outlayer)
            if not relative_out > 0:
                out = 0
            else:
                out = scan_init_val + (scan_incr * relative_out)
            bell_center_opt_pos_chip.append(out)

    return bell_center_opt_pos_chip


def find_between(s, first, last):
    """ Return characters between two characters, first match."""
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""
