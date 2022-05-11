"""**This submodel is to debug labview(windows) and python node**"""
import logging
import os
import subprocess
from colorlog import ColoredFormatter


class LOGPYLV:
    """
       This object only works with windows 10. With windos PowerShell.
    """
    def __init__(self):
        self.shell = None  # Where the power_shel is instanced
        self.logger = None
        self.logfile = None

    def mange_doc(self, path):
        """
        Initializes the logger.

        :param path: Absolue path where the logg is going to be created.
        """
        self.logfile = path
        # Generating log file for labview-python debug
        if os.path.exists(self.logfile):
            os.remove(self.logfile)
        else:
            print("The file does not exist")

        logging.basicConfig(filename=self.logfile,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
        self.logger = logging.getLogger("Python-Labview: ")

    def create_power_shell(self, _from, cmd):
        """
        Initialize the PowerShell on Windows.

        :param _from: If False, the PowerShell it will not be displayed. (bool)
        :param cmd: Especial command to initialize PowerShell. (str)
        """
        if _from:   # If you want to display the windows power shell
            formatter = self.foramt_color()
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            c = "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
            self.logger.addHandler(handler)
            self.shell = subprocess.Popen([c, "-Command", cmd], shell=False,
                                          creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:       # If is not necessary to dispaly th windows power shell
            formatter = self.foramt_color()
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def foramt_color(self):
        """
        Initializes the formmater for the logg.

        :return: Formatter object. (object)
        """
        foramtter = ColoredFormatter("%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s", log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }, secondary_log_colors={})
        return foramtter

    def info(self, msg):
        """
        Displays on the logg an informative message.

        :param msg: Input string. (str)
        """
        self.logger.info(msg)

    def error(self, msg):
        """
        Displays on the logg an error message.

        :param msg: Input string. (str)
        """
        self.logger.error(msg)

    def warning(self, msg):
        """
        Displays on the logg a warning message.

        :param msg: Input string. (str)
        """
        self.logger.warning(msg)

    def kill_shell(self):
        """
        Terminates the shell.
        """
        del self.logger
        self.shell.terminate()
