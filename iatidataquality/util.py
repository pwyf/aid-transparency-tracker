
import contextlib
import os

@contextlib.contextmanager
def report_error(success, failure):
    try:
        yield
        if success is not None:
            print success
    except Exception, e:
        if failure is not None:
            print failure, e
    finally:
        pass

def ensure_download_dir(directory):
    if not os.path.exists(directory):
        with report_error(None, "Couldn't create directory"):
            os.makedirs(directory)
