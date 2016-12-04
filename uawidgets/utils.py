
import inspect
import logging


logger = logging.getLogger(__name__)


def trycatchslot(func):
    """
    wrap a at slot.
    log and call a method called show_error in 
    case of error
    """
    def wrapper(self, *args):
        # filter out excess args as qt signals do
        sig = inspect.signature(func)
        args = args[:(len(sig.parameters)-1)]
        result = None
        try:
            result = func(self, *args)
        except Exception as ex:
            logger.exception(ex)
            if hasattr(self, "show_error"):
                self.show_error(ex)
            elif hasattr(self, "error"):
                self.error.emit(ex)
            else:
                logger.warning("Error class % has no member show_error or error", self)
        return result
    return wrapper


