import numpy as np
from LINDAaccesslib.equalization.dac_scan_opt import calculate_optimum_dac
from Excelacceslib.excel_matrix_manage import get_linda_matrix, write_linda_matrix
from LINDAaccesslib.useful_modules.data_replace import replace_data_in_matrix


def optimum_dac_write(folder_path_dac_scan, excel_path, dac, min_threshold, shell):
    """
    Calculates the optimum DAC value for every chip and then substituted the new values on Excel file.

    :param folder_path_dac_scan: Path of the folder where the DAC scan was saved. (str)
    :param excel_path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
    :param dac: Dac position to be analyzed. (uint)
    :param min_threshold:  Minimum value of counts above noise level. (float)
    :param shell: shell. (object)
    :return: Error. (bool)
    """
    dac_value_opt_chip = calculate_optimum_dac(folder_path_dac_scan, min_threshold, shell)
    if len(dac_value_opt_chip) == 0:
        shell.error("Error dac scan folder path, or missing documents inside.")
        return True
    else:
        shell.info(f"Dac optimum values for every chip: {dac_value_opt_chip}")

    """ Getting data form excel """
    try:
        chip_reg, pixel_reg = get_linda_matrix(excel_path)
    except FileNotFoundError:
        return True

    """Modifying chip register data"""
    md_cr = chip_reg
    opt_dac_pos_arr = np.uint32(np.round_(dac_value_opt_chip))
    md_cr, error = replace_data_in_matrix(md_cr, opt_dac_pos_arr, (0, dac))
    shell.info(f"Shape chip_reg: {np.shape(md_cr)}")

    """Saving matrix data"""
    error = write_linda_matrix(excel_path, md_cr, pixel_reg)
    if error:
        return True

    return False
