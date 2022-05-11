import numpy as np
import pandas as pd
import datetime
import glob
import os


class RowExtractor:
    def __init__(self, path, row_name_array, sep=","):
        self.path = path
        self.row_name_array = row_name_array
        self.sep = sep

    def normal_ext(self):
        out = []
        ch = pd.read_csv(self.path, sep=self.sep)
        for row_name in self.row_name_array:
            out.append(ch[row_name].values)
        return np.array(out)

    def replace_ext(self, replace_ch, replaced_ch):
        out = []
        ch = pd.read_csv(self.path, sep=self.sep).replace(replace_ch, replaced_ch, regex=True)

        for row_name in self.row_name_array:
            out.append(ch[row_name].values)
        return np.array(out)


class ManageCsv:
    """
    This class manges csv files.
    """
    def __init__(self, folder_path):
        self.folder_path = folder_path + "\\"

    def csv_names_inside_folder(self):
        """
        Gets all the csv files root inside a specific folder.

        :return: root array names. (array)
        """
        return [os.path.basename(x) for x in glob.glob(self.folder_path + '*.csv')]

    def create_folder(self, folder_name):
        """
        Creates a folder in the selected "self.folder_path".

        :param folder_name: New folder name. (str)
        """
        date_time = datetime.datetime.utcnow()
        str_date_time = date_time.strftime("%y_%m_%d__%H_%M_%S")
        self.folder_path = self.folder_path + str_date_time + "_" + folder_name + "\\"

        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

    def doc_creation(self, data_frame, doc_name, index_label=False, header=False, chunksize=100000, encoding='utf-8',
                     disc=False):
        """
        Creates doc on "self.folder_path".

        :param data_frame: Input data frame. (DataFrame)
        :param doc_name: Document name. (str)
        :param index_label: index_label. (bool)
        :param header: header. (bool)
        :param chunksize: chunksize. (uint)
        :param encoding: encoding. (str)
        :param disc: disc. (bool)
        """
        try:
            date_time = datetime.datetime.utcnow()
            str_date_time = date_time.strftime("%H_%M_%S")
            if disc:
                full_path = self.folder_path + str(doc_name) + ".csv"
            else:
                full_path = self.folder_path + str_date_time + "_" + str(doc_name) + ".csv"

            data_frame.to_csv(full_path
                              , header=header
                              , index=index_label
                              , chunksize=chunksize
                              , encoding=encoding)
        except FileNotFoundError:
            print("No such file or directory")

    def createa_data_frame(self, matrix):
        """
        Converts a matirx to DataFrame format.

        :param matrix: Input matrix. (ndarray)
        :return: returns dataframe. (DataFrame)
        """
        data_frame = pd.DataFrame(matrix)  # , columns=array_columns
        return data_frame

    def extract_df_from_csv(self, doc_name, header=None, sep=","):
        """
        Extracts data frame from csv file.

        :param doc_name: Document name. (str)
        :param header: header. (int)
        :param sep: separation. (str)
        :return: Data frame values. (DataFrmae)
        """
        try:
            df = pd.read_csv(self.folder_path + doc_name, header=header, sep=sep)
            return df.values
        except FileNotFoundError:
            return -1