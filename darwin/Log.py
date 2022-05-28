import datetime


class Log:
    def __init__(self):
        self.file_path = None
        self.file = None

    def __del__(self):
        if self.file:
            self.file.close()

    def initialize(self, file_path):
        self.file_path = file_path
        self.file = open(self.file_path, "a")

    def message(self, message):
        message = datetime.datetime.now().strftime("[%H:%M:%S] ") + message

        print(message)

        if self.file:
            self.file.write(message + "\n")
            self.file.flush()

    def error(self, message):
        self.message('!!! ' + message)


log = Log()
