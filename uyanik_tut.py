"""Keep Windows from going back to sleep for N minutes (default 90).

Woken by a scheduled task, Windows sleeps again after ~2 idle minutes. The 23:05 task runs this so
the Claude app has time to run the nightly content job. paylas.py uses keep_awake() itself.
Usage: pythonw uyanik_tut.py [minutes]
"""
import sys
import time


def keep_awake():
    """Hold the system awake until this process exits (no-op off Windows)."""
    if sys.platform == "win32":
        import ctypes
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)


if __name__ == "__main__":
    keep_awake()
    time.sleep(60 * float(sys.argv[1] if len(sys.argv) > 1 else 90))
