import glob
import os


def merge_data(folther_path):
    """
    Gets characterization data files and merge it in a specific format.

    :param folther_path: Absolute path of characterization scans. (str)
    :return: Error. (int)
    """
    chips_arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
                 28, 29]

    try:
        try:
            save_data_path = folther_path + "merge_data/"
            os.mkdir(save_data_path)

            "Moving a file"
            file_path_arr = glob.glob(folther_path + "*dac_charac_value_pos*")
            os.rename(file_path_arr[0], save_data_path + "dac_charac_value_pos.csv")

            for chip in chips_arr:
                path_arr = glob.glob(folther_path + "*_chip{}_*".format(chip))
                if len(path_arr) == 0:
                    print("files not found")
                else:
                    sorted_path_arr = sorted(path_arr)

                    # Open file3 in write mode

                    with open(save_data_path + f'md_chip{chip}_new.csv', 'w') as outfile:
                        # Iterate through list
                        for names in sorted_path_arr:
                            with open(names) as infile:
                                outfile.write(infile.read())

            return 0

        except FileExistsError:
            print("Folder already exist")
            return -2
    except FileNotFoundError:
        print("File not found")
        return -1
