
import inspect
import logging


logger = logging.getLogger(__name__)


def trycatch(func):
    def wrapper(self, *args):
        # filter out excess args as qt signals do
        sig = inspect.signature(func)
        args = args[:(len(sig.parameters)-1)]
        result = None
        try:
            result = func(self, *args)
        except Exception as ex:
            logger.exception(ex)
            self.error.emit(ex)
        return result
    return wrapper


