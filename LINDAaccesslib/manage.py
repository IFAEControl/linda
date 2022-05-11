"""
    **This module is the bridge between the GUI and the logic. All these functions are called from LabVIEW interface (GUI).**
"""
import os
import platform
import queue
import threading
import time
import numpy as np
from LINDAaccesslib.data_scans import scans
from LINDAaccesslib.comm_bridge import CommBridge
from LINDAaccesslib.chip_bitmap_pos import convert
from LINDAaccesslib.doc_operations.doc_operations import ManageCsv
from LINDAaccesslib.doc_operations.merge_documents import merge_data
from LINDAaccesslib.equalization.use_equalization import use_manual_eq_stp1, use_manual_eq_stp2, \
    use_manual_eq_stp2_precision
from LINDAaccesslib.equalization.use_dac_scan_opt import optimum_dac_write
from LINDAaccesslib.pixel_cleaning import clean_pixels
from LINDAaccesslib.useful_modules.data_replace import replace_data_in_matrix
from LINDAaccesslib.useful_modules.data_append import append_data_to_csv

from Bconvertacceslib.use_linda_data_manager import use_pack_chip_reg_to_data, \
    use_pack_pixel_reg_to_data, use_chip_reg_to_pack_data, use_pixel_reg_to_pack_data, use_pack_acq_to_data, \
    use_pack_acq_to_data_tdi
from Excelacceslib.excel_matrix_manage import get_linda_matrix, write_linda_matrix

if platform.system() == "Linux":
    from LINDAaccesslib.shell.logger_fake import FAKELOG as LG
else:
    from LINDAaccesslib.shell.logger import LOGPYLV as LG

# Init global objects
shell = LG()  # The shell class is intended to debug the py code from labview GUI.
comm_bridge = CommBridge()
save_queue = queue.Queue()
inst_k2410 = None


# Initialize logger.
def init_power_shell(_from, path):
    """
    Initialize custom logger.

    :param _from: True if you are working from Labview, False if you are working from Python. (bool)
    :param path: Logger absolute path. (str)
    """
    shell.mange_doc(path)
    cmd = "Get-Content {} -wait".format(path)
    shell.create_power_shell(_from, cmd)
    shell.info("Welcome to LINDA, you are in debug mode!!")


def close_power_shell():
    """
    Close logger conection.
    """
    shell.kill_shell()


""" ******************************** Global actions ******************************** """


def init_chips(ip, sync_port, async_port, dll_path):
    """
    Initialize the conection with the FPGA.

    :param ip: Ip address. (str)
    :param sync_port: Syncorn port. (str)
    :param async_port: Asyncorn port. (str)
    :param dll_path:  Absolute dll path. (str)
    :return: If there is a conenction error return negative integer. (int)
    """
    shell.info("Connecting to all the chips")
    shell.info(dll_path)
    try:
        comm_bridge.init_library_connection(ip, sync_port, async_port, dll_path)
        return 1
    except ConnectionError:
        shell.warning("Connection Error with dll")
        return -1


def kill_heart_beat():
    """
    Kill heart beat thread.
    """
    shell.info("Killing heart beat")
    comm_bridge.kill_hearbeat()


def reset_chips():
    """
    Reset all the chips.
    """
    shell.info("Resetting all the chips")
    comm_bridge.return_bridge().use_reset()


def reset_controller():
    """
    Reset FPGA controller.

    :return: Negative integer means error. (int)
    """
    shell.info("Resetting controller")
    return comm_bridge.return_bridge().use_controller_reset()


def close_communication():
    """
    Close the connection with the FPGA.
    """
    shell.info("Close communication!")
    comm_bridge.close_connection()


""" ******************************** Array operations chip reg and pixel reg ******************************** """


def write_register(path, chips_bitmap, dac1, offset_1, dac2, offset_2, dac3, offset_3):
    """
    Loads data from Excel file and program it to chip/pixel registers. Allows to apply an offset to the selected DACs.

    :param path: Excel fiel absoluet phat. (str)
    :param chips_bitmap: Chips bitmap. (uint)
    :param dac1: First dac position. (uint)
    :param offset_1: Count offset. (uint)
    :param dac2: Second dac position. (uint)
    :param offset_2: Count offset. (uint)
    :param dac3: Third dac position. (uint)
    :param offset_3: Count offset. (uint)
    :return: If no error retrun 0. (uint)
    """
    shell.info("Calling write register for pixel and chip config.")

    try:
        chip_reg, pixel_reg = get_linda_matrix(path)
    except FileNotFoundError:
        return 1

    data_in_dac1 = np.add(np.array(chip_reg[0][dac1]), offset_1)
    data_in_dac2 = np.add(np.array(chip_reg[0][dac2]), offset_2)
    data_in_dac3 = np.add(np.array(chip_reg[0][dac3]), offset_3)

    chip_reg, error = replace_data_in_matrix(chip_reg, data_in_dac1, (0, dac1))
    chip_reg, error = replace_data_in_matrix(chip_reg, data_in_dac2, (0, dac2))
    chip_reg, error = replace_data_in_matrix(chip_reg, data_in_dac3, (0, dac3))

    chip_error = full_array_chip_register_write(chip_reg, chips_bitmap)
    pixel_error = full_array_pixel_register_write(pixel_reg, chips_bitmap)

    if chip_error or pixel_error:
        shell.error("Error reading / writing dll full_array_programing_registers")
        return 2
    else:
        return 0


