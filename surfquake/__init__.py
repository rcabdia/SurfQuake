import logging
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UIS_PATH = os.path.join(os.path.dirname(ROOT_DIR), 'surfquake/resources', 'designer_uis')
MOMENT_TENSOR_OUTPUT = os.path.join(os.path.dirname(ROOT_DIR), "surfquake/moment_tensor_output")
magnitudes_config = os.path.join(os.path.dirname(ROOT_DIR), "surfquake/magnitude_tools/MagnitudesConfig"
                                                            "/automag_config")
source_config = os.path.join(os.path.dirname(ROOT_DIR), "surfquake/source_spec_parse/config/source_spec.conf")
magnitudes = os.path.join(os.path.dirname(ROOT_DIR), "surfquake/magnitudes_output/magnitudes_output.txt")
def create_logger():

    # create logger.
    logger = logging.getLogger('logger')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # create console handler and set level to debug.
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # create file handler.
        file_log = logging.FileHandler(filename="app.log")
        file_log.setLevel(logging.INFO)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to ch
        ch.setFormatter(formatter)
        file_log.setFormatter(formatter)

        # add ch and file_log to logger
        logger.addHandler(ch)
        logger.addHandler(file_log)

    return logger


app_logger = create_logger()
