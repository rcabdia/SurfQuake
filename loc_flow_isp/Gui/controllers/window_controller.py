# Singleton/SingletonDecorator.py
import traceback
from loc_flow_isp.Gui.Frames.loc_flow_frame import LocFlow
from loc_flow_isp.Utils import Singleton
from loc_flow_isp.Gui.Frames.qt_components import MessageDialog


@Singleton
class Controller:
    def __init__(self):
        self.main_frame = None
        self.locflow = LocFlow()

    def open_locflow(self):
        self.locflow.show()

    def exception_parse(self, error_cls, exception, exc_traceback):
        md = MessageDialog(self.main_frame)
        detail_error = "".join(traceback.format_exception(error_cls, exception, exc_traceback))
        md.set_error_message(message="{}:{}".format(error_cls.__name__, exception), detailed_message=detail_error)
        md.show()