def full_array_chip_register_write(chip_reg, chips_bitmap):
    """
    It programs the chip registers.

    :param chip_reg: Chip_register data. (ndarray)
    :param chips_bitmap: Chips bitmap. (uint)
    :return: If no error it returns False. (bool)
    """
    pack_data = use_chip_reg_to_pack_data(chip_reg)
    error = comm_bridge.return_bridge().use_full_array_chip_register_write(pack_data, chips_bitmap)

    if error == -1:
        shell.error("Error reading writing dll full_array_chip_register_read")
        return True
    else:
        return False


def full_array_pixel_register_write(pixel_reg, chips_bitmap):
    """
    It programs the pixel registers.

    :param pixel_reg: Pixel_register data. (ndarray)
    :param chips_bitmap: Chips bitmap. (uint)
    :return: If no error it returns False. (bool)
    """
    pack_data = use_pixel_reg_to_pack_data(pixel_reg)
    error = comm_bridge.return_bridge().use_full_array_pixel_register_write(pack_data, chips_bitmap)

    if error < 0:
        shell.error("Error reading writing dll full_array_chip_register_read")
        return True
    else:
        return False


def full_array_chip_register_read(chips_bitmap):
    """
    Reads chip_register data from chips.

    :param chips_bitmap: Chips bitmap. (uint)
    :return: (error, ndarray)
    """
    shell.info("Calling full_array_chip_register_read.")
    error, out_array = comm_bridge.return_bridge().use_full_array_chip_register_read(chips_bitmap)

    if error < 0:
        shell.error("Error reading from dll full_array_chip_register_read")
        return True, np.zeros((3, 3, 3), dtype=np.uint32)
    else:
        return False, use_pack_chip_reg_to_data(out_array)


def full_array_pixel_register_read(chips_bitmap):
    """
    Reads pixel_register data from chips.

    :param chips_bitmap: Chips bitmap. (uint)
    :return: (error, ndarray)
    """
    shell.info("Calling full_array_pixel_register_read.")
    error, out_array = comm_bridge.return_bridge().use_full_array_pixel_register_read(chips_bitmap)
    if error < 0:
        shell.error("Error reading from dll full_array_pixel_register_read")
        return True, np.zeros((3, 3, 3, 3), dtype=np.uint32)
    else:
        return False, use_pack_pixel_reg_to_data(out_array)


""" ******************************** Read id and temperatures ********************************"""


def full_array_read_erica_id(chips_bitmap):
    """
    Reads chips ID's.

    :param chips_bitmap: Chips bitmap. (uint)
    :return: (ndarray, error)
    """
    shell.info("Calling full_array_read_id.")
    error, out_array = comm_bridge.return_bridge().use_full_array_read_erica_id(chips_bitmap)
    if error < 0:
        shell.error("Error reading ID")
        return np.zeros(30, dtype=np.uint32), True

    else:
        shell.info("ID: {}".format(out_array))
        return np.array(out_array, dtype=np.uint32), False


def full_array_read_temperature(chips_bitmap):
    """
    Reads chips temperatures code.

    :param chips_bitmap: Chips bitmap. (uint)
    :return:  (ndarray, error)
    """
    shell.info("Calling full_array_read_temperature.")
    error, temp_value = comm_bridge.return_bridge().use_full_array_read_temperature(chips_bitmap)
    shell.info(error)
    shell.info(temp_value)
    expanded_data = np.expand_dims(temp_value, axis=0)
    if error < 0:
        shell.error("Error reading temperature")
        return np.zeros(30, dtype=np.uint32), True

    else:
        shell.info("Temperature value: {}".format(expanded_data))
        return np.array(expanded_data, dtype=np.uint32), False


""" ******************************** Acquisitions functions ********************************"""


