class FAKELOG:
    """Fake logger if you wnat to work with Linux."""
    def mange_doc(self, path):
        pass

    def create_power_shell(self, _from, cmd):
        pass

    def foramt_color(self):
        pass

    def info(self, msg):
        print("LoggerFAke: " + str(msg))

    def error(self, msg):
        print("LoggerFAke: " + str(msg))

    def warning(self, msg):
        print("LoggerFAke: " + str(msg))

    def kill_shell(self):
        pass
