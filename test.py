import LINDAaccesslib.manage as manage

DLL_PATH = "C:/Users/titoare/Desktop/test/PY_LINDA/linda-lib.dll"

""" Init chip and program values. """
manage.init_power_shell(False, "C:/Users/titoare/Desktop/test/PY_LINDA/LINDAaccesslib/shell/logger2.txt")
ret = manage.init_chips("172.16.17.103", 32000, 32001, DLL_PATH)

path = "C:/Users/titoare/Desktop/test/PY_LINDA/x.xlsx"
chips_bitmap = 0x5
manage.reset_chips()
err = manage.write_register(path, chips_bitmap, 0, 0, 1, 0, 2, 0)
data_chip_reg = manage.full_array_chip_register_read(chips_bitmap)
data_pixel_reg = manage.full_array_pixel_register_read(chips_bitmap)

""" Load normalization factors. """
factors, error = manage.load_csv(
    "C:/Users/titoare/Desktop/IFAE/Control-LINDA/Factors/08_01_51_load_flood_norm_factors.csv")
manage.load_flood_norm_factors(factors, chips_bitmap)


def get_image_no_tdi():
    """ Pop frame no tdi with thest pulses. """
    pulse_width = 1000
    pulses = 20
    time_reg = 3000
    blet_dir = False
    test_pulse = True
    frames = 1
    save_data = False

    manage.set_tdac(0.5)

    _tries = 5
    for i in range(_tries):
        manage.reset_buffer()
        manage.acq(pulse_width, pulses, time_reg, blet_dir, test_pulse, frames, chips_bitmap)

        if save_data:
            manage.save_thread("C:/Users/titoare/Desktop/data/data_saved")

        pop_data, error_data = manage.pop_frames(frames, (0, 2, 1, 3), (6, 8, 600), save_data, 0, 2, 3)
        if not error_data:
            print(pop_data[0, :, 0:40])
            break


def get_image_tdi():
    pulse_width = 1000
    pulses = 20
    time_reg = 3000
    blet_dir = False
    test_pulse = True
    frames = 1
    save_data = False

    manage.set_tdac(0.5)

    """ Pop frame tdi """
    _tries = 5
    for i in range(_tries):
        manage.reset_buffer()
        manage.acq_tdi(pulse_width, pulses, time_reg, blet_dir, test_pulse, frames, chips_bitmap)

        if save_data:
            manage.save_thread("C:/Users/titoare/Desktop/data/data_saved")

        pop_data_tdi, error_data = manage.pop_frame_tdi((3, 0, 1, 2), (6, 8, 600), save_data, 0, 2, 3)
        if not error_data:
            print(pop_data_tdi[0, :, 0:40])
            break


def pop_continous_frames():
    """ Pop contineous frame no tdi with thest pulses. """
    pulse_width = 1000
    pulses = 20
    time_reg = 3000
    blet_dir = False
    test_pulse = True
    save_data = False

    manage.set_tdac(0.5)

    manage.start_acq_con(pulse_width, pulses, time_reg, blet_dir, test_pulse, chips_bitmap)
    if save_data:
        manage.save_thread("C:/Users/titoare/Desktop/data/data_saved")

    for i in range(20):
        pop_data, error_data = manage.pop_frames(1, (0, 2, 1, 3), (6, 8, 600), save_data, 0, 2, 3)
        if not error_data:
            print("-------------------------")
            print(pop_data[0, :, 0:40])
        else:
            print("Error poping frames.")
    manage.stop_acq()
    rem_frames = manage.frames_remaining()
    if rem_frames > 0:
        for i in range(rem_frames - 1):
            pop_data, error_data = manage.pop_frames(1, (0, 2, 1, 3), (6, 8, 600), save_data, 0, 2, 3)
            if not error_data:
                print(pop_data[0, :, 0:40])
            else:
                print("Error poping frames on remaining loop.")
    manage.get_debug_data()
    manage.reset_buffer()


def dac_sacn():
    """ Dac Scan """
    pulse_width = 1000
    pulses = 20
    time_reg = 3000
    blet_dir = False
    test_pulse = True
    frames = 1
    manage.set_tdac(0.5)

    err = manage.dac_scan(path, "C:/Users/titoare/Desktop/data", pulse_width, pulses, time_reg, blet_dir, test_pulse,
                          frames, chips_bitmap, 0, -500, 500, 2)
    print(err)


def disc_scan():
    """ Disc Scan """
    pulse_width = 1000
    pulses = 20
    time_reg = 3000
    blet_dir = False
    test_pulse = True
    frames = 1
    manage.set_tdac(0.5)

    error_disc = manage.disc_charc_no_tdi(path,
                                          "C:/Users/titoare/Desktop/IFAE/Control-LINDA/LV_LINDA/files/characterization/7B.txt",
                                          "C:/Users/titoare/Desktop/data", ["th.V", ], 0.8, 1.3, 0.04, pulse_width,
                                          pulses,
                                          time_reg,
                                          blet_dir, test_pulse, frames, chips_bitmap, 0)
    print(error_disc)


def ifeed_scan():
    """ Ifeed Scan """
    pulse_width = 1000
    pulses = 20
    time_reg = 3000
    blet_dir = False
    test_pulse = True
    frames = 1
    manage.set_tdac(0.5)

    error_iffed = manage.ifeed_charc_no_tdi(path,
                                            "C:/Users/titoare/Desktop/IFAE/Control-LINDA/LV_LINDA/files/characterization/7B.txt",
                                            "C:/Users/titoare/Desktop/data", ["th.V", ], 0.8, 1.3, 0.01, pulse_width,
                                            pulses,
                                            time_reg,
                                            blet_dir, test_pulse, frames, chips_bitmap, 0)
    print(error_iffed)


def disc_scan_precision():
    """ Disc Scan Precision"""
    pulse_width = 1000
    pulses = 20
    time_reg = 3000
    blet_dir = False
    test_pulse = True
    frames = 1
    manage.set_tdac(0.5)

    error_disc = manage.disc_charc_no_tdi_precision(path,
                                                    "C:/Users/titoare/Desktop/data", -500, 500, 10, pulse_width, pulses,
                                                    time_reg,
                                                    blet_dir, test_pulse, frames, chips_bitmap, 0)
    print(error_disc)


def eq_step_1():
    "Equalization step 1"
    pixel_ifeed_matrix, \
    pixel_ifeed_range_matrix, \
    masked_pixel_matrix, \
    step1_err = manage.get_stp1("C:/Users/titoare/Desktop/data/22_05_19__13_53_55_IFEED_scan_no_tdi/merge_data",
                                5, 500, 5, 0, "C:/Users/titoare/Desktop/changes.xlsx")

    print(step1_err)


def eq_step2_precision():
    "Equalization step 2 precision"

    pixel_disc_matrix, pixel_disc_range_matrix, masked_pixel_matrix, error_disc = manage.get_stp2_precision(
        "C:/Users/titoare/Desktop/data/22_05_19__13_57_23_disc_scan_no_tdi/merge_data", 5, 0,
        "C:/Users/titoare/Desktop/changes.xlsx", 500, 5, 200)

    print(error_disc)
