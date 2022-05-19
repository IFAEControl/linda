import numpy as np
from LINDAaccesslib.equalization.Python_EqualizationStep1Lv import step1, get_opt_gain_step1
from LINDAaccesslib.equalization.Python_EqualizationStep2Lv import step2
from LINDAaccesslib.equalization import Python_EqualizationStep2Lv_Precision
from LINDAaccesslib.useful_modules.data_replace import replace_data_in_matrix
from LINDAaccesslib.equalization.split_pixel_reg_mx import range_split_IFEED, range_split_DISC
from LINDAaccesslib.doc_operations.doc_operations import ManageCsv
from Excelacceslib.excel_matrix_manage import get_linda_matrix, write_linda_matrix

N_PIXELS = 160


def use_manual_eq_stp1(folder_path_step1, min_threshold, pct_high, pct_low, dac, path, shell):
    """
   Performs the first step for the equalization.

   :param folder_path_step1: Path of the folder where the IFEED scan was saved. (str)
   :param min_threshold: Minimum value of counts above noise level. (float)
   :param pct_high: If the iffed gain is higher than the pct + opt_gain, mask this pixel. (float)
   :param pct_low: If the iffed gain is lower than the pct + opt_gain, mask this pixel. (float)
   :param dac: Select the dac position to be analyzed. (uint)
   :param path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
   :param shell: shell. (object)
   :return: (ndarra, ndarray, ndarray, bool)
   """
    try:
        chip_reg, pixel_reg = get_linda_matrix(path)
    except FileNotFoundError:
        return np.zeros((2, 2, 2), dtype=np.int32), np.full((2, 2, 2), True, dtype=bool), \
               np.full((2, 2, 2), True, dtype=bool), True

    gen_stp1 = ManageCsv(folder_path_step1)
    csv_array_stp1 = gen_stp1.csv_names_inside_folder()

    step1_csv_names = []
    chips_analized = []

    for chip in range(len(pixel_reg[0])):  # range(len(csv_array_stp1) - 1)
        try:
            index = [idx for idx, s in enumerate(csv_array_stp1) if 'chip{}_'.format(chip) in s][0]
            step1_csv_names.append(csv_array_stp1[index])
            chips_analized.append(chip)
        except IndexError:
            pass

    dac_pos_csv_names = csv_array_stp1[[idx for idx, s in enumerate(csv_array_stp1) if 'dac_charac_value_pos' in s][0]]

    # [DAC_VALUES_POSITIONS]
    dac_pos_data_csv = gen_stp1.extract_df_from_csv(dac_pos_csv_names)
    dac_pos_data_csv = dac_pos_data_csv.reshape(-1)

    pixel_ifeed_matrix = []
    pixel_ifeed_range_matrix = []
    masked_pixel_matrix = []
    mean_opt_gain_arr = []

    for doc in step1_csv_names:
        # [IFEED][PIXELS][DAC_VALUES]
        step1_data_csv = gen_stp1.extract_df_from_csv(doc)
        ifeed_values = int((len(step1_data_csv) / N_PIXELS))
        eq_data_stp1 = step1_data_csv.reshape(ifeed_values, N_PIXELS, len(step1_data_csv[0]))

        """Appending opt gain of each pixel"""
        mean_opt_gain_arr.append(get_opt_gain_step1(eq_data_stp1, dac_pos_data_csv, min_threshold))

    """Optimum gain for each chip"""
    shell.info(f"Optimum gain mean for each chip: {mean_opt_gain_arr}")
    arr = np.array(mean_opt_gain_arr)
    arr = np.where(arr > 100, arr, np.nan)
    opt_gain = np.nanmean(arr)
    shell.info(f"Optimum gain mean: {opt_gain}")

    i = 0
    for doc in step1_csv_names:
        # [IFEED][PIXELS][DAC_VALUES]
        step1_data_csv = gen_stp1.extract_df_from_csv(doc)
        ifeed_values = int((len(step1_data_csv) / N_PIXELS))
        eq_data_stp1 = step1_data_csv.reshape(ifeed_values, N_PIXELS, len(step1_data_csv[0]))

        """USING equalization algortim step1"""
        # distribución normal centrada en 200, con dispersión de 100
        pixel_ifeed_array = step1(eq_data_stp1, dac_pos_data_csv, min_threshold, pct_high, pct_low, opt_gain=opt_gain)
        pixel_ifeed, pixel_ifeed_range, masked_pixel = range_split_IFEED(pixel_ifeed_array)
        pixel_ifeed_matrix.append(pixel_ifeed.reshape((8, 20)))
        pixel_ifeed_range_matrix.append(pixel_ifeed_range.reshape((8, 20)))
        masked_pixel_matrix.append(masked_pixel.reshape((8, 20)))
        i += 1

    md_pr = pixel_reg
    iter_ = 0
    pr_mask_array_pos = [34, 30, 26, 22, 18, 14]

    for chip in chips_analized:
        """Modifing pixel register data"""
        md_pr, error = replace_data_in_matrix(md_pr, pixel_ifeed_range_matrix[iter_], (2, chip))
        md_pr, error = replace_data_in_matrix(md_pr, pixel_ifeed_matrix[iter_], (37, chip))
        md_pr, error = replace_data_in_matrix(md_pr, masked_pixel_matrix[iter_], (pr_mask_array_pos[dac], chip))
        iter_ += 1

    """Saving matrix data"""
    error = write_linda_matrix(path, chip_reg, md_pr)
    if error:
        return np.zeros((2, 2, 2), dtype=np.int32), np.full((2, 2, 2), True, dtype=bool), \
               np.full((2, 2, 2), True, dtype=bool), True

    return np.int32(pixel_ifeed_matrix), np.bool_(pixel_ifeed_range_matrix), np.bool_(masked_pixel_matrix), \
           False


