import faulthandler
import signal

def enable_stack_traces():
    faulthandler.enable()
    # On non-Windows platforms you can dump a stack trace by sending SIGUSR1 to Python.
    # This is useful if you're trying to find slow code or an infinite loop.
    if hasattr(signal, "SIGUSR1"):
        faulthandler.register(signal.SIGUSR1)