def start_acq_con(pulses_width, pulses, timer_reg, belt_dir, test_pulses, chips_bitmap):
    """
    Send the order to the FPGA to start acquiring images and stroring it in the buffer. No TDI mode.

    :param pulses_width: Pulse width. (uint)
    :param pulses: Number of test pulses. (uint)
    :param timer_reg: Timer regsiter. (uint)
    :param belt_dir: Blet direction. (bool)
    :param test_pulses: Test pulses. (bool)
    :param chips_bitmap: Chips bitmap. (uint)
    :return: Error. (bool)
    """
    shell.info("Calling start_acq_con.")
    shell.info("{}_{}_{}_{}_{}_{}".format(pulses_width, pulses, timer_reg, belt_dir, test_pulses, chips_bitmap))
    error = comm_bridge.return_bridge().use_acq_cont(pulses_width, pulses, timer_reg, belt_dir, test_pulses,
                                                     chips_bitmap)
    if error < 0:
        shell.error("Error starting continuous acquisition")
        return True

    else:
        shell.info("Acquisition running.")
        return False


def start_acq_con_tdi(pulses_width, pulses, timer_reg, belt_dir, test_pulses, chips_bitmap):
    """
   Send the order to the FPGA to start acquiring images and stroring it in the buffer. With TDI mode.

   :param pulses_width: Pulse width. (uint)
   :param pulses: Number of test pulses. (uint)
   :param timer_reg: Timer regsiter. (uint)
   :param belt_dir: Blet direction. (bool)
   :param test_pulses: Test pulses. (bool)
   :param chips_bitmap: Chips bitmap. (uint)
   :return: Error. (bool)
   """
    shell.info("Calling start_acq_con.")
    shell.info("{}_{}_{}_{}_{}_{}".format(pulses_width, pulses, timer_reg, belt_dir, test_pulses, chips_bitmap))
    error = comm_bridge.return_bridge().use_acq_cont_tdi(pulses_width, pulses, timer_reg, belt_dir, test_pulses,
                                                         chips_bitmap)
    if error == -1:
        shell.error("Error starting continuous acquisition")
        return True

    else:
        shell.info("Acquisition running.")
        return False


def stop_acq():
    """
    Stops continous adquisition mode.

    :return: Error. (bool)
    """
    shell.info("Calling stop_acq.")
    error = comm_bridge.return_bridge().use_stop_acq()
    if error < 0:
        shell.error("Error stopping acquisition")
        return True

    else:
        shell.info("Acquisition stopped.")
        return False


def acq(pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap):
    """
   Send the order to the FPGA to acquire a finit number of frames. No TDI mode.

   :param pulses_width: Pulse width. (uint)
   :param pulses: Number of test pulses. (uint)
   :param timer_reg: Timer regsiter. (uint)
   :param belt_dir: Blet direction. (bool)
   :param test_pulses: Test pulses. (bool)
   :param frames: Number of frames to acquire. (uint)
   :param chips_bitmap: Chips bitmap. (uint)
   :return: Error. (bool)
   """
    shell.info("Calling normal acq.")
    tries = 10
    while comm_bridge.return_bridge().use_acq(pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames,
                                              chips_bitmap) < 0 and tries != 0:
        shell.warning("Tries: {}".format(tries))
        time.sleep(0.2)
        tries -= 1
        if tries == 1:
            shell.error("Impossible to run correctly acq dll function")
            return True
    return False


def acq_tdi(pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap):
    """
   Send the order to the FPGA to acquire a finit number of frames. With TDI mode.

   :param pulses_width: Pulse width. (uint)
   :param pulses: Number of test pulses. (uint)
   :param timer_reg: Timer regsiter. (uint)
   :param belt_dir: Blet direction. (bool)
   :param test_pulses: Test pulses. (bool)
   :param frames: Number of frames to acquire. (uint)
   :param chips_bitmap: Chips bitmap. (uint)
   :return: Error. (bool)
   """
    tries = 10
    shell.info("Frames: {}".format(frames))
    while comm_bridge.return_bridge().use_acq_tdi(pulses_width, pulses, timer_reg, belt_dir, test_pulses,
                                                  frames, chips_bitmap) < 0 and tries != 0:
        shell.warning("Tries: {}".format(tries))
        time.sleep(0.2)
        tries -= 1
        if tries == 1:
            shell.error("Impossible to run correctly acq tdi dll function")
            return True

    return False