def use_manual_eq_stp2(folder_path_step2, min_threshold, dac, path, shell, pct_cut_high, pct_cut_low, factor_std_noise,
                       save_disc_excel_falg):
    """
    Performs the second step for the equalization.

    :param folder_path_step2: Path of the folder where the DISC scan was saved. (str)
    :param min_threshold: Minimum value of counts above noise level. (float)
    :param dac: Dac position to be analyzed. (uint)
    :param path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
    :param pct_cut_high: High cut to determine the optimum dac postion. (float)
    :param pct_cut_low: Low cut to determine the optimum dac postion. (float)
    :param factor_std_noise: Standard deviation factor to mask outlier pixels. (float)
    :param save_disc_excel_falg: If Ture the new DISC values will be replaced in the document. (bool)
    :param shell: shell. (object)
    :return: (ndarra, ndarray, ndarray, bool)
    """
    shell.info(path)
    shell.info(folder_path_step2)
    try:
        chip_reg, pixel_reg = get_linda_matrix(path)
    except FileNotFoundError:
        return np.zeros((2, 2, 2), dtype=np.int32), np.full((2, 2, 2), True, dtype=bool), \
               np.full((2, 2, 2), True, dtype=bool), True

    gen_stp2 = ManageCsv(folder_path_step2)
    csv_array_stp2 = gen_stp2.csv_names_inside_folder()

    step2_csv_names = []
    chips_analized = []

    for chip in range(len(pixel_reg[0])):  # range(len(csv_array_stp1) - 1)
        try:
            index = [idx for idx, s in enumerate(csv_array_stp2) if 'chip{}_'.format(chip) in s][0]
            step2_csv_names.append(csv_array_stp2[index])
            chips_analized.append(chip)
        except IndexError:
            pass

    dac_pos_csv_names = csv_array_stp2[[idx for idx, s in enumerate(csv_array_stp2) if 'dac_charac_value_pos' in s][0]]

    # [DAC_VALUES_POSITIONS]
    dac_pos_data_csv = gen_stp2.extract_df_from_csv(dac_pos_csv_names)
    dac_pos_data_csv = dac_pos_data_csv.reshape(-1)

    pixel_disc_matrix = []
    pixel_disc_range_matrix = []
    masked_pixel_matrix = []
    opt_dac_pos_arr = []

    for doc in step2_csv_names:
        # [DISC][PIXELS][DAC_VALUES]
        step2_data_csv = gen_stp2.extract_df_from_csv(doc)
        disc_values = int((len(step2_data_csv) / N_PIXELS))
        eq_data_stp2 = step2_data_csv.reshape(disc_values, N_PIXELS, len(step2_data_csv[0]))

        """USING equalization algortim step2"""
        # distribución normal centrada en 200, con dispersión de 100
        pixel_ifeed_array, opt_DAC_pos = step2(eq_data_stp2, dac_pos_data_csv, min_threshold,
                                               pct_cut_high, pct_cut_low, factor_std_noise)
        pixel_disc, pixel_disc_range, masked_pixel = range_split_DISC(pixel_ifeed_array)
        pixel_disc_matrix.append(pixel_disc.reshape((8, 20)))
        pixel_disc_range_matrix.append(pixel_disc_range.reshape((8, 20)))
        masked_pixel_matrix.append(masked_pixel.reshape((8, 20)))
        opt_dac_pos_arr.append(opt_DAC_pos)

    md_pr = pixel_reg
    md_cr = chip_reg
    iter_ = 0
    pr_mask_array_pos = [34, 30, 26, 22, 18, 14]
    pr_disc_array_pos = [31, 27, 23, 19, 15, 11]
    pr_pol_array_pos = [32, 28, 24, 20, 16, 12]

    """Modifing chip register data"""
    opt_dac_pos_arr = np.where(np.array(opt_dac_pos_arr) <= 0, 0, opt_dac_pos_arr)
    opt_dac_pos_arr = np.uint32(np.round_(opt_dac_pos_arr))
    shell.info(f"Optimum dac{dac} postion for each xip: {opt_dac_pos_arr}")
    md_cr, error = replace_data_in_matrix(md_cr, opt_dac_pos_arr, (0, dac))
    shell.info(f"Shape chip_reg: {np.shape(md_cr)}")

    if save_disc_excel_falg:
        for chip in chips_analized:
            """Modifing pixel register data"""

            md_pr, error = replace_data_in_matrix(md_pr, pixel_disc_matrix[iter_], (pr_disc_array_pos[dac], chip))
            md_pr, error = replace_data_in_matrix(md_pr, pixel_disc_range_matrix[iter_], (pr_pol_array_pos[dac], chip))
            md_pr, error = replace_data_in_matrix(md_pr, masked_pixel_matrix[iter_], (pr_mask_array_pos[dac], chip))
            iter_ += 1

    """Saving matrix data"""
    error = write_linda_matrix(path, md_cr, md_pr)
    if error:
        return np.zeros((2, 2, 2), dtype=np.int32), np.full((2, 2, 2), True, dtype=bool), \
               np.full((2, 2, 2), True, dtype=bool), True

    return np.int32(pixel_disc_matrix), np.bool_(pixel_disc_range_matrix), np.bool_(masked_pixel_matrix), False


