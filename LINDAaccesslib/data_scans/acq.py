import time
import numpy as np


def pop_frame(bridge):
    """
    Pop the selected number of frames stored in the FPGA buffer. No TDI mode.

    :param bridge: Bridge to communicate with dll. (object)
    :return: (ndarray, error)
    """
    error, sampl = bridge.use_pop_frame()

    if error:
        return np.full(14400, 255, dtype=np.uint32), True
    else:
        return sampl, False


def acq(pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap, shell, bridge):
    """
   Send the order to the FPGA to acquire a finit number of frames. No TDI mode.

   :param pulses_width: Pulse width. (uint)
   :param pulses: Number of test pulses. (uint)
   :param timer_reg: Timer regsiter. (uint)
   :param belt_dir: Blet direction. (bool)
   :param test_pulses: Test pulses. (bool)
   :param frames: Number of frames to acquire. (uint)
   :param chips_bitmap: Chips bitmap. (uint)
   :param bridge: Bridge to communicate with dll. (object)
   :param shell: shell. (object)
   :return: Error. (bool)
   """
    tries = 10
    while bridge.use_acq(pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames,
                         chips_bitmap) < 0 and tries != 0:
        shell.warning("Tries: {}".format(tries))
        time.sleep(0.2)
        tries -= 1
        if tries == 1:
            shell.error("Impossible to run correctly acq dll function")
            return True

    return False


def acq_and_pop_data(dac_value, pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap, shell,
                     bridge):
    """
   Integrates adquisition function and pop_data function.

   :param dac_value: Chip regsiter value. (uint)
   :param pulses_width: Pulse width. (uint)
   :param pulses: Number of test pulses. (uint)
   :param timer_reg: Timer regsiter. (uint)
   :param belt_dir: Blet direction. (bool)
   :param test_pulses: Test pulses. (bool)
   :param frames: Number of frames to acquire. (uint)
   :param chips_bitmap: Chips bitmap. (uint)
   :param bridge: Bridge to communicate with dll. (object)
   :param shell: shell. (object)
   :return: Error. (bool)
   """
    bridge.use_reset_buffer()
    acq_error = acq(pulses_width, pulses, timer_reg, belt_dir, test_pulses, frames, chips_bitmap, shell, bridge)
    if acq_error:
        return True, np.full(14400, 255, dtype=np.uint32)
    else:
        summed_data_frame = None

        for frame in range(frames):
            data_frame, error = pop_frame(bridge)
            if error:
                shell.error("Time out poping frame, chip_reg_value = {}".format(dac_value))
                return True, data_frame

            else:
                if frame == 0:
                    summed_data_frame = data_frame
                else:
                    summed_data_frame = np.add(summed_data_frame, data_frame)

        return False, summed_data_frame
