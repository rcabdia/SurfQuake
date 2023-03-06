import sys
from loc_flow_isp.Gui import start_locflow, except_hook

if __name__ == '__main__':
    sys.excepthook = except_hook
    start_locflow()