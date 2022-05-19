import numpy as np
from Bconvertacceslib.use_linda_data_manager import use_chip_reg_to_pack_data, use_pixel_reg_to_pack_data
from Bconvertacceslib.data_manager import simple_data_unpack
from LINDAaccesslib.data_scans.acq import acq_and_pop_data
from LINDAaccesslib.doc_operations.doc_operations import RowExtractor, ManageCsv
from LINDAaccesslib.data_scans.matrix_operations import ArrayOperations
from LINDAaccesslib.data_scans.use_matrix_operations import pr_range_true, pr_set_disc, cr_set_dac, pr_feed_false_all, \
    pr_feed_true_all, pr_set_ifeed, pr_range_false
from LINDAaccesslib.useful_modules.data_replace import replace_data_in_matrix

ERROR_MAX_ITERATIONS = 20


def IFEED_charac_no_tdi(chip_reg, pixel_reg, dac_name_array, dac_v_ini, dac_v_fi, dac_v_incr, pulses_width, pulses,
                        timer_reg, belt_dir, test_pulses, frames, chips_bitmap, dac_doc_path, folder_path, shell,
                        dac_pos, bridge):
    """
    Performs a IFEED scan and it saves the data adquired on the selected folder_path.

    :param chip_reg: Chip regsiter matrix. (ndarray)
    :param pixel_reg: Pixel regsiter matrix. (ndarray)
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
    :param dac_pos: Dac position to be analyzed. (uint)
    :param shell: shell. (object)
    :param bridge: Bridge to communicate with dll. (object)
    :return: Error. (bool)
    """
    # chip_reg, pixel_reg = (1, 19, 30) (44, 30, 8, 20)

    ext = RowExtractor(dac_doc_path, dac_name_array, sep='\t')
    dac_array_values = ext.replace_ext(',', '.').astype(np.float)

    gen_doc = ManageCsv(folder_path)
    gen_doc.create_folder("IFEED_scan_no_tdi")  # Create folder if not exist

    dac_charact_value_pos = []
    """Finding nearest values in DAC[dac_pos] range"""
    manger = ArrayOperations(dac_array_values[0])
    init_idx, final_idx, jump_steps = manger.numerical_subarray(dac_v_ini, dac_v_fi, dac_v_incr)
    len_value = int((final_idx - init_idx) / jump_steps)
    shell.info("The initail DAC{} value is: {} and the final is:"
               " {} with jumps of {} and len of {}.".format(dac_pos, dac_array_values[0][init_idx],
                                                            dac_array_values[0][final_idx], jump_steps,
                                                            len_value))

    """ ¡¡¡¡¡Here putting the defaul values to the matrix and programing!!!!!"""
    md_pr = pixel_reg
    md_cr = chip_reg

    """Programing chip register"""
    pack_data = use_chip_reg_to_pack_data(md_cr)
    bridge.use_full_array_chip_register_write_all(pack_data, chips_bitmap)
    """Programing pixel register"""
    pack_data = use_pixel_reg_to_pack_data(md_pr)
    bridge.use_full_array_pixel_register_write_all(pack_data, chips_bitmap)

    iter_dac = 0  # DAC iteration

    for IFEED in range(1, 24):
        container = []

        """ ¡¡¡¡¡Here change pixel register matrix, in IFEED positions!!!!!"""
        shell.info("IFEED value {}".format(IFEED))
        if IFEED == 1:
            md_pr = pr_feed_false_all(md_pr)
        elif IFEED == 16:
            md_pr = pr_feed_true_all(md_pr)

        if IFEED > 15:
            IFEED_value = IFEED - 8
        else:
            IFEED_value = IFEED

        md_pr = pr_set_ifeed(md_pr, IFEED_value)
        pack_data = use_pixel_reg_to_pack_data(md_pr)
        bridge.use_full_array_pixel_register_write_all(pack_data, chips_bitmap)
        dac_value = -99
        incr = init_idx
        counter_error = 0
        iter_dac = 0
        while dac_value <= dac_array_values[0][final_idx]:
            if counter_error >= ERROR_MAX_ITERATIONS:
                shell.error("Exit program,  counter_error >= {}".format(ERROR_MAX_ITERATIONS))
                break

            """Loop for each DAC value """
            dac_value = dac_array_values[0][incr]
            dac_charact_value_pos.append(incr)

            """ ¡¡¡¡¡Here changing chip register matrix!!!!!"""
            md_cr = cr_set_dac(md_cr, dac_pos, dac_value)
            pack_data = use_chip_reg_to_pack_data(md_cr)
            bridge.use_full_array_chip_register_write_all(pack_data, chips_bitmap)

            """Making one acq for all chips"""
            summed_data = None
            for i in range(ERROR_MAX_ITERATIONS):
                error, summed_data = acq_and_pop_data(dac_value, pulses_width, pulses, timer_reg, belt_dir,
                                                      test_pulses, frames, chips_bitmap, shell, bridge)
                if not error:
                    break
                else:
                    counter_error += 1

            container.append(summed_data)
            incr += jump_steps
            iter_dac += 1

        shell.info("Iter dac. {}".format(iter_dac))

        list_data = np.reshape(container, -1)
        all_counters_data = simple_data_unpack(list_data, (1, iter_dac, 30, 160, 6))

        if all_counters_data is None:
            return -2, "", 0
        else:

            # [CHIPS][IFEED][DAC_VALUES][PIXELS]
            disc_charac_mx = all_counters_data.transpose((4, 2, 0, 1, 3))[dac_pos]
            data_new = np.flip(disc_charac_mx, 3)
            # [CHIPS][IFEED][DAC_VALUES][PIXELS ROW][PIXEL COLUMNS]
            data_new = np.reshape(data_new, (len(data_new), len(data_new[0]), len(data_new[0][0]), 8, 20))
            data_new = np.flip(data_new, 3)
            # [CHIPS][IFEED][PIXELS ROW][PIXEL COLUMNS][DAC_VALUES]
            data_new = data_new.transpose((0, 1, 3, 4, 2))

            """Generating the corresponding csv"""
            chip_value = 0
            for chip in data_new:
                # [IFEED][PIXELS ROW][PIXEL COLUMNS][DAC_VALUES]
                new_chip_data = chip.reshape((len(chip) * len(chip[0]) * len(chip[0][0])), iter_dac)
                data_frame_ch_v = gen_doc.createa_data_frame(new_chip_data)
                gen_doc.doc_creation(data_frame_ch_v,
                                     "IFEED{}_chip{}_DAC{}_{}_{}_{}_stp1".format(IFEED, chip_value, dac_pos, init_idx,
                                                                                 final_idx, iter_dac))

                chip_value += 1
                # shell.info(np.shape(disc_charac_mx))

    data_frame_dac_pos = gen_doc.createa_data_frame(dac_charact_value_pos[0:iter_dac])
    gen_doc.doc_creation(data_frame_dac_pos, "dac_charac_value_pos")

    return 0, gen_doc.folder_path, 0


