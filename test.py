import numpy as np
import LINDAaccesslib.manage as manage

DLL_PATH = "C:/Users/titoare/Desktop/test/PY_LINDA/linda-lib.dll"

# def test_ifeed_charc_no_tdi():
#     manage.init_power_shell(False, "C:/Users/titoare/Desktop/test/PY_LINDA/LINDAaccesslib/shell/logger.txt")
#     ret = manage.init_chips("172.16.17.103", 32000, 32001, DLL_PATH)
#     if ret < 0:
#         print("Error in registration with dll")
#     else:
#         # dac_name_array = ["th.V", ]  # ["DAC0", "DAC1", "DAC2", "DAC3", "DAC4", "DAC5"]
#         # dac_doc_path = "C:/Users/IFAE/Desktop/ControlTeam/Control-LINDA/LV_LINDA/files/characterization/7B.txt"
#         # folder_path = "C:/Users/IFAE/Desktop/DocGen/"  # Select a folther were the documantation is saved.
#         # config_xls_parth = "C:/Users/IFAE/Desktop/ControlTeam/Control-LINDA/LV_LINDA/files/"
#         # chip_bitmap = 0x3FFFFFFE
#         # frames = 2
#         # time_reg = 3000
#         #
#         # manage.ifeed_charc_no_tdi(config_xls_parth, dac_doc_path, folder_path,
#         #                           dac_name_array, 0.75, 1, 0.003, 1000, 0, time_reg, False, False, frames, chip_bitmap,
#         #                           1)
#         manage.close_communication()
#         manage.kill_heart_beat()

manage.init_power_shell(False, "C:/Users/titoare/Desktop/test/PY_LINDA/LINDAaccesslib/shell/logger.txt")
ret = manage.init_chips("172.16.17.103", 32000, 32001, DLL_PATH)

path = "C:/Users/titoare/Desktop/test/PY_LINDA/x.xlsx"
chips_bitmap = 0x5
err = manage.write_register(path, chips_bitmap, 0, 0, 1, 0, 2, 0)
data = manage.full_array_chip_register_read(chips_bitmap)

# frames = 1
# # manage.save_thread("C:/Users/titoare/Desktop/test/PY_LINDA/save_acq.csv")
# manage.reset_buffer()
# manage.acq(300, 20, 1000, False, True, frames, chips_bitmap)
# out = manage.pop_frames(frames, (0, 2, 1, 3), (6, 8, 600), False, 0, 1, 2)