def pop_frames(frames, tuple_transpose, tuple_reshape, save, dac1, dac2, dac3):
    """
    Pop the selected number of frames stored in the FPGA buffer.  No TDI mode.

    :param frames: Number of frames to get. (uint)
    :param tuple_transpose: Tuple to reorder the ndarray. Use -> (0, 2, 1, 3). (tuple)
    :param tuple_reshape: Tuple to reshape the ndarray. Use -> (6, 8, 600). (tuple)
    :param save: Absolute path where the  data will be stored. (str)
    :param dac1: First dac to save. (uint)
    :param dac2: Second dac to save. (uint)
    :param dac3: Third dac to save. (uint)
    :return: (ndarray, Error)
    """
    try:
        summed_data_frame = None

        for frame in range(frames):
            error, data_frame = comm_bridge.return_bridge().use_pop_frame()
            if error:
                shell.error("Error reading from dll pop_frames")
                return np.ones((6, 8, 600), dtype=np.uint32), True

            if frame == 0:
                summed_data_frame = data_frame
            else:
                summed_data_frame = np.add(summed_data_frame, data_frame)

        data_out = use_pack_acq_to_data(summed_data_frame, tuple_transpose, tuple_reshape)

        if save:
            try:
                global save_queue
                save_queue.put([data_out, dac1, dac2, dac3])
            except FileNotFoundError:
                shell.error("File not found!")

        return data_out, False
    except:
        shell.error("Unknown")
        return np.ones((6, 8, 600), dtype=np.uint32), True


def pop_frame_tdi(tuple_transpose, tuple_reshape, save, dac1, dac2, dac3):
    """
    Pop the selected number of frames stored in the FPGA buffer.  No TDI mode.

    :param tuple_transpose: Tuple to reorder the ndarray. Use -> (3, 0, 1, 2). (tuple)
    :param tuple_reshape: Tuple to reshape the ndarray. Use -> (6, 8, 600). (tuple)
    :param save: Absolute path where the  data will be stored. (str)
    :param dac1: First dac to save. (uint)
    :param dac2: Second dac to save. (uint)
    :param dac3: Third dac to save. (uint)
    :return: (ndarray, Error)
    """
    try:
        error, sampl = comm_bridge.return_bridge().use_pop_frame()
        if error:
            shell.error("Error reading pop_frame_tdi")
            return np.ones(tuple_reshape, dtype=np.uint32), True
        else:
            data_out = use_pack_acq_to_data_tdi(sampl, tuple_transpose, tuple_reshape)
            if save:
                try:
                    global save_queue
                    save_queue.put([data_out, dac1, dac2, dac3])
                except FileNotFoundError:
                    shell.error("File not found!")

            return data_out, False
    except:
        shell.error("Unknown")
        return np.ones(tuple_reshape, dtype=np.uint32), True


def save_thread(doc_save_path):
    """
    Saves adquisition data.

    :param doc_save_path: Absolute path. (str)
    """
    threading.Thread(target=append_data_to_csv, args=(save_queue, doc_save_path, shell), daemon=False).start()


""" ******************************** Num Factors ******************************** """


def load_flood_norm_factors(factors_value_mx, chip_bitmap):
    """
    Loads flood normalized factors.

    :param factors_value_mx: Ndarray factors matrix. (ndarray)
    :param chip_bitmap: Chips bitmap. (uint)
    :return: (error, ndarray)
    """
    shell.info("Loading scalar factors!")
    chip_bitmap_array, _ = convert(chip_bitmap, 5)
    shell.info(chip_bitmap_array)
    error_array, acq_out_array = comm_bridge.return_bridge().use_load_flood_norm_factors(factors_value_mx,
                                                                                         chip_bitmap_array)
    return error_array, acq_out_array


""" ******************************** Scans ******************************** """


def dac_scan(path, folder_path, pulses_width, pulses, timer_reg, belt_dir,
             test_pulses, frames, chips_bitmap, dac, offset_low, offset_high, offset_increment):
    """
    Performs a DAC scan and it saves the data adquired on the selected folder_path.

    :param path: Excel fiel absoluet phat. (str)
    :param folder_path: Folder path where the documents will be created. (str)
    :param pulses_width: Pulse width. (uint)
    :param pulses: Number of test pulses. (uint)
    :param timer_reg: Timer regsiter. (uint)
    :param belt_dir: Blet direction. (bool)
    :param test_pulses: Test pulses. (bool)
    :param frames: Number of frames to acquire. (uint)
    :param chips_bitmap: Chips bitmap. (uint)
    :param dac: Dac position to be analyzed. (uint)
    :param offset_low: Low offset for selected start value. (int)
    :param offset_high: High offset for selected start value. (int)
    :param offset_increment: Incriment value in the range. (uint)
    :return: Error. (bool)
    """
    shell.info("Starting dac_scan.")
    try:
        chip_reg, pixel_reg = get_linda_matrix(path)
    except FileNotFoundError:
        return True

    add_mask = np.array(chip_reg[0][dac]) >= offset_low
    data_in_dac_high = np.add(np.array(chip_reg[0][dac]), offset_high, where=add_mask)
    data_in_dac_low = np.add(np.array(chip_reg[0][dac]), offset_low, where=add_mask)

    if offset_low >= offset_high:
        shell.error("Offset low is higher than offset_high")
        return True

    if np.any(data_in_dac_high > 2047):
        shell.error("Some chip register value is higher than 2047")
        return True
    elif np.any(data_in_dac_low < 0):
        shell.error("Some chip register value is lower than 0")
        return True

    error = scans.dac_scan(chip_reg, pixel_reg,
                           pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap,
                           folder_path, shell, dac, data_in_dac_low, offset_low, offset_high,
                           offset_increment, add_mask, comm_bridge.return_bridge())
    shell.error(error[0])
    return False


