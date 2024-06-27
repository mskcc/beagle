class OperatorLogger(object):
    def __init__(self):
        self.message = ""

    def log(self, message):
        self.message += f"{message}\n"
