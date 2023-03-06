# Add new ui designers here. The *.ui files must be placed inside resources/designer_uis
from loc_flow_isp.Gui.Utils.pyqt_utils import load_ui_designers

# Add the new UiFrame to the imports at Frames.__init__
#UiMainFrame = load_ui_designers("MainFrame.ui")
#UiHelp = load_ui_designers("help.ui")
UiLoc_Flow = load_ui_designers("loc_flow.ui")
