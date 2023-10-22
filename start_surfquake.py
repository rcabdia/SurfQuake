import sys
from surfquake.db import db
import os

if __name__ == '__main__':

    # Initializa DB
    dir_path = os.path.dirname(os.path.abspath(__file__))
    db.set_db_url("sqlite:///{}/surfquake.db".format(dir_path))
    db.start()

    from surfquake.Gui import start_locflow, except_hook

    sys.excepthook = except_hook

    start_locflow()