def disc_charc_no_tdi(path, dac_doc_path, folder_path, dac_name_array, dac_v_ini, dac_v_fi, dac_v_incr, pulses_width,
                      pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap, dac):
    """
    Performs a DISC scan and it saves the data adquired on the selected folder_path.

    :param path: Excel fiel absoluet phat. (str)
    :param dac_doc_path: Absolute path from the characteritzation file. (str)
    :param folder_path: Folder path where the documents will be created. (str)
    :param dac_name_array: On characteritzation file column name to extract. (str)
    :param dac_v_ini: Initial dac value. (float)
    :param dac_v_fi: Final dac value. (float)
    :param dac_v_incr: Dac increment. (flaot)
    :param pulses_width: Pulse width. (uint)
    :param pulses: Number of test pulses. (uint)
    :param timer_reg: Timer regsiter. (uint)
    :param belt_dir: Blet direction. (bool)
    :param test_pulses: Test pulses. (bool)
    :param frames: Number of frames to acquire. (uint)
    :param chips_bitmap: Chips bitmap. (uint)
    :param dac: Dac position to be analyzed. (uint)
    :return: Error. (bool)
    """
    shell.info("Starting disc_charc_no_tdi.")
    try:
        chip_reg, pixel_reg = get_linda_matrix(path)
    except FileNotFoundError:
        return True
    error, out_folder_path, _ = scans.DISC_charac_no_tdi(chip_reg, pixel_reg, dac_name_array, dac_v_ini,
                                                         dac_v_fi, dac_v_incr, pulses_width, pulses, timer_reg,
                                                         belt_dir, test_pulses, frames, chips_bitmap,
                                                         dac_doc_path, folder_path, shell, dac,
                                                         comm_bridge.return_bridge())
    shell.info(out_folder_path)
    shell.error(f"characterization_logic: {error}")
    error = merge_data(out_folder_path)
    shell.error(f"merge_data: {error}")

    return False


def disc_charc_no_tdi_precision(excel_path, folder_path, offset_low, offset_high, offset_increment,
                                pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap, dac):
    """
    Performs an DISC_precision scan and it saves the data adquired on the selected folder_path.

    :param excel_path: Excel fiel absoluet phat. (str)
    :param folder_path: Folder path where the documents will be created. (str)
    :param pulses_width: Pulse width. (uint)
    :param pulses: Number of test pulses. (uint)
    :param timer_reg: Timer regsiter. (uint)
    :param belt_dir: Blet direction. (bool)
    :param test_pulses: Test pulses. (bool)
    :param frames: Number of frames to acquire. (uint)
    :param chips_bitmap: Chips bitmap. (uint)
    :param dac: Dac position to be analyzed. (uint)
    :param offset_low: Low offset for selected start value. (int)
    :param offset_high: High offset for selected start value. (int)
    :param offset_increment: Incriment value in the range. (uint)
    :return: Error. (bool)
    """
    shell.info("Starting disc_charc_no_tdi.")
    try:
        chip_reg, pixel_reg = get_linda_matrix(excel_path)
    except FileNotFoundError:
        return True

    error, out_folder_path, _ = scans.DISC_charac_no_tdi_precision(chip_reg, pixel_reg, offset_low, offset_high,
                                                                   offset_increment, pulses_width, pulses,
                                                                   timer_reg, belt_dir, test_pulses, frames,
                                                                   chips_bitmap, folder_path, shell, dac,
                                                                   comm_bridge.return_bridge())
    shell.info(out_folder_path)
    shell.error(f"characterization_logic: {error}")
    error = merge_data(out_folder_path)
    shell.error(f"merge_data: {error}")

    return False