def DISC_charac_no_tdi(chip_reg, pixel_reg, dac_name_array, dac_v_ini, dac_v_fi, dac_v_incr, pulses_width, pulses,
                       timer_reg, belt_dir, test_pulses, frames, chips_bitmap, dac_doc_path, folder_path, shell,
                       dac_pos, bridge):
    """
    Performs a DISC scan and it saves the data adquired on the selected folder_path.

    :param chip_reg: Chip regsiter matrix. (ndarray)
    :param pixel_reg: Pixel regsiter matrix. (ndarray)
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
    :param dac_pos: Dac position to be analyzed. (uint)
    :param shell: shell. (object)
    :param bridge: Bridge to communicate with dll. (object)
    :return: Error. (bool)
    """
    # chip_reg, pixel_reg = (1, 19, 30) (44, 30, 8, 20)

    ext = RowExtractor(dac_doc_path, dac_name_array, sep='\t')
    dac_array_values = ext.replace_ext(',', '.').astype(np.float)

    gen_doc = ManageCsv(folder_path)
    gen_doc.create_folder("disc_scan_no_tdi")  # Create folder if not exist

    dac_charact_value_pos = []
    """Finding nearest values in DAC[dac_pos] range"""
    manger = ArrayOperations(dac_array_values[0])
    init_idx, final_idx, jump_steps = manger.numerical_subarray(dac_v_ini, dac_v_fi, dac_v_incr)
    len_value = int((final_idx - init_idx) / jump_steps)
    shell.info("The initail DAC{} value is: {} and the final is:"
               " {} with jumps of {} and len of {}.".format(dac_pos, dac_array_values[0][init_idx],
                                                            dac_array_values[0][final_idx], jump_steps,
                                                            len_value))

    """ ¡¡¡¡¡Here putting the defaul values to the matrix and programing!!!!!"""
    md_pr = pixel_reg
    md_cr = chip_reg

    """Programing chip register"""
    pack_data = use_chip_reg_to_pack_data(md_cr)
    error = bridge.use_full_array_chip_register_write_all(pack_data, chips_bitmap)
    """Programing pixel register one by one, because values are diferent in each chip."""
    pack_data = use_pixel_reg_to_pack_data(md_pr)
    pixel_error = bridge.use_full_array_pixel_register_write(pack_data, chips_bitmap)
    if pixel_error == -1:
        shell.error("Error in one ore more chips pixel reg programing")

    iter_dac = 0  # DAC iteration
    disc_counter = 0

    for sign_disc in range(2):  # For FS = True
        if sign_disc == 1:
            md_pr = pr_range_true(md_pr, dac_pos)
        else:
            md_pr = pr_range_false(md_pr, dac_pos)

        for disc_value in range(16):
            container = []

            if sign_disc == 1:
                disc_value = 15 - disc_value

            shell.info("Disc value {}".format(disc_value))
            dac_value = -99
            incr = init_idx

            """ ¡¡¡¡¡Here changinh pixel register matrix!!!!!"""
            md_pr = pr_set_disc(md_pr, dac_pos, disc_value)
            pack_data = use_pixel_reg_to_pack_data(md_pr)
            pixel_error = bridge.use_full_array_pixel_register_write(pack_data, chips_bitmap)
            if pixel_error == -1:
                shell.error("Error in one ore more chips pixel reg programing")

            iter_dac = 0
            counter_error = 0
            while dac_value <= dac_array_values[0][final_idx]:
                if counter_error >= ERROR_MAX_ITERATIONS:
                    shell.error("Exit program,  counter_error >= {}".format(ERROR_MAX_ITERATIONS))
                    break
                """Loop for each DAC value """
                dac_value = dac_array_values[0][incr]
                dac_charact_value_pos.append(incr)

                """ ¡¡¡¡¡Here changinh chip register matrix!!!!!"""
                md_cr = cr_set_dac(md_cr, dac_pos, dac_value)
                pack_data = use_chip_reg_to_pack_data(md_cr)
                bridge.use_full_array_chip_register_write_all(pack_data, chips_bitmap)

                """Making one acq for all chips"""
                summed_data = None
                for i in range(ERROR_MAX_ITERATIONS):
                    error, summed_data = acq_and_pop_data(dac_value, pulses_width, pulses, timer_reg, belt_dir,
                                                          test_pulses, frames, chips_bitmap, shell, bridge)
                    if not error:
                        break
                    else:
                        counter_error += 1

                container.append(summed_data)
                incr += jump_steps
                iter_dac += 1

            shell.info("Iter dac. {}".format(iter_dac))

            list_data = np.reshape(container, -1)
            all_counters_data = simple_data_unpack(list_data, (1, iter_dac, 30, 160, 6))

            if all_counters_data is None:
                return -2, "", 0
            else:

                # [CHIPS][DISC][DAC_VALUES][PIXELS]
                disc_charac_mx = all_counters_data.transpose((4, 2, 0, 1, 3))[dac_pos]
                data_new = np.flip(disc_charac_mx, 3)
                # [CHIPS][DISC][DAC_VALUES][PIXELS ROW][PIXEL COLUMNS]
                data_new = np.reshape(data_new, (len(data_new), len(data_new[0]),
                                                 len(data_new[0][0]), 8, 20))
                data_new = np.flip(data_new, 3)
                # [CHIPS][DISC][PIXELS ROW][PIXEL COLUMNS][DAC_VALUES]
                data_new = data_new.transpose((0, 1, 3, 4, 2))

                """Generating the corresponding csv"""
                chip_value = 0
                for chip in data_new:
                    # [DISC][PIXELS ROW][PIXEL COLUMNS][DAC_VALUES]
                    new_chip_data = chip.reshape((len(chip) * len(chip[0]) * len(chip[0][0])), iter_dac)
                    data_frame_ch_v = gen_doc.createa_data_frame(new_chip_data)
                    gen_doc.doc_creation(data_frame_ch_v,
                                         "DISC{}_chip{}_DAC{}_{}_{}_{}_stp2".format(disc_counter, chip_value, dac_pos,
                                                                                    init_idx, final_idx, iter_dac))

                    chip_value += 1
            disc_counter += 1

    data_frame_dac_pos = gen_doc.createa_data_frame(dac_charact_value_pos[0:iter_dac])
    gen_doc.doc_creation(data_frame_dac_pos, "dac_charac_value_pos")

    return 0, gen_doc.folder_path, 0


