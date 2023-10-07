class Log():
    INFO, OK, WARNING, ERROR = range(0, 4)

    __write_call = None

    @staticmethod
    def set_call(call):
        Log.__write_call = call

    @staticmethod
    def write(type, name, text):
        if Log.__write_call is not None:
            Log.__write_call(type, name, text)

    @staticmethod
    def info(name, text):
        Log.write(Log.INFO, name, text)

    @staticmethod
    def info_write(text):
        Log.write(Log.INFO, None, text)

    @staticmethod
    def ok(name, text):
        Log.write(Log.OK, name, text)

    @staticmethod
    def ok_write(text):
        Log.write(Log.OK, None, text)

    @staticmethod
    def warning(name, text):
        Log.write(Log.WARNING, name, text)

    @staticmethod
    def warning_write(text):
        Log.write(Log.WARNING, None, text)

    @staticmethod
    def error(name, text):
        Log.write(Log.ERROR, name, text)

    @staticmethod
    def error_write(text):
        Log.write(Log.ERROR, None, text)