def ifeed_charc_no_tdi(path, dac_doc_path, folder_path, dac_name_array, dac_v_ini, dac_v_fi, dac_v_incr, pulses_width,
                       pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap, dac):
    """
    Performs a IFEED scan and it saves the data adquired on the selected folder_path.

    :param path: Excel fiel absoluet phat. (str)
    :param dac_doc_path: Absolute path from the characteritzation file. (str)
    :param folder_path: Folder path where the documents will be created. (str)
    :param dac_name_array: On characteritzation file column name to extract. (str)
    :param dac_v_ini: Initial dac value. (float)
    :param dac_v_fi: Final dac value. (float)
    :param dac_v_incr: Dac increment. (flaot)
    :param pulses_width: Pulse width. (uint)
    :param pulses: Number of test pulses. (uint)
    :param timer_reg: Timer regsiter. (uint)
    :param belt_dir: Blet direction. (bool)
    :param test_pulses: Test pulses. (bool)
    :param frames: Number of frames to acquire. (uint)
    :param chips_bitmap: Chips bitmap. (uint)
    :param dac: Dac position to be analyzed. (uint)
    :return: Error. (bool)
    """
    shell.info("Starting ifeed_charc_no_tdi.")
    try:
        chip_reg, pixel_reg = get_linda_matrix(path)
    except FileNotFoundError:
        return True

    error, out_folder_path, _ = scans.IFEED_charac_no_tdi(chip_reg, pixel_reg, dac_name_array, dac_v_ini,
                                                          dac_v_fi, dac_v_incr, pulses_width, pulses, timer_reg,
                                                          belt_dir, test_pulses, frames, chips_bitmap,
                                                          dac_doc_path, folder_path, shell, dac,
                                                          comm_bridge.return_bridge())
    shell.info(out_folder_path)
    shell.error(f"characterization_logic: {error}")
    error = merge_data(out_folder_path)
    shell.error(f"merge_data: {error}")

    return False


""" ******************************** Equalization ******************************** """


def get_stp1(folder_path_step1, min_threshold, pct_high, pct_low, dac, excel_path):
    """
    Performs the first step for the equalization.

    :param folder_path_step1: Path of the folder where the IFEED scan was saved. (str)
    :param min_threshold: Minimum value of counts above noise level. (float)
    :param pct_high: If the iffed gain is higher than the pct + opt_gain, mask this pixel. (float)
    :param pct_low: If the iffed gain is lower than the pct + opt_gain, mask this pixel. (float)
    :param dac: Select the dac position to be analyzed. (uint)
    :param excel_path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
    :return: (ndarra, ndarray, ndarray, bool)
    """
    shell.info("Getting equalization matrix manual step 1")

    pixel_ifeed_matrix, pixel_ifeed_range_matrix, masked_pixel_matrix, error = use_manual_eq_stp1(folder_path_step1,
                                                                                                  min_threshold,
                                                                                                  pct_high, pct_low,
                                                                                                  dac,
                                                                                                  excel_path, shell)

    return pixel_ifeed_matrix, pixel_ifeed_range_matrix, masked_pixel_matrix, error


def get_stp2(folder_path_step2, min_threshold, dac, excel_path, pct_cut_high, pct_cut_low, factor_std_noise,
             save_disc_excel_falg):
    """
    Performs the second step for the equalization.

    :param folder_path_step2: Path of the folder where the DISC scan was saved. (str)
    :param min_threshold: Minimum value of counts above noise level. (float)
    :param dac: Dac position to be analyzed. (uint)
    :param excel_path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
    :param pct_cut_high: High cut to determine the optimum dac postion. (float)
    :param pct_cut_low: Low cut to determine the optimum dac postion. (float)
    :param factor_std_noise: Standard deviation factor to mask outlier pixels. (float)
    :param save_disc_excel_falg: If Ture the new DISC values will be replaced in the document. (bool)
    :return: (ndarra, ndarray, ndarray, bool)
    """
    shell.info("Getting equalization matrix manual step 2")

    pixel_disc_matrix, pixel_disc_range_matrix, masked_pixel_matrix, error = use_manual_eq_stp2(folder_path_step2,
                                                                                                min_threshold,
                                                                                                dac,
                                                                                                excel_path,
                                                                                                shell,
                                                                                                pct_cut_high,
                                                                                                pct_cut_low,
                                                                                                factor_std_noise,
                                                                                                save_disc_excel_falg)
    return pixel_disc_matrix, pixel_disc_range_matrix, masked_pixel_matrix, error


def get_stp2_precision(folder_path_step2, min_threshold, dac, excel_path, count_cut_high, count_cut_low,
                       count_factor_noise):
    """
    Performs the second step for the equalization in presision mode.

    :param folder_path_step2: Path of the folder where the DISC scan was saved. (str)
    :param min_threshold: Minimum value of counts above noise level. (float)
    :param dac: Dac position to be analyzed. (uint)
    :param excel_path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
    :param count_cut_high: High cut to determine the optimum dac postion. (float)
    :param count_cut_low: Low cut to determine the optimum dac postion. (float)
    :param count_factor_noise: Count increment to mask outlier pixels. (float)
    :return: (ndarra, ndarray, ndarray, bool)
    """
    shell.info("Getting equalization matrix manual step 2")

    pixel_disc_matrix, pixel_disc_range_matrix, masked_pixel_matrix, error = \
        use_manual_eq_stp2_precision(folder_path_step2, min_threshold, dac, excel_path, count_cut_high, count_cut_low,
                                     count_factor_noise, shell)

    return pixel_disc_matrix, pixel_disc_range_matrix, masked_pixel_matrix, error