def use_manual_eq_stp2_precision(folder_path_step2, min_threshold, dac, path, count_cut_high, count_cut_low,
                                 count_factor_noise, shell):
    """
    Performs the second step for the equalization in presision mode.

    :param folder_path_step2: Path of the folder where the DISC scan was saved. (str)
    :param min_threshold: Minimum value of counts above noise level. (float)
    :param dac: Dac position to be analyzed. (uint)
    :param path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
    :param count_cut_high: High cut to determine the optimum dac postion. (float)
    :param count_cut_low: Low cut to determine the optimum dac postion. (float)
    :param count_factor_noise: Count increment to mask outlier pixels. (float)
    :param shell: shell. (object)
    :return: (ndarra, ndarray, ndarray, bool)
    """
    try:
        chip_reg, pixel_reg = get_linda_matrix(path)
    except FileNotFoundError:
        return np.zeros((2, 2, 2), dtype=np.int32), np.full((2, 2, 2), True, dtype=bool), \
               np.full((2, 2, 2), True, dtype=bool), True

    gen_stp2 = ManageCsv(folder_path_step2)
    csv_array_stp2 = gen_stp2.csv_names_inside_folder()

    step2_csv_names = []
    chips_analyzed = []

    for chip in range(len(pixel_reg[0])):
        try:
            index = [idx for idx, s in enumerate(csv_array_stp2) if 'chip{}_'.format(chip) in s][0]
            step2_csv_names.append(csv_array_stp2[index])
            chips_analyzed.append(chip)
        except IndexError:
            pass

    dac_pos_csv_names = csv_array_stp2[[idx for idx, s in enumerate(csv_array_stp2) if 'dac_charac_value_pos' in s][0]]

    """ Determine optimum threshold position """
    opt_threshold_pos_arr = []
    for doc in step2_csv_names:
        step2_data_csv = gen_stp2.extract_df_from_csv(doc)
        disc_values = int((len(step2_data_csv) / N_PIXELS))
        eq_data_stp2 = step2_data_csv.reshape(disc_values, N_PIXELS, len(step2_data_csv[0]))
        opt_threshold = Python_EqualizationStep2Lv_Precision.get_otp_dac_pos(eq_data_stp2, min_threshold,
                                                                             count_cut_high, count_cut_low)
        opt_threshold_pos_arr.append(opt_threshold)

    mask = np.array(opt_threshold_pos_arr) < 10
    opt_dac_pos_arr = np.where(mask, np.nan, opt_threshold_pos_arr)
    try:
        opt_dac_pos_val = int(np.nanmean(opt_dac_pos_arr))
    except ValueError:
        opt_dac_pos_val = 0
    shell.info(f"Optimum threshold position array: {opt_threshold_pos_arr}")
    shell.info(f"Optimum threshold mean value: {opt_dac_pos_val}")

    """ Determine disc value per pixel """
    dac_pos_data_csv = gen_stp2.extract_df_from_csv(dac_pos_csv_names)
    dac_pos_data_csv = dac_pos_data_csv.T
    shell.info(f"DAC_pos_data_csv shape: {dac_pos_data_csv.shape}")
    pixel_disc_matrix = []
    pixel_disc_range_matrix = []
    masked_pixel_matrix = []

    chip = 0
    for doc in step2_csv_names:
        shell.info(f"-------- CHIP {chip} ---------")
        step2_data_csv = gen_stp2.extract_df_from_csv(doc)
        disc_values = int((len(step2_data_csv) / N_PIXELS))
        eq_data_stp2 = step2_data_csv.reshape(disc_values, N_PIXELS, len(step2_data_csv[0]))

        pixel_ifeed_array = Python_EqualizationStep2Lv_Precision.step2(eq_data_stp2, dac_pos_data_csv[chip],
                                                                       min_threshold, count_factor_noise,
                                                                       opt_dac_pos_val)
        pixel_disc, pixel_disc_range, masked_pixel = range_split_DISC(pixel_ifeed_array)
        pixel_disc_matrix.append(pixel_disc.reshape((8, 20)))
        pixel_disc_range_matrix.append(pixel_disc_range.reshape((8, 20)))
        masked_pixel_matrix.append(masked_pixel.reshape((8, 20)))
        chip += 1

    md_pr = pixel_reg
    md_cr = chip_reg
    iter_ = 0
    pr_mask_array_pos = [34, 30, 26, 22, 18, 14]
    pr_disc_array_pos = [31, 27, 23, 19, 15, 11]
    pr_pol_array_pos = [32, 28, 24, 20, 16, 12]

    for chip in chips_analyzed:
        """Modifing pixel register data"""

        md_pr, error = replace_data_in_matrix(md_pr, pixel_disc_matrix[iter_], (pr_disc_array_pos[dac], chip))
        md_pr, error = replace_data_in_matrix(md_pr, pixel_disc_range_matrix[iter_], (pr_pol_array_pos[dac], chip))
        md_pr, error = replace_data_in_matrix(md_pr, masked_pixel_matrix[iter_], (pr_mask_array_pos[dac], chip))
        iter_ += 1

    """Saving matrix data"""
    error = write_linda_matrix(path, md_cr, md_pr)
    if error:
        return np.zeros((2, 2, 2), dtype=np.int32), np.full((2, 2, 2), True, dtype=bool), \
               np.full((2, 2, 2), True, dtype=bool), True

    return np.int32(pixel_disc_matrix), np.bool_(pixel_disc_range_matrix), np.bool_(masked_pixel_matrix), False
