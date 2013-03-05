
import contextlib

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
