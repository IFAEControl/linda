import numpy as np


class ArrayOperations:
    def __init__(self, array):
        self.array = array

    def find_nearest_idx(self, value):
        array = np.asarray(self.array)
        idx = (np.abs(array - value)).argmin()
        return idx

    def numerical_subarray(self, init_val, final_val, val_incr):
        init_idx = self.find_nearest_idx(init_val)
        final_idx = self.find_nearest_idx(final_val)

        steps = (self.array[final_idx] - self.array[init_idx]) / val_incr
        jump_steps = int(np.round((final_idx - init_idx) / steps, decimals=False))
        return init_idx, final_idx, jump_steps


def replace_values(matrix, tuple_pos, old_value, new_value, compare_type):
    try:
        if compare_type == ">=":
            mask = matrix[tuple_pos] >= old_value
        elif compare_type == ">":
            mask = matrix[tuple_pos] > old_value
        elif compare_type == "<=":
            mask = matrix[tuple_pos] <= old_value
        elif compare_type == "<":
            mask = matrix[tuple_pos] < old_value
        else:
            # compare_type == "=="
            mask = matrix[tuple_pos] == old_value

        sub_array = np.where(mask, new_value, matrix[tuple_pos])
        matrix[tuple_pos] = sub_array

        return matrix
    except IndexError:
        raise IndexError


def replace_values_loop(matrix, tuple_pos_of_arrays, old_value, new_value, compare_type):
    for array_pos in tuple_pos_of_arrays:
        matrix = replace_values(matrix, array_pos, old_value, new_value, compare_type)

    return matrix