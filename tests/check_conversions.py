from loc_flow_isp.loc_flow_tools.utils import ConversionUtils
from loc_flow_isp import ROOT_DIR, model_dir, p_dir, station, ttime, nllinput, realout


if __name__ == "__main__":
    ConversionUtils.real2nll(realout, nllinput)