def DISC_charac_no_tdi_precision(chip_reg, pixel_reg, offset_low, offset_high, offset_increment,
                                 pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames,
                                 chips_bitmap, folder_path, shell, dac_pos, bridge):
    """
    Performs an DISC_precision scan and it saves the data adquired on the selected folder_path.

    :param chip_reg: Chip regsiter matrix. (ndarray)
    :param pixel_reg: Pixel regsiter matrix. (ndarray)
    :param folder_path: Folder path where the documents will be created. (str)
    :param pulses_width: Pulse width. (uint)
    :param pulses: Number of test pulses. (uint)
    :param timer_reg: Timer regsiter. (uint)
    :param belt_dir: Blet direction. (bool)
    :param test_pulses: Test pulses. (bool)
    :param frames: Number of frames to acquire. (uint)
    :param chips_bitmap: Chips bitmap. (uint)
    :param dac_pos: Dac position to be analyzed. (uint)
    :param offset_low: Low offset for selected start value. (int)
    :param offset_high: High offset for selected start value. (int)
    :param offset_increment: Incriment value in the range. (uint)
    :param shell: shell. (object)
    :param bridge: Bridge to communicate with dll. (object)
    :return: Error. (bool)
    """

    gen_doc = ManageCsv(folder_path)
    gen_doc.create_folder("disc_scan_no_tdi")  # Create folder if not exist

    dac_charact_value_pos = []

    """Finding nearest values in DAC[dac_pos] range"""
    add_mask = np.array(chip_reg[0][dac_pos]) > 25
    data_in_dac_low = np.add(np.array(chip_reg[0][dac_pos]), offset_low, where=add_mask)
    offset = offset_low * -1
    times_incr = int((offset + offset_high) / offset_increment)
    shell.info(f"Times increment {times_incr}, increment {offset_increment}")

    """ ¡¡¡¡¡Here putting the defaul values to the matrix and programing!!!!!"""
    md_pr = pixel_reg
    md_cr, error = replace_data_in_matrix(chip_reg, data_in_dac_low, (0, dac_pos))

    """Programing chip register"""
    pack_data = use_chip_reg_to_pack_data(md_cr)
    error = bridge.use_full_array_chip_register_write(pack_data, chips_bitmap)
    """Programing pixel register one by one, because values are diferent in each chip."""
    pack_data = use_pixel_reg_to_pack_data(md_pr)
    pixel_error = bridge.use_full_array_pixel_register_write(pack_data, chips_bitmap)
    if pixel_error == -1:
        shell.error("Error in one ore more chips pixel reg programing")

    iter_dac = 0  # DAC iteration
    disc_counter = 0

    for sign_disc in range(2):  # For FS = True
        if sign_disc == 1:
            md_pr = pr_range_true(md_pr, dac_pos)
        else:
            md_pr = pr_range_false(md_pr, dac_pos)

        for disc_value in range(16):
            container = []

            if sign_disc == 1:
                disc_value = 15 - disc_value

            shell.info("Disc value {}".format(disc_value))

            """ ¡¡¡¡¡Here changinh pixel register matrix!!!!!"""
            md_pr = pr_set_disc(md_pr, dac_pos, disc_value)
            pack_data = use_pixel_reg_to_pack_data(md_pr)
            pixel_error = bridge.use_full_array_pixel_register_write(pack_data, chips_bitmap)
            if pixel_error == -1:
                shell.error("Error in one ore more chips pixel reg programing")

            """ Setting chip register to the lower values"""
            md_cr, error = replace_data_in_matrix(chip_reg, data_in_dac_low, (0, dac_pos))

            iter_dac = 0
            counter_error = 0
            for time_incr in range(times_incr):
                if counter_error >= ERROR_MAX_ITERATIONS:
                    shell.error("Exit program,  counter_error >= {}".format(ERROR_MAX_ITERATIONS))
                    break

                """ ¡¡¡¡¡Here changing chip register matrix!!!!!"""
                data_incremented = np.add(md_cr[0][dac_pos], + offset_increment, where=add_mask)
                md_cr, error = replace_data_in_matrix(md_cr, data_incremented, (0, dac_pos))
                pack_data = use_chip_reg_to_pack_data(md_cr)
                bridge.use_full_array_chip_register_write(pack_data, chips_bitmap)

                """Loop for each DAC value """
                dac_value = md_cr[0][dac_pos]
                dac_charact_value_pos.append(data_incremented)

                """Making one acq for all chips"""
                summed_data = None
                for i in range(ERROR_MAX_ITERATIONS):
                    error, summed_data = acq_and_pop_data(dac_value, pulses_width, pulses, timer_reg, belt_dir,
                                                          test_pulses, frames, chips_bitmap, shell, bridge)
                    if not error:
                        break
                    else:
                        counter_error += 1

                container.append(summed_data)
                iter_dac += 1

            shell.info("Iter dac. {}".format(iter_dac))

            list_data = np.reshape(container, -1)
            all_counters_data = simple_data_unpack(list_data, (1, iter_dac, 30, 160, 6))

            if all_counters_data is None:
                return -2, "", 0
            else:

                # [CHIPS][DISC][DAC_VALUES][PIXELS]
                disc_charac_mx = all_counters_data.transpose((4, 2, 0, 1, 3))[dac_pos]
                data_new = np.flip(disc_charac_mx, 3)
                # [CHIPS][DISC][DAC_VALUES][PIXELS ROW][PIXEL COLUMNS]
                data_new = np.reshape(data_new, (len(data_new), len(data_new[0]),
                                                 len(data_new[0][0]), 8, 20))
                data_new = np.flip(data_new, 3)
                # [CHIPS][DISC][PIXELS ROW][PIXEL COLUMNS][DAC_VALUES]
                data_new = data_new.transpose((0, 1, 3, 4, 2))

                """Generating the corresponding csv"""
                chip_value = 0
                for chip in data_new:
                    # [DISC][PIXELS ROW][PIXEL COLUMNS][DAC_VALUES]
                    new_chip_data = chip.reshape((len(chip) * len(chip[0]) * len(chip[0][0])), iter_dac)
                    data_frame_ch_v = gen_doc.createa_data_frame(new_chip_data)
                    gen_doc.doc_creation(data_frame_ch_v,
                                         "DISC{}_chip{}_DAC{}_{}_stp2".format(disc_counter, chip_value, dac_pos,
                                                                                    iter_dac))

                    chip_value += 1
            disc_counter += 1

    DAC_charact_value_pos = np.array(dac_charact_value_pos)
    data_frame_dac_pos = gen_doc.createa_data_frame(DAC_charact_value_pos[0:iter_dac])
    gen_doc.doc_creation(data_frame_dac_pos, "dac_charac_value_pos")

    return 0, gen_doc.folder_path, 0


