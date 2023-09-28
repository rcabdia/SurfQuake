import logging
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BINARIES = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/binaries")
MACROS_PATH = os.path.join(ROOT_DIR, 'macros')
p_dir = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/data", "picks")
original_p_dir = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/data", "original_picks")
station = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/data", "station", "station.dat")
ttime = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/data", "tt_real", "ttdb.txt")
mseed_dir = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/data", "mseed")
model_dir = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/loc_flow_tools", "models", "190703-214543")
realout = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/loc_flow_tools", "out_data", "phase_sel_total.txt")
nllinput = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/loc_flow_tools", "location_output/obs", "nll_input.txt")
location_output = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/loc_flow_tools", "location_output")
all_locations = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/loc_flow_tools", "location_output", "all_locations")
UIS_PATH = os.path.join(os.path.dirname(ROOT_DIR), 'loc_flow_isp/resources', 'designer_uis')
TT_DB_PATH = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/loc_flow_tools/tt_db", "mymodel.nd")
MOMENT_TENSOR_OUTPUT = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/moment_tensor_output")
magnitudes_config = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/magnitude_tools/MagnitudesConfig"
                                                            "/automag_config")
magnitudes = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/magnitudes_output/magnitudes_output.txt")
green_path = os.path.join(os.path.dirname(ROOT_DIR), "loc_flow_isp/sq_isola_tools/green")
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
