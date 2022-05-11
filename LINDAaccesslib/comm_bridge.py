"""
    **Contains the logic for communication with the FPGA.**
"""
from Commacceslib.use_comm import UseBridge
from LINDAaccesslib.hearbeat_thread import KillableThread


class CommBridge:
    """ Main Communication with library class"""

    def __init__(self):
        self.heartbeat = None
        self._bridge = None

    def init_library_connection(self, ip, sync, _async, libpath):
        """
        Init conenction with dll.

        :param ip: Ip address. (str)
        :param sync: Syncorn port. (str)
        :param _async: Asyncorn port. (str)
        :param libpath:  Absolute dll path. (str)
        """
        self._bridge = UseBridge(ip, sync, _async, libpath)
        self.heartbeat = KillableThread(self._bridge.use_update_HB, sleep_interval=2.5)
        self.heartbeat.start()

    def close_connection(self):
        """ Closes the comunication with the library """
        self._bridge.close_communication()

    def kill_hearbeat(self):
        """Kills heart beat thread."""
        self.heartbeat.kill()

    def return_bridge(self):
        """Retruns bridge object."""
        return self._bridge
