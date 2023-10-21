# Add new ui designers here. The *.ui files must be placed inside resources/designer_uis
from surfquake.Gui.Utils.pyqt_utils import load_ui_designers

# Add the new UiFrame to the imports at Frames.__init__
UiLoc_Flow = load_ui_designers("loc_flow.ui")
UiEventLocationFrame = load_ui_designers("EventLocationFrame.ui")
UiParametersFrame = load_ui_designers("parameters.ui")
UiAdditionalParameters = load_ui_designers("additionalParameters.ui")
