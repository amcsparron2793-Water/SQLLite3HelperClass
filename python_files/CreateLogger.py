import logging

from datetime import datetime
from os import makedirs
from os.path import isdir, join


def create_logger(project_name=None, log_location="../logs/{}/{}".format(datetime.now().date().isoformat(),
                                                                         ''.join(
                                                                             datetime.now().time().isoformat().split(
                                                                                 '.')[0].split(":")[:-1])),
                  chosen_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    def _GetProjectName():
        """ Either returns the given project name, or if none is given, uses the __file__ name."""
        if project_name:
            return project_name
        else:
            pname = __file__.split('\\')[-1].split(".")[0]
            return pname

    def _CheckMakeLogLocation():
        if isdir(log_location):
            pass
        else:
            makedirs(log_location)

    def _MakeFileHandlers():
        """ Add three filehandlers to the logger then set the log level to debug.
        This way all messages will be sorted into their appropriate spots"""
        for lvl in logger_levels:
            logger.setLevel(lvl)
            if logger.level == 10:
                level_string = "DEBUG"
            elif logger.level == 20:
                level_string = "INFO"
            elif logger.level == 40:
                level_string = "ERROR"
            else:
                print("other logger level detected, defaulting to DEBUG")
                level_string = "DEBUG"
            log_path = join(log_location, '{}-{}-{}.log'.format(level_string, project_name, timestamp))

            # Create a file handler for the logger, and specify the log file location
            file_handler = logging.FileHandler(log_path)
            # Set the logging format for the file handler
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logger.level)
            # Add the file handlers to the loggers
            logger.addHandler(file_handler)

    project_name = _GetProjectName()

    _CheckMakeLogLocation()

    timestamp = datetime.now().isoformat(timespec='minutes').replace(':', '')  # datetime.now().date().isoformat()
    formatter = logging.Formatter(chosen_format)
    logger_levels = ["DEBUG", "INFO", "ERROR"]

    # Create a logger with a specified name and make sure propagate is True
    logger = logging.getLogger('logger')
    logger.propagate = True

    _MakeFileHandlers()

    # set the logger level back to DEBUG, so it handles all messages
    logger.setLevel(10)
    logger.info(f"Starting {project_name} with the following FileHandlers:"
                f"{logger.handlers[0]}"
                f"{logger.handlers[1]}"
                f"{logger.handlers[2]}")

    print("logger initialized")
    return logger


if __name__ == "__main__":
    logger = create_logger(project_name="CreateLogger_test")