def get_optimum_dac_write(folder_path_dac_sacan, excel_path, dac, min_threshold):
    """
    Calculates the optimum DAC value for every chip and then substituted the new values on Excel file.

    :param folder_path_dac_sacan: Path of the folder where the DAC scan was saved. (str)
    :param excel_path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
    :param dac: Dac position to be analyzed. (uint)
    :param min_threshold:  Minimum value of counts above noise level. (float)
    :return: Error. (bool)
    """
    shell.info("Getting optimum dac for step 2 precision")
    error = optimum_dac_write(folder_path_dac_sacan, excel_path, dac, min_threshold, shell)
    return error


""" ******************************** Pixel Cleaning ******************************** """


def pixel_cleaning(excel_path, acq_file_path, std_high, std_low, dacx):
    """
    This function masks the pixels out of the selected range.

    :param excel_path: Excel file absolute path where the data is taken and then substituted with the new values. (str)
    :param acq_file_path: Absolute adquisition file path. (str)
    :param std_high: Counts cut high. (uint)
    :param std_low: Counts cut low. (uint)
    :param dacx: Dac position to be analyzed. (uint)
    :return: Error. (uint)
    """
    shell.info("Start pixel cleaning!")

    try:
        chip_reg, pixel_reg = get_linda_matrix(excel_path)

    except FileNotFoundError:
        shell.error("File not found.")
        return 1

    pixel_reg, error = clean_pixels(pixel_reg, acq_file_path, std_high, std_low, dacx)

    if error == 1:
        shell.error("ACQ file shape != (8, 600)")
        return 2

    w_error = write_linda_matrix(excel_path, chip_reg, pixel_reg)

    if w_error:
        shell.error("Error writting new matrix to excel file.")
        return 3
    else:
        shell.info("Operation works succesfully.")
        return 0


""" ******************************** General operations ******************************** """


def write_linda_mx(chip_reg, pixel_reg, path):
    """
    Writes chip and pixel registers data on excel file.

    :param chip_reg: Chip register data. (ndarray)
    :param pixel_reg: pixel register data. (ndarray)
    :param path: Absolut path excel file. (str)
    :return: Error. (bool)
    """
    # chipreg matrix = (1, 15, 30)
    # pixelreg matrix = (3, 30, 8, 20)
    pixel_reg_trans = np.array(pixel_reg, dtype=np.uint32).transpose((3, 0, 1, 2))
    shell.info("Starting write_excel_matrix process... Called from: {}".format(__name__))
    shell.info("Received chip reg matrix with size: {}".format(np.shape(chip_reg)))
    shell.info("Received pixel reg matrix with size: {}".format(np.shape(pixel_reg_trans)))
    error = write_linda_matrix(path, chip_reg, pixel_reg_trans)
    return error


def convert_matrix(matrix, tuple_transpose, tuple_reshape):
    """
    Gets ndarray and then transpose it and reshape it.

    :param matrix: In ndarray. (ndarry)
    :param tuple_transpose: Tuple transpose. (tuple)
    :param tuple_reshape:  Tuple reshape. (tuple)
    :return: Error. (boo)
    """
    tr = matrix.transpose(tuple_transpose).reshape(tuple_reshape)
    container = np.zeros(tuple_reshape, dtype=np.uint32)
    out = np.where(container >= 0, tr, container)
    return out


def set_hv(hv_value):
    """
    Programs high voltage reigster on FPGA.

    :param hv_value: High voltage value. (float)
    :return: Error. (bool)
    """
    shell.info("Starting set_hv")
    error = comm_bridge.return_bridge().use_set_hv(hv_value)
    shell.warning(error)
    return error


def get_debug_data():
    """
    Prints adquisition debug data.
    """
    w = comm_bridge.return_bridge().use_get_write_frame()
    r = comm_bridge.return_bridge().use_get_read_frame()
    e = comm_bridge.return_bridge().use_get_element_counter()
    shell.info(w)
    shell.info(r)
    shell.info(e)


def frames_remaining():
    """
    Returns number of frames.

    :return: Number of frames. (uint)
    """
    frames = comm_bridge.return_bridge().use_get_element_counter()
    shell.info("The number of frames remaining in the buffer are: {}".format(frames))
    return frames


def set_tdac(tdac_value):
    """
    Programs tdac reigster on FPGA.

    :param tdac_value: Tdac value. (float)
    :return: Error. (bool)
    """
    shell.info("Starting set_tdac")
    error = comm_bridge.return_bridge().use_set_tdac(tdac_value)
    shell.warning(error)
    return error