def dac_scan(chip_reg, pixel_reg, pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames,
             chips_bitmap, folder_path, shell, dac_pos, data_in_dac_low,
             offset_low, offset_high, offset_increment, add_mask, bridge):
    """
    Performs a DAC scan and it saves the data adquired on the selected folder_path.

    :param chip_reg: Chip regsiter matrix. (ndarray)
    :param pixel_reg: Pixel regsiter matrix. (ndarray)
    :param folder_path: Folder path where the documents will be created. (str)
    :param pulses_width: Pulse width. (uint)
    :param pulses: Number of test pulses. (uint)
    :param timer_reg: Timer regsiter. (uint)
    :param belt_dir: Blet direction. (bool)
    :param test_pulses: Test pulses. (bool)
    :param frames: Number of frames to acquire. (uint)
    :param chips_bitmap: Chips bitmap. (uint)
    :param dac_pos: Dac position to be analyzed. (uint)
    :param offset_low: Low offset for selected start value. (int)
    :param offset_high: High offset for selected start value. (int)
    :param offset_increment: Incriment value in the range. (uint)
    :param add_mask: Masked pixels' matrix. (ndarray)
    :param data_in_dac_low: DACs values calculated. (ndarray)
    :param shell: shell. (object)
    :param bridge: Bridge to communicate with dll. (object)
    :return: Error. (bool)
        """
    gen_doc = ManageCsv(folder_path)
    gen_doc.create_folder("dac_scan")  # Create folder if not exist

    container = []
    dac_charact_value_pos = []

    offset = offset_low * -1
    times_incr = int((offset + offset_high) / offset_increment)
    shell.info(f"Times increment {times_incr}, increment {offset_increment}")

    """ ¡¡¡¡¡Here putting the defaul values to the matrix and programing!!!!!"""
    md_pr = pixel_reg
    md_cr, error = replace_data_in_matrix(chip_reg, data_in_dac_low, (0, dac_pos))

    """Programing chip register one by one, because values are diferent in each chip."""
    pack_data = use_chip_reg_to_pack_data(md_cr)
    error = bridge.use_full_array_chip_register_write(pack_data, chips_bitmap)
    """Programing pixel register one by one, because values are diferent in each chip."""
    pack_data = use_pixel_reg_to_pack_data(md_pr)
    pixel_error = bridge.use_full_array_pixel_register_write(pack_data, chips_bitmap)
    if pixel_error == -1:
        shell.error("Error in one ore more chips pixel reg programing")

    iter_dac = 0
    counter_error = 0
    for time_incr in range(times_incr):
        if counter_error >= ERROR_MAX_ITERATIONS:
            shell.error("Exit program,  counter_error >= {}".format(ERROR_MAX_ITERATIONS))
            break

        """Making one acq for all chips"""
        summed_data = None
        for i in range(ERROR_MAX_ITERATIONS):
            error, summed_data = acq_and_pop_data("DAC_SCAN", pulses_width, pulses, timer_reg, belt_dir,
                                                  test_pulses, frames, chips_bitmap, shell, bridge)
            if not error:
                break
            else:
                counter_error += 1

        container.append(summed_data)
        iter_dac += 1

        """ ¡¡¡¡¡Here changing chip register matrix!!!!!"""
        data_incremented = np.add(md_cr[0][dac_pos], + offset_increment, where=add_mask)
        md_cr, error = replace_data_in_matrix(md_cr, data_incremented, (0, dac_pos))
        pack_data = use_chip_reg_to_pack_data(md_cr)
        bridge.use_full_array_chip_register_write(pack_data, chips_bitmap)

        shell.info(f"Actual data in chip_regsiter DAC{dac_pos}: {data_incremented}")

    shell.info("Iter dac. {}".format(iter_dac))

    list_data = np.reshape(container, -1)
    all_counters_data = simple_data_unpack(list_data, (iter_dac, 30, 160, 6))

    if all_counters_data is None:
        return -2, 0, 0
    else:

        # [CHIPS][DAC_VALUES][PIXELS]
        disc_charac_mx = all_counters_data.transpose((3, 1, 0, 2))[dac_pos]
        data_new = np.flip(disc_charac_mx, 2)
        # [CHIPS][DAC_VALUES][PIXELS ROW][PIXEL COLUMNS]
        data_new = np.reshape(data_new, (len(data_new), len(data_new[0]), 8, 20))
        data_new = np.flip(data_new, 2)
        # [CHIPS][PIXELS ROW][PIXEL COLUMNS][DAC_VALUES]
        data_new = data_new.transpose((0, 2, 3, 1))

        """Generating the corresponding csv"""
        chip_value = 0
        for chip in data_new:
            # [PIXELS ROW][PIXEL COLUMNS][DAC_VALUES]
            new_chip_data = chip.reshape((len(chip) * len(chip[0])), iter_dac)
            data_frame_ch_v = gen_doc.createa_data_frame(new_chip_data)
            gen_doc.doc_creation(data_frame_ch_v,
                                 "chip{}_DAC{}_stp2".format(chip_value, dac_pos), disc=True)

            chip_value += 1
            shell.info(np.shape(disc_charac_mx))

        data_frame_dac_pos = gen_doc.createa_data_frame(dac_charact_value_pos[0:iter_dac])
        gen_doc.doc_creation(data_frame_dac_pos, "dac_charac_value_pos", disc=True)

        return 0, data_new, data_frame_dac_pos


