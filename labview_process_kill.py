import os


def pkill(process_name):
    """Kill a windows process"""
    os.system('taskkill /f /im ' + process_name)