def get_all_regs():
    """
    Returns all regsites from adquisition.

    :return: (ndarray)
    """
    shell.info("Starting get_all_regs")
    return comm_bridge.return_bridge().use_get_all_regs()


def reset_buffer():
    """
    Resets the FPGA buffer.
    """
    shell.info("Reseting the buffer!")
    error = comm_bridge.return_bridge().use_reset_buffer()


def load_csv(doc_path):
    """
    Loads a csv file from path.

    :param doc_path: Absolute csv file path. (str)
    :return: (ndarray, bool)
    """
    shell.info("Starting load_csv")
    doc_name = os.path.basename(doc_path)
    folder_path = os.path.dirname(doc_path)

    gen = ManageCsv(folder_path)
    df = gen.extract_df_from_csv(doc_name)

    if type(df) == int:
        return np.zeros((30, 120), dtype=np.float64), True
    else:
        container = np.zeros(df.shape, dtype=np.float64)
        out = np.where(container == 0, df, container)
        shell.info(out.shape)
        return out, False


def merge_two_mask(excel_path, dac_x, dac_y):
    """
    Merge on Excel file 2 selected mask registers.

    :param excel_path: Absolute Excel file path. (str)
    :param dac_x: Dac position to be merged. (uint)
    :param dac_y: Dac position to be merged. (uint)
    :return: Error. (uint)
    """
    shell.info(f"Merge DAC{dac_x} mask and DAC{dac_y} mask")

    try:
        chip_reg, pixel_reg = get_linda_matrix(excel_path)

    except FileNotFoundError:
        shell.error("File not found.")
        return 1

    try:
        excel_position_track = [34, 30, 26, 22, 18, 14]
        dacx_mask = pixel_reg[excel_position_track[dac_x]]
        dacy_mask = pixel_reg[excel_position_track[dac_y]]
        or_mask = np.logical_or(dacx_mask, dacy_mask)
        pixel_reg[excel_position_track[dac_x]] = or_mask
        pixel_reg[excel_position_track[dac_y]] = or_mask
    except:
        shell.error("Problem merging two matrix.")
        return 2

    w_error = write_linda_matrix(shell, excel_path, chip_reg, pixel_reg)

    if w_error:
        shell.error("Error writing new matrix to excel file.")
        return 3
    else:
        shell.info("Operation works successfully.")
        return 0

# def init_k2410(gpib_str):
#     err
#     shell.info("Initialize connection with KEITHLEY 2410")
#     global inst_k2410
#     try:
#         inst_k2410 = K2410(gpib_str)
#         inst_k2410.init_connection()
#         return False
#     except Exception as e:
#         shell.error(e)
#         return True
#
#
# def close_k2410():
#     err
#     shell.info("Close connection with KEITHLEY 2410.")
#     global inst_k2410
#     inst_k2410.close_connection()

# """ ******************************** XRAY ******************************** """
#
#
# def xray_process(iter_get_data, std_multy, pulses_width, pulses, timer_reg, belt_dir,
#                  test_pulses, frames, chips_bitmap, folder_path):
#     shell.info("Determining outlier_pixels and first scalar factors!")
#
#     TDI = False
#     pixel_reg = full_array_pixel_register_read(chips_bitmap)
#     pixel_reg = np.transpose(pixel_reg, (3, 0, 1, 2))
#
#     chips_scalar_factor, mask_outlier_pixels = xray(iter_get_data, std_multy, pulses_width, pulses, timer_reg,
#                                                     belt_dir, test_pulses, frames, chips_bitmap, TDI, shell)
#
#     error = save_scalar_factors(folder_path, chips_scalar_factor)
#     if error:
#         shell.error("Error saving .csv scalar factors")
#
#     shell.warning(mask_outlier_pixels[0][0])
#     shell.warning(mask_outlier_pixels[0][1])
#     shell.warning(mask_outlier_pixels[0][2])
#     error = mask_pixel_reg(pixel_reg, mask_outlier_pixels)
#     if error:
#         shell.error("Error writsing new values to the pixel register")
#         return True
#     else:
#         return False
#
#
# def xray_process_tdi(iter_get_data, std_multy, pulses_width, pulses, timer_reg, belt_dir,
#                      test_pulses, frames, chips_bitmap, folder_path):
#     shell.info("Determining outlier_pixels and first scalar factors!")
#
#     TDI = True
#     chips_scalar_factor, mask_outlier_pixels = xray(iter_get_data, std_multy, pulses_width, pulses, timer_reg,
#                                                     belt_dir, test_pulses, frames, chips_bitmap, TDI, shell)
#
#     error = save_scalar_factors(folder_path, chips_scalar_factor)
#     if error:
#         shell.error("Error saving .csv scalar factors")
#         return True
#     else:
#         return False
