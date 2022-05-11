def replace_data_in_matrix(in_matrix, new_value_matrix, pos_tuple):
    """
    Replaces data in matrix.

    :param in_matrix: Input matrix. (ndarray)
    :param new_value_matrix: Value to append on matirx. (ndarray)
    :param pos_tuple: position to append the data on the matrix. (tuple)
    :return: (ndarray, error)
    """
    try:
        in_matrix[pos_tuple] = new_value_matrix
        return in_matrix, False
    except ValueError:
        return in_matrix, True


